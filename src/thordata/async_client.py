"""
Asynchronous client for the Thordata API.

This module provides the AsyncThordataClient for high-concurrency workloads,
built on aiohttp.
"""

from __future__ import annotations

import asyncio
import logging
import os
from datetime import date
from typing import Any
from urllib.parse import quote

import aiohttp

# Import Legacy/Compat
from ._utils import (
    build_auth_headers,
    build_builder_headers,
    build_public_api_headers,
    decode_base64_image,
    extract_error_message,
    parse_json_response,
)
from .async_unlimited import AsyncUnlimitedNamespace

# Import Core
from .core.async_http_client import AsyncThordataHttpSession
from .enums import Engine
from .exceptions import (
    ThordataConfigError,
    ThordataNetworkError,
    ThordataTimeoutError,
    raise_for_code,
)
from .retry import RetryConfig
from .serp_engines import AsyncSerpNamespace

# Import Types
from .types import (
    CommonSettings,
    ProxyConfig,
    ProxyProduct,
    ProxyServer,
    ProxyType,
    ProxyUserList,
    ScraperTaskConfig,
    SerpRequest,
    UniversalScrapeRequest,
    UsageStatistics,
    VideoTaskConfig,
)

logger = logging.getLogger(__name__)


class AsyncThordataClient:
    """The official asynchronous Python client for Thordata."""

    # API Endpoints
    BASE_URL = "https://scraperapi.thordata.com"
    UNIVERSAL_URL = "https://universalapi.thordata.com"
    API_URL = "https://openapi.thordata.com/api/web-scraper-api"
    LOCATIONS_URL = "https://openapi.thordata.com/api/locations"

    def __init__(
        self,
        scraper_token: str | None = None,
        public_token: str | None = None,
        public_key: str | None = None,
        proxy_host: str = "pr.thordata.net",
        proxy_port: int = 9999,
        timeout: int = 30,
        api_timeout: int = 60,
        retry_config: RetryConfig | None = None,
        auth_mode: str = "bearer",
        scraperapi_base_url: str | None = None,
        universalapi_base_url: str | None = None,
        web_scraper_api_base_url: str | None = None,
        locations_base_url: str | None = None,
    ) -> None:
        self.scraper_token = scraper_token
        self.public_token = public_token
        self.public_key = public_key

        self._proxy_host = proxy_host
        self._proxy_port = proxy_port
        self._retry_config = retry_config or RetryConfig()

        self._api_timeout = api_timeout

        self._auth_mode = auth_mode.lower()
        if self._auth_mode not in ("bearer", "header_token"):
            raise ThordataConfigError(f"Invalid auth_mode: {auth_mode}")

        # Core Async HTTP Client
        self._http = AsyncThordataHttpSession(
            timeout=api_timeout, retry_config=self._retry_config
        )

        # Base URLs Configuration
        scraperapi_base = (
            scraperapi_base_url
            or os.getenv("THORDATA_SCRAPERAPI_BASE_URL")
            or self.BASE_URL
        ).rstrip("/")
        universalapi_base = (
            universalapi_base_url
            or os.getenv("THORDATA_UNIVERSALAPI_BASE_URL")
            or self.UNIVERSAL_URL
        ).rstrip("/")
        web_scraper_api_base = (
            web_scraper_api_base_url
            or os.getenv("THORDATA_WEB_SCRAPER_API_BASE_URL")
            or self.API_URL
        ).rstrip("/")
        locations_base = (
            locations_base_url
            or os.getenv("THORDATA_LOCATIONS_BASE_URL")
            or self.LOCATIONS_URL
        ).rstrip("/")

        self._gateway_base_url = os.getenv(
            "THORDATA_GATEWAY_BASE_URL", "https://openapi.thordata.com/api/gateway"
        )
        self._child_base_url = os.getenv(
            "THORDATA_CHILD_BASE_URL", "https://openapi.thordata.com/api/child"
        )

        # URL Construction
        self._serp_url = f"{scraperapi_base}/request"
        self._builder_url = f"{scraperapi_base}/builder"
        self._video_builder_url = f"{scraperapi_base}/video_builder"
        self._universal_url = f"{universalapi_base}/request"
        self._status_url = f"{web_scraper_api_base}/tasks-status"
        self._download_url = f"{web_scraper_api_base}/tasks-download"
        self._list_url = f"{web_scraper_api_base}/tasks-list"
        self._locations_base_url = locations_base

        shared_api_base = locations_base.replace("/locations", "")
        self._usage_stats_url = f"{shared_api_base}/account/usage-statistics"
        self._proxy_users_url = f"{shared_api_base}/proxy-users"

        whitelist_base = os.getenv(
            "THORDATA_WHITELIST_BASE_URL", "https://openapi.thordata.com/api"
        )
        self._whitelist_url = f"{whitelist_base}/whitelisted-ips"

        proxy_api_base = os.getenv(
            "THORDATA_PROXY_API_BASE_URL", "https://openapi.thordata.com/api"
        )
        self._proxy_list_url = f"{proxy_api_base}/proxy/proxy-list"
        self._proxy_expiration_url = f"{proxy_api_base}/proxy/expiration-time"

        # Namespaces
        self.serp = AsyncSerpNamespace(self)
        self.unlimited = AsyncUnlimitedNamespace(self)

    async def __aenter__(self) -> AsyncThordataClient:
        await self._http._ensure_session()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        await self.close()

    async def close(self) -> None:
        await self._http.close()

    def _get_session(self) -> aiohttp.ClientSession:
        """Internal helper for namespaces that expect direct session access (legacy compat)."""
        if not self._http._session:
            raise RuntimeError("Session not initialized. Use 'async with client'.")
        return self._http._session

    def _require_public_credentials(self) -> None:
        if not self.public_token or not self.public_key:
            raise ThordataConfigError("public_token and public_key are required.")

    # =========================================================================
    # Proxy Network Methods
    # =========================================================================

    async def get(
        self,
        url: str,
        *,
        proxy_config: ProxyConfig | None = None,
        **kwargs: Any,
    ) -> aiohttp.ClientResponse:
        return await self._proxy_request("GET", url, proxy_config, **kwargs)

    async def post(
        self,
        url: str,
        *,
        proxy_config: ProxyConfig | None = None,
        **kwargs: Any,
    ) -> aiohttp.ClientResponse:
        return await self._proxy_request("POST", url, proxy_config, **kwargs)

    async def _proxy_request(
        self, method: str, url: str, proxy_config: ProxyConfig | None, **kwargs: Any
    ) -> aiohttp.ClientResponse:
        logger.debug(f"Async Proxy {method}: {url}")

        if proxy_config is None:
            proxy_config = self._get_default_proxy_config_from_env()

        if proxy_config is None:
            raise ThordataConfigError("Proxy credentials are missing.")

        # Restore strict check for aiohttp HTTPS proxy limitation
        if getattr(proxy_config, "protocol", "http").lower() == "https":
            raise ThordataConfigError(
                "Proxy Network requires an HTTPS proxy endpoint. "
                "aiohttp support for 'https://' proxies is limited. "
                "Please use ThordataClient.get/post (sync client) for Proxy Network requests."
            )

        proxy_url, proxy_auth = proxy_config.to_aiohttp_config()

        # Use the core HTTP client to execute, leveraging retry logic
        return await self._http.request(
            method=method, url=url, proxy=proxy_url, proxy_auth=proxy_auth, **kwargs
        )

    # =========================================================================
    # API Methods (SERP, Universal)
    # =========================================================================

    async def serp_search(
        self,
        query: str,
        *,
        engine: Engine | str = Engine.GOOGLE,
        num: int = 10,
        country: str | None = None,
        language: str | None = None,
        search_type: str | None = None,
        device: str | None = None,
        render_js: bool | None = None,
        no_cache: bool | None = None,
        output_format: str = "json",
        **kwargs: Any,
    ) -> dict[str, Any]:
        engine_str = engine.value if isinstance(engine, Engine) else engine.lower()
        request = SerpRequest(
            query=query,
            engine=engine_str,
            num=num,
            country=country,
            language=language,
            search_type=search_type,
            device=device,
            render_js=render_js,
            no_cache=no_cache,
            output_format=output_format,
            extra_params=kwargs,
        )
        return await self.serp_search_advanced(request)

    async def serp_search_advanced(self, request: SerpRequest) -> dict[str, Any]:
        if not self.scraper_token:
            raise ThordataConfigError("scraper_token required")
        payload = request.to_payload()
        headers = build_auth_headers(self.scraper_token, mode=self._auth_mode)
        logger.info(f"Async SERP: {request.engine} - {request.query}")

        response = await self._http.request(
            "POST", self._serp_url, data=payload, headers=headers
        )

        if request.output_format.lower() == "json":
            data = await response.json()
            if isinstance(data, dict):
                code = data.get("code")
                if code is not None and code != 200:
                    raise_for_code(
                        f"SERP Error: {extract_error_message(data)}",
                        code=code,
                        payload=data,
                    )
            return parse_json_response(data)

        text = await response.text()
        return {"html": text}

    async def universal_scrape(
        self,
        url: str,
        *,
        js_render: bool = False,
        output_format: str | list[str] = "html",
        country: str | None = None,
        block_resources: str | None = None,
        clean_content: str | None = None,
        wait: int | None = None,
        wait_for: str | None = None,
        follow_redirect: bool | None = None,
        headers: list[dict[str, str]] | None = None,
        cookies: list[dict[str, str]] | None = None,
        **kwargs: Any,
    ) -> str | bytes | dict[str, str | bytes]:
        request = UniversalScrapeRequest(
            url=url,
            js_render=js_render,
            output_format=output_format,
            country=country,
            block_resources=block_resources,
            clean_content=clean_content,
            wait=wait,
            wait_for=wait_for,
            follow_redirect=follow_redirect,
            headers=headers,
            cookies=cookies,
            extra_params=kwargs,
        )
        return await self.universal_scrape_advanced(request)

    async def universal_scrape_advanced(
        self, request: UniversalScrapeRequest
    ) -> str | bytes | dict[str, str | bytes]:
        if not self.scraper_token:
            raise ThordataConfigError("scraper_token required")
        payload = request.to_payload()
        headers = build_auth_headers(self.scraper_token, mode=self._auth_mode)

        response = await self._http.request(
            "POST", self._universal_url, data=payload, headers=headers
        )

        try:
            resp_json = await response.json()
        except ValueError:
            # If not JSON, return raw content based on format
            if isinstance(request.output_format, list) or (
                isinstance(request.output_format, str) and "," in request.output_format
            ):
                return {"raw": await response.read()}
            fmt = (
                request.output_format.lower()
                if isinstance(request.output_format, str)
                else str(request.output_format).lower()
            )
            return await response.read() if fmt == "png" else await response.text()

        if isinstance(resp_json, dict):
            code = resp_json.get("code")
            if code is not None and code != 200:
                msg = extract_error_message(resp_json)
                raise_for_code(f"Universal Error: {msg}", code=code, payload=resp_json)

        # Handle multiple output formats
        if isinstance(request.output_format, list) or (
            isinstance(request.output_format, str) and "," in request.output_format
        ):
            result: dict[str, str | bytes] = {}
            formats = (
                request.output_format
                if isinstance(request.output_format, list)
                else [f.strip() for f in request.output_format.split(",")]
            )

            for fmt in formats:
                fmt_lower = fmt.lower()
                if fmt_lower == "html" and "html" in resp_json:
                    result["html"] = resp_json["html"]
                elif fmt_lower == "png" and "png" in resp_json:
                    result["png"] = decode_base64_image(resp_json["png"])

            if result:
                return result

        if "html" in resp_json:
            return resp_json["html"]
        if "png" in resp_json:
            return decode_base64_image(resp_json["png"])
        return str(resp_json)

    # =========================================================================
    # Task Management
    # =========================================================================

    async def create_scraper_task(
        self,
        file_name: str,
        spider_id: str,
        spider_name: str,
        parameters: dict[str, Any] | list[dict[str, Any]],
        universal_params: dict[str, Any] | None = None,
    ) -> str:
        config = ScraperTaskConfig(
            file_name=file_name,
            spider_id=spider_id,
            spider_name=spider_name,
            parameters=parameters,
            universal_params=universal_params,
        )
        return await self.create_scraper_task_advanced(config)

    async def run_tool(
        self,
        tool_request: Any,
        file_name: str | None = None,
        universal_params: dict[str, Any] | None = None,
    ) -> str:
        """Run a specific pre-defined tool (Async)."""
        if not hasattr(tool_request, "to_task_parameters") or not hasattr(
            tool_request, "get_spider_id"
        ):
            raise ValueError(
                "tool_request must be an instance of a thordata.tools class"
            )

        spider_id = tool_request.get_spider_id()
        spider_name = tool_request.get_spider_name()
        params = tool_request.to_task_parameters()

        if not file_name:
            import uuid

            short_id = uuid.uuid4().hex[:8]
            file_name = f"{spider_id}_{short_id}"

        # Check if it's a Video Tool
        if hasattr(tool_request, "common_settings"):
            config_video = VideoTaskConfig(
                file_name=file_name,
                spider_id=spider_id,
                spider_name=spider_name,
                parameters=params,
                common_settings=tool_request.common_settings,
            )
            return await self.create_video_task_advanced(config_video)
        else:
            config = ScraperTaskConfig(
                file_name=file_name,
                spider_id=spider_id,
                spider_name=spider_name,
                parameters=params,
                universal_params=universal_params,
            )
            return await self.create_scraper_task_advanced(config)

    async def create_scraper_task_advanced(self, config: ScraperTaskConfig) -> str:
        self._require_public_credentials()
        if not self.scraper_token:
            raise ThordataConfigError("scraper_token required")
        payload = config.to_payload()
        headers = build_builder_headers(
            self.scraper_token, str(self.public_token), str(self.public_key)
        )

        response = await self._http.request(
            "POST", self._builder_url, data=payload, headers=headers
        )
        data = await response.json(content_type=None)
        if data.get("code") != 200:
            raise_for_code(
                f"Task creation failed: {extract_error_message(data)}",
                code=data.get("code"),
                payload=data,
            )
        return data["data"]["task_id"]

    async def create_video_task(
        self,
        file_name: str,
        spider_id: str,
        spider_name: str,
        parameters: dict[str, Any] | list[dict[str, Any]],
        common_settings: CommonSettings,
    ) -> str:
        config = VideoTaskConfig(
            file_name=file_name,
            spider_id=spider_id,
            spider_name=spider_name,
            parameters=parameters,
            common_settings=common_settings,
        )
        return await self.create_video_task_advanced(config)

    async def create_video_task_advanced(self, config: VideoTaskConfig) -> str:
        self._require_public_credentials()
        if not self.scraper_token:
            raise ThordataConfigError("scraper_token required")
        payload = config.to_payload()
        headers = build_builder_headers(
            self.scraper_token, str(self.public_token), str(self.public_key)
        )

        response = await self._http.request(
            "POST", self._video_builder_url, data=payload, headers=headers
        )
        data = await response.json()
        if data.get("code") != 200:
            raise_for_code(
                f"Video task failed: {extract_error_message(data)}",
                code=data.get("code"),
                payload=data,
            )
        return data["data"]["task_id"]

    async def get_task_status(self, task_id: str) -> str:
        self._require_public_credentials()
        headers = build_public_api_headers(str(self.public_token), str(self.public_key))
        response = await self._http.request(
            "POST", self._status_url, data={"tasks_ids": task_id}, headers=headers
        )
        data = await response.json(content_type=None)

        if isinstance(data, dict):
            code = data.get("code")
            if code is not None and code != 200:
                raise_for_code(
                    f"Status error: {extract_error_message(data)}",
                    code=code,
                    payload=data,
                )
            items = data.get("data") or []
            for item in items:
                if str(item.get("task_id")) == str(task_id):
                    return item.get("status", "unknown")
            return "unknown"
        raise ThordataNetworkError(f"Unexpected response type: {type(data)}")

    async def safe_get_task_status(self, task_id: str) -> str:
        try:
            return await self.get_task_status(task_id)
        except Exception:
            return "error"

    async def get_task_result(self, task_id: str, file_type: str = "json") -> str:
        self._require_public_credentials()
        headers = build_public_api_headers(str(self.public_token), str(self.public_key))
        response = await self._http.request(
            "POST",
            self._download_url,
            data={"tasks_id": task_id, "type": file_type},
            headers=headers,
        )
        data = await response.json(content_type=None)
        if data.get("code") == 200 and data.get("data"):
            return data["data"]["download"]
        raise_for_code("Get result failed", code=data.get("code"), payload=data)
        return ""

    async def list_tasks(self, page: int = 1, size: int = 20) -> dict[str, Any]:
        self._require_public_credentials()
        headers = build_public_api_headers(str(self.public_token), str(self.public_key))
        response = await self._http.request(
            "POST",
            self._list_url,
            data={"page": str(page), "size": str(size)},
            headers=headers,
        )
        data = await response.json(content_type=None)
        if data.get("code") != 200:
            raise_for_code("List tasks failed", code=data.get("code"), payload=data)
        return data.get("data", {"count": 0, "list": []})

    async def wait_for_task(
        self, task_id: str, *, poll_interval: float = 5.0, max_wait: float = 600.0
    ) -> str:
        import time

        start = time.monotonic()
        while (time.monotonic() - start) < max_wait:
            status = await self.get_task_status(task_id)
            if status.lower() in {
                "ready",
                "success",
                "finished",
                "failed",
                "error",
                "cancelled",
            }:
                return status
            await asyncio.sleep(poll_interval)
        raise TimeoutError(f"Task {task_id} timeout")

    async def run_task(
        self,
        file_name: str,
        spider_id: str,
        spider_name: str,
        parameters: dict[str, Any] | list[dict[str, Any]],
        universal_params: dict[str, Any] | None = None,
        *,
        max_wait: float = 600.0,
        initial_poll_interval: float = 2.0,
        max_poll_interval: float = 10.0,
        include_errors: bool = True,
        task_type: str = "web",
        common_settings: CommonSettings | None = None,
    ) -> str:
        if task_type == "video":
            if common_settings is None:
                raise ValueError("common_settings required for video")
            task_id = await self.create_video_task(
                file_name, spider_id, spider_name, parameters, common_settings
            )
        else:
            task_id = await self.create_scraper_task(
                file_name, spider_id, spider_name, parameters, universal_params
            )

        import time

        start_time = time.monotonic()
        current_poll = initial_poll_interval

        while (time.monotonic() - start_time) < max_wait:
            status = await self.get_task_status(task_id)
            if status.lower() in {"ready", "success", "finished"}:
                return await self.get_task_result(task_id)
            if status.lower() in {"failed", "error", "cancelled"}:
                raise ThordataNetworkError(f"Task {task_id} failed: {status}")
            await asyncio.sleep(current_poll)
            current_poll = min(current_poll * 1.5, max_poll_interval)
        raise ThordataTimeoutError(f"Task {task_id} timed out")

    # =========================================================================
    # Account, Usage, Proxy Management (Delegated to HTTP)
    # =========================================================================

    async def get_usage_statistics(
        self, from_date: str | date, to_date: str | date
    ) -> UsageStatistics:
        self._require_public_credentials()
        if isinstance(from_date, date):
            from_date = from_date.strftime("%Y-%m-%d")
        if isinstance(to_date, date):
            to_date = to_date.strftime("%Y-%m-%d")
        params = {
            "token": self.public_token,
            "key": self.public_key,
            "from_date": from_date,
            "to_date": to_date,
        }
        response = await self._http.request("GET", self._usage_stats_url, params=params)
        data = await response.json()
        if data.get("code") != 200:
            raise_for_code("Usage error", code=data.get("code"), payload=data)
        return UsageStatistics.from_dict(data.get("data", data))

    async def get_traffic_balance(self) -> float:
        self._require_public_credentials()
        api_base = self._locations_base_url.replace("/locations", "")
        params = {"token": str(self.public_token), "key": str(self.public_key)}
        response = await self._http.request(
            "GET", f"{api_base}/account/traffic-balance", params=params
        )
        data = await response.json()
        if data.get("code") != 200:
            raise_for_code("Balance error", code=data.get("code"), payload=data)
        return float(data.get("data", {}).get("traffic_balance", 0))

    async def get_wallet_balance(self) -> float:
        self._require_public_credentials()
        api_base = self._locations_base_url.replace("/locations", "")
        params = {"token": str(self.public_token), "key": str(self.public_key)}
        response = await self._http.request(
            "GET", f"{api_base}/account/wallet-balance", params=params
        )
        data = await response.json()
        if data.get("code") != 200:
            raise_for_code("Balance error", code=data.get("code"), payload=data)
        return float(data.get("data", {}).get("balance", 0))

    async def get_proxy_user_usage(
        self,
        username: str,
        start_date: str | date,
        end_date: str | date,
        proxy_type: ProxyType | int = ProxyType.RESIDENTIAL,
    ) -> list[dict[str, Any]]:
        self._require_public_credentials()
        pt = int(proxy_type) if isinstance(proxy_type, ProxyType) else proxy_type
        if isinstance(start_date, date):
            start_date = start_date.strftime("%Y-%m-%d")
        if isinstance(end_date, date):
            end_date = end_date.strftime("%Y-%m-%d")

        params = {
            "token": self.public_token,
            "key": self.public_key,
            "proxy_type": str(pt),
            "username": username,
            "from_date": start_date,
            "to_date": end_date,
        }
        response = await self._http.request(
            "GET", f"{self._proxy_users_url}/usage-statistics", params=params
        )
        data = await response.json()
        if data.get("code") != 200:
            raise_for_code("Get usage failed", code=data.get("code"), payload=data)
        return data.get("data", [])

    async def list_proxy_users(
        self, proxy_type: ProxyType | int = ProxyType.RESIDENTIAL
    ) -> ProxyUserList:
        self._require_public_credentials()
        pt = int(proxy_type) if isinstance(proxy_type, ProxyType) else proxy_type
        params = {
            "token": self.public_token,
            "key": self.public_key,
            "proxy_type": str(pt),
        }
        response = await self._http.request(
            "GET", f"{self._proxy_users_url}/user-list", params=params
        )
        data = await response.json()
        if data.get("code") != 200:
            raise_for_code("List users error", code=data.get("code"), payload=data)
        return ProxyUserList.from_dict(data.get("data", data))

    async def create_proxy_user(
        self,
        username: str,
        password: str,
        proxy_type: ProxyType | int = ProxyType.RESIDENTIAL,
        traffic_limit: int = 0,
        status: bool = True,
    ) -> dict[str, Any]:
        self._require_public_credentials()
        pt = int(proxy_type) if isinstance(proxy_type, ProxyType) else proxy_type
        headers = build_public_api_headers(str(self.public_token), str(self.public_key))
        payload = {
            "proxy_type": str(pt),
            "username": username,
            "password": password,
            "traffic_limit": str(traffic_limit),
            "status": "true" if status else "false",
        }
        response = await self._http.request(
            "POST",
            f"{self._proxy_users_url}/create-user",
            data=payload,
            headers=headers,
        )
        data = await response.json()
        if data.get("code") != 200:
            raise_for_code("Create user failed", code=data.get("code"), payload=data)
        return data.get("data", {})

    async def update_proxy_user(
        self,
        username: str,
        password: str,
        traffic_limit: int | None = None,
        status: bool | None = None,
        proxy_type: ProxyType | int = ProxyType.RESIDENTIAL,
        new_username: str | None = None,
    ) -> dict[str, Any]:
        """
        Update a proxy user.
        Note: API requires 'new_' prefixed fields and ALL are required.
        """
        self._require_public_credentials()
        pt = int(proxy_type) if isinstance(proxy_type, ProxyType) else proxy_type
        headers = build_public_api_headers(str(self.public_token), str(self.public_key))

        limit_val = str(traffic_limit) if traffic_limit is not None else "0"
        status_val = "true" if (status is None or status) else "false"
        target_username = new_username or username

        payload = {
            "proxy_type": str(pt),
            "username": username,
            "new_username": target_username,
            "new_password": password,
            "new_traffic_limit": limit_val,
            "new_status": status_val,
        }

        response = await self._http.request(
            "POST",
            f"{self._proxy_users_url}/update-user",
            data=payload,
            headers=headers,
        )
        data = await response.json()
        if data.get("code") != 200:
            raise_for_code("Update user failed", code=data.get("code"), payload=data)
        return data.get("data", {})

    async def delete_proxy_user(
        self, username: str, proxy_type: ProxyType | int = ProxyType.RESIDENTIAL
    ) -> dict[str, Any]:
        self._require_public_credentials()
        pt = int(proxy_type) if isinstance(proxy_type, ProxyType) else proxy_type
        headers = build_public_api_headers(str(self.public_token), str(self.public_key))
        payload = {"proxy_type": str(pt), "username": username}
        response = await self._http.request(
            "POST",
            f"{self._proxy_users_url}/delete-user",
            data=payload,
            headers=headers,
        )
        data = await response.json()
        if data.get("code") != 200:
            raise_for_code("Delete user failed", code=data.get("code"), payload=data)
        return data.get("data", {})

    async def add_whitelist_ip(
        self,
        ip: str,
        proxy_type: ProxyType | int = ProxyType.RESIDENTIAL,
        status: bool = True,
    ) -> dict[str, Any]:
        self._require_public_credentials()
        pt = int(proxy_type) if isinstance(proxy_type, ProxyType) else proxy_type
        headers = build_public_api_headers(str(self.public_token), str(self.public_key))
        payload = {
            "proxy_type": str(pt),
            "ip": ip,
            "status": "true" if status else "false",
        }
        response = await self._http.request(
            "POST", f"{self._whitelist_url}/add-ip", data=payload, headers=headers
        )
        data = await response.json()
        if data.get("code") != 200:
            raise_for_code("Add whitelist failed", code=data.get("code"), payload=data)
        return data.get("data", {})

    async def delete_whitelist_ip(
        self, ip: str, proxy_type: ProxyType | int = ProxyType.RESIDENTIAL
    ) -> dict[str, Any]:
        self._require_public_credentials()
        pt = int(proxy_type) if isinstance(proxy_type, ProxyType) else proxy_type
        headers = build_public_api_headers(str(self.public_token), str(self.public_key))
        payload = {"proxy_type": str(pt), "ip": ip}
        response = await self._http.request(
            "POST", f"{self._whitelist_url}/delete-ip", data=payload, headers=headers
        )
        data = await response.json()
        if data.get("code") != 200:
            raise_for_code(
                "Delete whitelist failed", code=data.get("code"), payload=data
            )
        return data.get("data", {})

    async def list_whitelist_ips(
        self, proxy_type: ProxyType | int = ProxyType.RESIDENTIAL
    ) -> list[str]:
        self._require_public_credentials()
        pt = int(proxy_type) if isinstance(proxy_type, ProxyType) else proxy_type
        params = {
            "token": self.public_token,
            "key": self.public_key,
            "proxy_type": str(pt),
        }
        response = await self._http.request(
            "GET", f"{self._whitelist_url}/ip-list", params=params
        )
        data = await response.json()
        if data.get("code") != 200:
            raise_for_code("List whitelist failed", code=data.get("code"), payload=data)

        items = data.get("data", []) or []
        result = []
        for item in items:
            if isinstance(item, str):
                result.append(item)
            elif isinstance(item, dict) and "ip" in item:
                result.append(str(item["ip"]))
            else:
                result.append(str(item))
        return result

    # =========================================================================
    # Locations & ASN Methods
    # =========================================================================

    async def _get_locations(
        self, endpoint: str, **kwargs: Any
    ) -> list[dict[str, Any]]:
        self._require_public_credentials()
        params = {"token": self.public_token, "key": self.public_key}
        for k, v in kwargs.items():
            params[k] = str(v)

        response = await self._http.request(
            "GET", f"{self._locations_base_url}/{endpoint}", params=params
        )
        data = await response.json()

        if isinstance(data, dict):
            if data.get("code") != 200:
                raise RuntimeError(f"Locations error: {data.get('msg')}")
            return data.get("data") or []
        return data if isinstance(data, list) else []

    async def list_countries(
        self, proxy_type: ProxyType | int = ProxyType.RESIDENTIAL
    ) -> list[dict[str, Any]]:
        pt = int(proxy_type) if isinstance(proxy_type, ProxyType) else proxy_type
        return await self._get_locations("countries", proxy_type=pt)

    async def list_states(
        self, country_code: str, proxy_type: ProxyType | int = ProxyType.RESIDENTIAL
    ) -> list[dict[str, Any]]:
        pt = int(proxy_type) if isinstance(proxy_type, ProxyType) else proxy_type
        return await self._get_locations(
            "states", proxy_type=pt, country_code=country_code
        )

    async def list_cities(
        self,
        country_code: str,
        state_code: str | None = None,
        proxy_type: ProxyType | int = ProxyType.RESIDENTIAL,
    ) -> list[dict[str, Any]]:
        pt = int(proxy_type) if isinstance(proxy_type, ProxyType) else proxy_type
        kwargs = {"proxy_type": pt, "country_code": country_code}
        if state_code:
            kwargs["state_code"] = state_code
        return await self._get_locations("cities", **kwargs)

    async def list_asn(
        self, country_code: str, proxy_type: ProxyType | int = ProxyType.RESIDENTIAL
    ) -> list[dict[str, Any]]:
        pt = int(proxy_type) if isinstance(proxy_type, ProxyType) else proxy_type
        return await self._get_locations(
            "asn", proxy_type=pt, country_code=country_code
        )

    # =========================================================================
    # ISP & Datacenter Proxy Management
    # =========================================================================

    async def list_proxy_servers(self, proxy_type: int) -> list[ProxyServer]:
        self._require_public_credentials()
        params = {
            "token": self.public_token,
            "key": self.public_key,
            "proxy_type": str(proxy_type),
        }
        response = await self._http.request("GET", self._proxy_list_url, params=params)
        data = await response.json()
        if data.get("code") != 200:
            raise_for_code(
                "List proxy servers error", code=data.get("code"), payload=data
            )

        server_list = []
        if isinstance(data, dict):
            server_list = data.get("data", data.get("list", []))
        elif isinstance(data, list):
            server_list = data
        return [ProxyServer.from_dict(s) for s in server_list]

    async def get_proxy_expiration(
        self, ips: str | list[str], proxy_type: int
    ) -> dict[str, Any]:
        self._require_public_credentials()
        if isinstance(ips, list):
            ips = ",".join(ips)
        params = {
            "token": self.public_token,
            "key": self.public_key,
            "proxy_type": str(proxy_type),
            "ips": ips,
        }
        response = await self._http.request(
            "GET", self._proxy_expiration_url, params=params
        )
        data = await response.json()
        if data.get("code") != 200:
            raise_for_code("Get expiration error", code=data.get("code"), payload=data)
        return data.get("data", data)

    async def extract_ip_list(
        self,
        num: int = 1,
        country: str | None = None,
        state: str | None = None,
        city: str | None = None,
        time_limit: int | None = None,
        port: int | None = None,
        return_type: str = "txt",
        protocol: str = "http",
        sep: str = "\r\n",
        product: str = "residential",
    ) -> list[str]:
        base_url = "https://get-ip.thordata.net"
        endpoint = "/unlimited_api" if product == "unlimited" else "/api"
        params: dict[str, Any] = {
            "num": str(num),
            "return_type": return_type,
            "protocol": protocol,
            "sep": sep,
        }
        if country:
            params["country"] = country
        if state:
            params["state"] = state
        if city:
            params["city"] = city
        if time_limit:
            params["time"] = str(time_limit)
        if port:
            params["port"] = str(port)

        if product == "unlimited":
            username = os.getenv("THORDATA_UNLIMITED_USERNAME") or os.getenv(
                "THORDATA_RESIDENTIAL_USERNAME"
            )
        else:
            username = os.getenv("THORDATA_RESIDENTIAL_USERNAME")
        if username:
            params["td-customer"] = username

        response = await self._http.request(
            "GET", f"{base_url}{endpoint}", params=params
        )

        if return_type == "json":
            data = await response.json()
            if isinstance(data, dict):
                if data.get("code") in (0, 200):
                    raw_list = data.get("data") or []
                    return [f"{item['ip']}:{item['port']}" for item in raw_list]
                else:
                    raise_for_code(
                        "Extract IPs failed", code=data.get("code"), payload=data
                    )
            return []
        else:
            text = await response.text()
            text = text.strip()
            if text.startswith("{") and "code" in text:
                try:
                    err_data = await response.json()
                    raise_for_code(
                        "Extract IPs failed",
                        code=err_data.get("code"),
                        payload=err_data,
                    )
                except ValueError:
                    pass
            actual_sep = sep.replace("\\r", "\r").replace("\\n", "\n")
            return [line.strip() for line in text.split(actual_sep) if line.strip()]

    # =========================================================================
    # Helpers
    # =========================================================================

    def _get_proxy_endpoint_overrides(
        self, product: ProxyProduct
    ) -> tuple[str | None, int | None, str]:
        prefix = product.value.upper()
        host = os.getenv(f"THORDATA_{prefix}_PROXY_HOST") or os.getenv(
            "THORDATA_PROXY_HOST"
        )
        port_raw = os.getenv(f"THORDATA_{prefix}_PROXY_PORT") or os.getenv(
            "THORDATA_PROXY_PORT"
        )
        protocol = (
            os.getenv(f"THORDATA_{prefix}_PROXY_PROTOCOL")
            or os.getenv("THORDATA_PROXY_PROTOCOL")
            or "http"
        )
        port = int(port_raw) if port_raw and port_raw.isdigit() else None
        return host or None, port, protocol

    def _get_default_proxy_config_from_env(self) -> ProxyConfig | None:
        for prod in [
            ProxyProduct.RESIDENTIAL,
            ProxyProduct.DATACENTER,
            ProxyProduct.MOBILE,
        ]:
            prefix = prod.value.upper()
            u = os.getenv(f"THORDATA_{prefix}_USERNAME")
            p = os.getenv(f"THORDATA_{prefix}_PASSWORD")
            if u and p:
                h, port, proto = self._get_proxy_endpoint_overrides(prod)
                return ProxyConfig(
                    username=u,
                    password=p,
                    product=prod,
                    host=h,
                    port=port,
                    protocol=proto,
                )
        return None

    def get_browser_connection_url(
        self, username: str | None = None, password: str | None = None
    ) -> str:
        user = username or os.getenv("THORDATA_BROWSER_USERNAME")
        pwd = password or os.getenv("THORDATA_BROWSER_PASSWORD")
        if not user or not pwd:
            raise ThordataConfigError("Browser credentials missing.")
        prefix = "td-customer-"
        final_user = f"{prefix}{user}" if not user.startswith(prefix) else user

        safe_user = quote(final_user, safe="")
        safe_pass = quote(pwd, safe="")
        return f"wss://{safe_user}:{safe_pass}@ws-browser.thordata.com"
