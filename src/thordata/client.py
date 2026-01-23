"""
Synchronous client for the Thordata API.

This module provides the main ThordataClient class for interacting with
Thordata's proxy network, SERP API, Universal Scraping API, and Web Scraper API.
"""

from __future__ import annotations

import base64
import hashlib
import logging
import os
import socket
import ssl
from datetime import date
from typing import Any, Union, cast
from urllib.parse import urlencode, urlparse

import requests
import urllib3
from requests.structures import CaseInsensitiveDict

# Import Legacy/Compat
from ._utils import (
    build_auth_headers,
    build_builder_headers,
    build_public_api_headers,
    decode_base64_image,
    extract_error_message,
    parse_json_response,
)

# Import Core Components
from .core.http_client import ThordataHttpSession
from .core.tunnel import (
    HAS_PYSOCKS,
    UpstreamProxySocketFactory,
    create_tls_in_tls,
    parse_upstream_proxy,
    socks5_handshake,
)
from .enums import Engine
from .exceptions import (
    ThordataConfigError,
    ThordataNetworkError,
    ThordataTimeoutError,
    raise_for_code,
)
from .retry import RetryConfig, with_retry
from .serp_engines import SerpNamespace

# Import Types (Modernized)
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
from .unlimited import UnlimitedNamespace

logger = logging.getLogger(__name__)

# =========================================================================
# Internal Logic for Upstream Proxies
# =========================================================================


def _parse_upstream_proxy() -> dict[str, Any] | None:
    return parse_upstream_proxy()


# =========================================================================
# Main Client Class
# =========================================================================


class ThordataClient:
    """Main client for interacting with Thordata API services."""

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
        self._default_timeout = timeout
        self._api_timeout = api_timeout
        self._retry_config = retry_config or RetryConfig()

        self._auth_mode = auth_mode.lower()
        if self._auth_mode not in ("bearer", "header_token"):
            raise ThordataConfigError(
                f"Invalid auth_mode: {auth_mode}. Must be 'bearer' or 'header_token'."
            )

        # Initialize Core HTTP Client for API calls
        self._http = ThordataHttpSession(
            timeout=api_timeout, retry_config=self._retry_config
        )

        # Legacy logic for Proxy Network connections (requests.Session)
        self._proxy_session = requests.Session()
        self._proxy_session.trust_env = False
        self._proxy_managers: dict[str, urllib3.PoolManager] = {}

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
            "THORDATA_GATEWAY_BASE_URL", "https://api.thordata.com/api/gateway"
        )
        self._child_base_url = os.getenv(
            "THORDATA_CHILD_BASE_URL", "https://api.thordata.com/api/child"
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

        # Determine shared API base from locations URL
        shared_api_base = locations_base.replace("/locations", "")
        self._usage_stats_url = f"{shared_api_base}/account/usage-statistics"
        self._proxy_users_url = f"{shared_api_base}/proxy-users"

        whitelist_base = os.getenv(
            "THORDATA_WHITELIST_BASE_URL", "https://api.thordata.com/api"
        )
        self._whitelist_url = f"{whitelist_base}/whitelisted-ips"

        proxy_api_base = os.getenv(
            "THORDATA_PROXY_API_BASE_URL", "https://openapi.thordata.com/api"
        )
        self._proxy_list_url = f"{proxy_api_base}/proxy/proxy-list"
        self._proxy_expiration_url = f"{proxy_api_base}/proxy/expiration-time"

        # Initialize Namespaces
        self.serp = SerpNamespace(self)
        self.unlimited = UnlimitedNamespace(self)

    # =========================================================================
    # Context Manager
    # =========================================================================

    def close(self) -> None:
        """Close the client and release resources."""
        self._http.close()
        self._proxy_session.close()
        for pm in self._proxy_managers.values():
            pm.clear()
        self._proxy_managers.clear()

    def __enter__(self) -> ThordataClient:
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.close()

    # =========================================================================
    # Internal Helper: API Request Delegation
    # =========================================================================

    def _api_request_with_retry(
        self,
        method: str,
        url: str,
        *,
        data: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
        params: dict[str, Any] | None = None,
    ) -> requests.Response:
        """Delegate to Core HTTP Client."""
        return self._http.request(
            method=method, url=url, data=data, headers=headers, params=params
        )

    def _require_public_credentials(self) -> None:
        if not self.public_token or not self.public_key:
            raise ThordataConfigError(
                "public_token and public_key are required for this operation."
            )

    # =========================================================================
    # Proxy Network Methods
    # =========================================================================

    def get(
        self,
        url: str,
        *,
        proxy_config: ProxyConfig | None = None,
        timeout: int | None = None,
        **kwargs: Any,
    ) -> requests.Response:
        logger.debug(f"Proxy GET request: {url}")
        return self._proxy_verb("GET", url, proxy_config, timeout, **kwargs)

    def post(
        self,
        url: str,
        *,
        proxy_config: ProxyConfig | None = None,
        timeout: int | None = None,
        **kwargs: Any,
    ) -> requests.Response:
        logger.debug(f"Proxy POST request: {url}")
        return self._proxy_verb("POST", url, proxy_config, timeout, **kwargs)

    def build_proxy_url(
        self,
        username: str,
        password: str,
        *,
        country: str | None = None,
        state: str | None = None,
        city: str | None = None,
        session_id: str | None = None,
        session_duration: int | None = None,
        product: ProxyProduct | str = ProxyProduct.RESIDENTIAL,
    ) -> str:
        config = ProxyConfig(
            username=username,
            password=password,
            host=self._proxy_host,
            port=self._proxy_port,
            product=product,
            country=country,
            state=state,
            city=city,
            session_id=session_id,
            session_duration=session_duration,
        )
        return config.build_proxy_url()

    # =========================================================================
    # SERP API Methods
    # =========================================================================

    def serp_search(
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
        return self.serp_search_advanced(request)

    def serp_search_advanced(self, request: SerpRequest) -> dict[str, Any]:
        if not self.scraper_token:
            raise ThordataConfigError("scraper_token is required for SERP API")

        payload = request.to_payload()
        headers = build_auth_headers(self.scraper_token, mode=self._auth_mode)

        logger.info(f"SERP Advanced Search: {request.engine} - {request.query[:50]}")

        response = self._api_request_with_retry(
            "POST",
            self._serp_url,
            data=payload,
            headers=headers,
        )
        response.raise_for_status()

        if request.output_format.lower() == "json":
            data = response.json()
            if isinstance(data, dict):
                code = data.get("code")
                if code is not None and code != 200:
                    msg = extract_error_message(data)
                    raise_for_code(f"SERP Error: {msg}", code=code, payload=data)
            return parse_json_response(data)

        return {"html": response.text}

    # =========================================================================
    # Universal Scraping API (WEB UNLOCKER) Methods
    # =========================================================================

    def universal_scrape(
        self,
        url: str,
        *,
        js_render: bool = False,
        output_format: str = "html",
        country: str | None = None,
        block_resources: str | None = None,
        wait: int | None = None,
        wait_for: str | None = None,
        **kwargs: Any,
    ) -> str | bytes:
        request = UniversalScrapeRequest(
            url=url,
            js_render=js_render,
            output_format=output_format,
            country=country,
            block_resources=block_resources,
            wait=wait,
            wait_for=wait_for,
            extra_params=kwargs,
        )
        return self.universal_scrape_advanced(request)

    def universal_scrape_advanced(self, request: UniversalScrapeRequest) -> str | bytes:
        if not self.scraper_token:
            raise ThordataConfigError("scraper_token required")

        payload = request.to_payload()
        headers = build_auth_headers(self.scraper_token, mode=self._auth_mode)

        response = self._api_request_with_retry(
            "POST", self._universal_url, data=payload, headers=headers
        )
        response.raise_for_status()
        return self._process_universal_response(response, request.output_format)

    # =========================================================================
    # Web Scraper API - Task Management
    # =========================================================================

    def create_scraper_task(
        self,
        file_name: str,
        spider_id: str,
        spider_name: str,
        parameters: dict[str, Any],
        universal_params: dict[str, Any] | None = None,
    ) -> str:
        config = ScraperTaskConfig(
            file_name=file_name,
            spider_id=spider_id,
            spider_name=spider_name,
            parameters=parameters,
            universal_params=universal_params,
        )
        return self.create_scraper_task_advanced(config)

    def run_tool(
        self,
        tool_request: Any,
        file_name: str | None = None,
        universal_params: dict[str, Any] | None = None,
    ) -> str:
        """
        Run a specific pre-defined tool.
        Supports both standard Scrapers and Video downloaders.
        """
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

        # Check if it's a Video Tool (Duck typing check for common_settings)
        if hasattr(tool_request, "common_settings"):
            # It is a Video Task
            config_video = VideoTaskConfig(
                file_name=file_name,
                spider_id=spider_id,
                spider_name=spider_name,
                parameters=params,
                common_settings=tool_request.common_settings,
            )
            return self.create_video_task_advanced(config_video)
        else:
            # It is a Standard Scraper Task
            config = ScraperTaskConfig(
                file_name=file_name,
                spider_id=spider_id,
                spider_name=spider_name,
                parameters=params,
                universal_params=universal_params,
            )
            return self.create_scraper_task_advanced(config)

    def create_scraper_task_advanced(self, config: ScraperTaskConfig) -> str:
        self._require_public_credentials()
        if not self.scraper_token:
            raise ThordataConfigError("scraper_token is required for Task Builder")

        payload = config.to_payload()
        headers = build_builder_headers(
            self.scraper_token, str(self.public_token), str(self.public_key)
        )

        response = self._api_request_with_retry(
            "POST", self._builder_url, data=payload, headers=headers
        )
        response.raise_for_status()
        data = response.json()
        if data.get("code") != 200:
            raise_for_code("Task creation failed", code=data.get("code"), payload=data)
        return data["data"]["task_id"]

    def create_video_task(
        self,
        file_name: str,
        spider_id: str,
        spider_name: str,
        parameters: dict[str, Any],
        common_settings: CommonSettings,
    ) -> str:
        config = VideoTaskConfig(
            file_name=file_name,
            spider_id=spider_id,
            spider_name=spider_name,
            parameters=parameters,
            common_settings=common_settings,
        )
        return self.create_video_task_advanced(config)

    def create_video_task_advanced(self, config: VideoTaskConfig) -> str:
        self._require_public_credentials()
        if not self.scraper_token:
            raise ThordataConfigError(
                "scraper_token is required for Video Task Builder"
            )

        payload = config.to_payload()
        headers = build_builder_headers(
            self.scraper_token, str(self.public_token), str(self.public_key)
        )

        response = self._api_request_with_retry(
            "POST", self._video_builder_url, data=payload, headers=headers
        )
        response.raise_for_status()
        data = response.json()
        if data.get("code") != 200:
            raise_for_code(
                "Video task creation failed", code=data.get("code"), payload=data
            )
        return data["data"]["task_id"]

    def get_task_status(self, task_id: str) -> str:
        self._require_public_credentials()
        headers = build_public_api_headers(str(self.public_token), str(self.public_key))

        response = self._api_request_with_retry(
            "POST",
            self._status_url,
            data={"tasks_ids": task_id},
            headers=headers,
        )
        response.raise_for_status()
        data = response.json()
        if data.get("code") != 200:
            raise_for_code("Task status error", code=data.get("code"), payload=data)

        items = data.get("data") or []
        for item in items:
            if str(item.get("task_id")) == str(task_id):
                return item.get("status", "unknown")
        return "unknown"

    def safe_get_task_status(self, task_id: str) -> str:
        try:
            return self.get_task_status(task_id)
        except Exception:
            return "error"

    def get_task_result(self, task_id: str, file_type: str = "json") -> str:
        self._require_public_credentials()
        headers = build_public_api_headers(str(self.public_token), str(self.public_key))

        response = self._api_request_with_retry(
            "POST",
            self._download_url,
            data={"tasks_id": task_id, "type": file_type},
            headers=headers,
        )
        response.raise_for_status()
        data = response.json()
        if data.get("code") == 200 and data.get("data"):
            return data["data"]["download"]
        raise_for_code("Get result failed", code=data.get("code"), payload=data)
        return ""

    def list_tasks(self, page: int = 1, size: int = 20) -> dict[str, Any]:
        self._require_public_credentials()
        headers = build_public_api_headers(str(self.public_token), str(self.public_key))

        response = self._api_request_with_retry(
            "POST",
            self._list_url,
            data={"page": str(page), "size": str(size)},
            headers=headers,
        )
        response.raise_for_status()
        data = response.json()
        if data.get("code") != 200:
            raise_for_code("List tasks failed", code=data.get("code"), payload=data)
        return data.get("data", {"count": 0, "list": []})

    def wait_for_task(
        self,
        task_id: str,
        *,
        poll_interval: float = 5.0,
        max_wait: float = 600.0,
    ) -> str:
        import time

        start = time.monotonic()
        while (time.monotonic() - start) < max_wait:
            status = self.get_task_status(task_id)
            if status.lower() in {
                "ready",
                "success",
                "finished",
                "failed",
                "error",
                "cancelled",
            }:
                return status
            time.sleep(poll_interval)
        raise TimeoutError(f"Task {task_id} timeout")

    def run_task(
        self,
        file_name: str,
        spider_id: str,
        spider_name: str,
        parameters: dict[str, Any],
        universal_params: dict[str, Any] | None = None,
        *,
        max_wait: float = 600.0,
        initial_poll_interval: float = 2.0,
        max_poll_interval: float = 10.0,
        include_errors: bool = True,
        task_type: str = "web",
        common_settings: CommonSettings | None = None,
    ) -> str:
        import time

        if task_type == "video":
            if common_settings is None:
                raise ValueError("common_settings is required for video tasks")
            config_video = VideoTaskConfig(
                file_name=file_name,
                spider_id=spider_id,
                spider_name=spider_name,
                parameters=parameters,
                common_settings=common_settings,
                include_errors=include_errors,
            )
            task_id = self.create_video_task_advanced(config_video)
        else:
            config = ScraperTaskConfig(
                file_name=file_name,
                spider_id=spider_id,
                spider_name=spider_name,
                parameters=parameters,
                universal_params=universal_params,
                include_errors=include_errors,
            )
            task_id = self.create_scraper_task_advanced(config)

        logger.info(f"Task created: {task_id}. Polling...")

        start_time = time.monotonic()
        current_poll = initial_poll_interval

        while (time.monotonic() - start_time) < max_wait:
            status = self.get_task_status(task_id)
            status_lower = status.lower()

            if status_lower in {"ready", "success", "finished"}:
                return self.get_task_result(task_id)

            if status_lower in {"failed", "error", "cancelled"}:
                raise ThordataNetworkError(
                    f"Task {task_id} failed with status: {status}"
                )

            time.sleep(current_poll)
            current_poll = min(current_poll * 1.5, max_poll_interval)

        raise ThordataTimeoutError(f"Task {task_id} timed out")

    # =========================================================================
    # Account & Usage Methods
    # =========================================================================

    def get_usage_statistics(
        self,
        from_date: str | date,
        to_date: str | date,
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
        response = self._api_request_with_retry(
            "GET", self._usage_stats_url, params=params
        )
        response.raise_for_status()
        data = response.json()
        if data.get("code") != 200:
            raise_for_code("Usage stats error", code=data.get("code"), payload=data)
        return UsageStatistics.from_dict(data.get("data", data))

    def get_traffic_balance(self) -> float:
        self._require_public_credentials()
        params = {"token": self.public_token, "key": self.public_key}
        api_base = self._locations_base_url.replace("/locations", "")
        response = self._api_request_with_retry(
            "GET", f"{api_base}/account/traffic-balance", params=params
        )
        response.raise_for_status()
        data = response.json()
        if data.get("code") != 200:
            raise_for_code(
                "Get traffic balance failed", code=data.get("code"), payload=data
            )
        return float(data.get("data", {}).get("traffic_balance", 0))

    def get_wallet_balance(self) -> float:
        self._require_public_credentials()
        params = {"token": self.public_token, "key": self.public_key}
        api_base = self._locations_base_url.replace("/locations", "")
        response = self._api_request_with_retry(
            "GET", f"{api_base}/account/wallet-balance", params=params
        )
        response.raise_for_status()
        data = response.json()
        if data.get("code") != 200:
            raise_for_code(
                "Get wallet balance failed", code=data.get("code"), payload=data
            )
        return float(data.get("data", {}).get("balance", 0))

    def get_proxy_user_usage(
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
        response = self._api_request_with_retry(
            "GET", f"{self._proxy_users_url}/usage-statistics", params=params
        )
        response.raise_for_status()
        data = response.json()
        if data.get("code") != 200:
            raise_for_code("Get user usage failed", code=data.get("code"), payload=data)
        return data.get("data", [])

    def extract_ip_list(
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

        username = os.getenv("THORDATA_RESIDENTIAL_USERNAME")
        if username:
            params["td-customer"] = username

        response = self._api_request_with_retry(
            "GET", f"{base_url}{endpoint}", params=params
        )
        response.raise_for_status()

        if return_type == "json":
            data = response.json()
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
            text = response.text.strip()
            if text.startswith("{") and "code" in text:
                try:
                    err_data = response.json()
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
    # Proxy Users Management
    # =========================================================================

    def list_proxy_users(
        self, proxy_type: ProxyType | int = ProxyType.RESIDENTIAL
    ) -> ProxyUserList:
        self._require_public_credentials()
        pt = int(proxy_type) if isinstance(proxy_type, ProxyType) else proxy_type
        params = {
            "token": self.public_token,
            "key": self.public_key,
            "proxy_type": str(pt),
        }
        response = self._api_request_with_retry(
            "GET", f"{self._proxy_users_url}/user-list", params=params
        )
        response.raise_for_status()
        data = response.json()
        if data.get("code") != 200:
            raise_for_code("List users error", code=data.get("code"), payload=data)
        return ProxyUserList.from_dict(data.get("data", data))

    def create_proxy_user(
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
        response = self._api_request_with_retry(
            "POST",
            f"{self._proxy_users_url}/create-user",
            data=payload,
            headers=headers,
        )
        response.raise_for_status()
        data = response.json()
        if data.get("code") != 200:
            raise_for_code("Create user failed", code=data.get("code"), payload=data)
        return data.get("data", {})

    def update_proxy_user(
        self,
        username: str,
        password: str,
        traffic_limit: int | None = None,
        status: bool | None = None,
        proxy_type: ProxyType | int = ProxyType.RESIDENTIAL,
        new_username: str | None = None,  # Added optional new_username
    ) -> dict[str, Any]:
        """
        Update a proxy user.
        Note: API requires 'new_' prefixed fields and ALL are required.
        """
        self._require_public_credentials()
        pt = int(proxy_type) if isinstance(proxy_type, ProxyType) else proxy_type
        headers = build_public_api_headers(str(self.public_token), str(self.public_key))

        # Defaults
        limit_val = str(traffic_limit) if traffic_limit is not None else "0"
        status_val = "true" if (status is None or status) else "false"

        # If new_username is not provided, keep the old one (API requires new_username field)
        target_username = new_username or username

        # Mapping to API specific field names (new_...)
        payload = {
            "proxy_type": str(pt),
            "username": username,  # Who to update
            "new_username": target_username,  # Required field
            "new_password": password,  # Required field
            "new_traffic_limit": limit_val,  # Required field
            "new_status": status_val,  # Required field
        }

        response = self._api_request_with_retry(
            "POST",
            f"{self._proxy_users_url}/update-user",
            data=payload,
            headers=headers,
        )
        data = response.json()
        if data.get("code") != 200:
            raise_for_code("Update user failed", code=data.get("code"), payload=data)
        return data.get("data", {})

    def delete_proxy_user(
        self,
        username: str,
        proxy_type: ProxyType | int = ProxyType.RESIDENTIAL,
    ) -> dict[str, Any]:
        self._require_public_credentials()
        pt = int(proxy_type) if isinstance(proxy_type, ProxyType) else proxy_type
        headers = build_public_api_headers(str(self.public_token), str(self.public_key))
        payload = {"proxy_type": str(pt), "username": username}
        response = self._api_request_with_retry(
            "POST",
            f"{self._proxy_users_url}/delete-user",
            data=payload,
            headers=headers,
        )
        response.raise_for_status()
        data = response.json()
        if data.get("code") != 200:
            raise_for_code("Delete user failed", code=data.get("code"), payload=data)
        return data.get("data", {})

    # =========================================================================
    # Whitelist IP Management
    # =========================================================================

    def add_whitelist_ip(
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
        response = self._api_request_with_retry(
            "POST", f"{self._whitelist_url}/add-ip", data=payload, headers=headers
        )
        response.raise_for_status()
        data = response.json()
        if data.get("code") != 200:
            raise_for_code(
                "Add whitelist IP failed", code=data.get("code"), payload=data
            )
        return data.get("data", {})

    def delete_whitelist_ip(
        self,
        ip: str,
        proxy_type: ProxyType | int = ProxyType.RESIDENTIAL,
    ) -> dict[str, Any]:
        self._require_public_credentials()
        pt = int(proxy_type) if isinstance(proxy_type, ProxyType) else proxy_type
        headers = build_public_api_headers(str(self.public_token), str(self.public_key))
        payload = {"proxy_type": str(pt), "ip": ip}
        response = self._api_request_with_retry(
            "POST", f"{self._whitelist_url}/delete-ip", data=payload, headers=headers
        )
        response.raise_for_status()
        data = response.json()
        if data.get("code") != 200:
            raise_for_code(
                "Delete whitelist IP failed", code=data.get("code"), payload=data
            )
        return data.get("data", {})

    def list_whitelist_ips(
        self,
        proxy_type: ProxyType | int = ProxyType.RESIDENTIAL,
    ) -> list[str]:
        self._require_public_credentials()
        pt = int(proxy_type) if isinstance(proxy_type, ProxyType) else proxy_type
        params = {
            "token": self.public_token,
            "key": self.public_key,
            "proxy_type": str(pt),
        }
        response = self._api_request_with_retry(
            "GET", f"{self._whitelist_url}/ip-list", params=params
        )
        response.raise_for_status()
        data = response.json()
        if data.get("code") != 200:
            raise_for_code(
                "List whitelist IPs failed", code=data.get("code"), payload=data
            )

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

    def _get_locations(self, endpoint: str, **kwargs: Any) -> list[dict[str, Any]]:
        self._require_public_credentials()
        params = {"token": self.public_token, "key": self.public_key}
        for k, v in kwargs.items():
            params[k] = str(v)

        response = self._api_request_with_retry(
            "GET", f"{self._locations_base_url}/{endpoint}", params=params
        )
        response.raise_for_status()
        data = response.json()

        if isinstance(data, dict):
            if data.get("code") != 200:
                raise RuntimeError(f"Locations error: {data.get('msg')}")
            return data.get("data") or []
        return data if isinstance(data, list) else []

    def list_countries(
        self, proxy_type: ProxyType | int = ProxyType.RESIDENTIAL
    ) -> list[dict[str, Any]]:
        pt = int(proxy_type) if isinstance(proxy_type, ProxyType) else proxy_type
        return self._get_locations("countries", proxy_type=pt)

    def list_states(
        self,
        country_code: str,
        proxy_type: ProxyType | int = ProxyType.RESIDENTIAL,
    ) -> list[dict[str, Any]]:
        pt = int(proxy_type) if isinstance(proxy_type, ProxyType) else proxy_type
        return self._get_locations("states", proxy_type=pt, country_code=country_code)

    def list_cities(
        self,
        country_code: str,
        state_code: str | None = None,
        proxy_type: ProxyType | int = ProxyType.RESIDENTIAL,
    ) -> list[dict[str, Any]]:
        pt = int(proxy_type) if isinstance(proxy_type, ProxyType) else proxy_type
        kwargs = {"proxy_type": pt, "country_code": country_code}
        if state_code:
            kwargs["state_code"] = state_code
        return self._get_locations("cities", **kwargs)

    def list_asn(
        self,
        country_code: str,
        proxy_type: ProxyType | int = ProxyType.RESIDENTIAL,
    ) -> list[dict[str, Any]]:
        pt = int(proxy_type) if isinstance(proxy_type, ProxyType) else proxy_type
        return self._get_locations("asn", proxy_type=pt, country_code=country_code)

    # =========================================================================
    # ISP & Datacenter Proxy Management
    # =========================================================================

    def list_proxy_servers(self, proxy_type: int) -> list[ProxyServer]:
        self._require_public_credentials()
        params = {
            "token": self.public_token,
            "key": self.public_key,
            "proxy_type": str(proxy_type),
        }
        response = self._api_request_with_retry(
            "GET", self._proxy_list_url, params=params
        )
        response.raise_for_status()
        data = response.json()
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

    def get_proxy_expiration(
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
        response = self._api_request_with_retry(
            "GET", self._proxy_expiration_url, params=params
        )
        response.raise_for_status()
        data = response.json()
        if data.get("code") != 200:
            raise_for_code("Get expiration error", code=data.get("code"), payload=data)
        return data.get("data", data)

    # =========================================================================
    # Helpers needed for compatibility
    # =========================================================================

    def _process_universal_response(
        self, response: requests.Response, output_format: str
    ) -> str | bytes:
        try:
            resp_json = response.json()
        except ValueError:
            return response.content if output_format.lower() == "png" else response.text

        if isinstance(resp_json, dict):
            code = resp_json.get("code")
            if code is not None and code != 200:
                msg = extract_error_message(resp_json)
                raise_for_code(f"Universal Error: {msg}", code=code, payload=resp_json)

        if "html" in resp_json:
            return resp_json["html"]
        if "png" in resp_json:
            return decode_base64_image(resp_json["png"])
        return str(resp_json)

    def get_browser_connection_url(
        self, username: str | None = None, password: str | None = None
    ) -> str:
        # User requested modification: ONLY use browser credentials, do not fall back to residential.
        user = username or os.getenv("THORDATA_BROWSER_USERNAME")
        pwd = password or os.getenv("THORDATA_BROWSER_PASSWORD")

        if not user or not pwd:
            raise ThordataConfigError(
                "Browser credentials missing. Set THORDATA_BROWSER_USERNAME/PASSWORD or pass arguments."
            )
        prefix = "td-customer-"
        final_user = f"{prefix}{user}" if not user.startswith(prefix) else user

        from urllib.parse import quote

        safe_user = quote(final_user, safe="")
        safe_pass = quote(pwd, safe="")

        return f"wss://{safe_user}:{safe_pass}@ws-browser.thordata.com"

    # =========================================================================
    # Proxy Internal Logic
    # =========================================================================

    def _proxy_verb(
        self,
        method: str,
        url: str,
        proxy_config: ProxyConfig | None,
        timeout: int | None,
        **kwargs: Any,
    ) -> requests.Response:
        timeout = timeout or self._default_timeout
        if proxy_config is None:
            proxy_config = self._get_default_proxy_config_from_env()
        if proxy_config is None:
            raise ThordataConfigError("Proxy credentials are missing.")

        kwargs.pop("proxies", None)

        @with_retry(self._retry_config)
        def _do() -> requests.Response:
            return self._proxy_request_with_proxy_manager(
                method,
                url,
                proxy_config=cast(ProxyConfig, proxy_config),
                timeout=cast(int, timeout),
                headers=kwargs.pop("headers", None),
                params=kwargs.pop("params", None),
                data=kwargs.pop("data", None),
            )

        try:
            return _do()
        except Exception as e:
            raise ThordataNetworkError(f"Request failed: {e}", original_error=e) from e

    def _proxy_manager_key(self, proxy_endpoint: str, userpass: str | None) -> str:
        if not userpass:
            return proxy_endpoint
        h = hashlib.sha256(userpass.encode("utf-8")).hexdigest()[:12]
        return f"{proxy_endpoint}|auth={h}"

    def _get_proxy_manager(
        self,
        proxy_url: str,
        *,
        cache_key: str,
        proxy_headers: dict[str, str] | None = None,
    ) -> urllib3.PoolManager:
        cached = self._proxy_managers.get(cache_key)
        if cached is not None:
            return cached

        if proxy_url.startswith(("socks5://", "socks5h://", "socks4://", "socks4a://")):
            if not HAS_PYSOCKS:
                raise ThordataConfigError(
                    "SOCKS support requires PySocks/urllib3[socks]"
                )
            from urllib3.contrib.socks import SOCKSProxyManager

            pm = SOCKSProxyManager(proxy_url, num_pools=10, maxsize=10)  # type: ignore
            self._proxy_managers[cache_key] = pm
            return pm

        proxy_ssl_context = (
            ssl.create_default_context() if proxy_url.startswith("https://") else None
        )
        pm = urllib3.ProxyManager(
            proxy_url,
            proxy_headers=proxy_headers,
            proxy_ssl_context=proxy_ssl_context,
            num_pools=10,
            maxsize=10,
        )
        self._proxy_managers[cache_key] = pm
        return pm

    def _proxy_request_with_proxy_manager(
        self,
        method: str,
        url: str,
        *,
        proxy_config: ProxyConfig,
        timeout: int,
        headers: dict[str, str] | None = None,
        params: dict[str, Any] | None = None,
        data: Any = None,
    ) -> requests.Response:
        upstream = _parse_upstream_proxy()
        if upstream:
            return self._proxy_request_with_upstream(
                method,
                url,
                proxy_config=proxy_config,
                timeout=timeout,
                headers=headers,
                params=params,
                data=data,
                upstream_config=upstream,
            )

        req = requests.Request(method=method.upper(), url=url, params=params)
        prepped = self._proxy_session.prepare_request(req)
        final_url = prepped.url or url

        proxy_endpoint = proxy_config.build_proxy_endpoint()
        is_socks = proxy_endpoint.startswith(("socks",))

        if is_socks:
            proxy_url_for_manager = proxy_config.build_proxy_url()
            cache_key = proxy_url_for_manager
            pm = self._get_proxy_manager(proxy_url_for_manager, cache_key=cache_key)
            req_headers = dict(headers or {})
        else:
            userpass = proxy_config.build_proxy_basic_auth()
            proxy_headers = urllib3.make_headers(proxy_basic_auth=userpass)
            cache_key = self._proxy_manager_key(proxy_endpoint, userpass)
            pm = self._get_proxy_manager(
                proxy_endpoint, cache_key=cache_key, proxy_headers=dict(proxy_headers)
            )
            req_headers = dict(headers or {})

        body = None
        if data is not None:
            if isinstance(data, dict):
                body = urlencode({k: str(v) for k, v in data.items()})
                req_headers.setdefault(
                    "Content-Type", "application/x-www-form-urlencoded"
                )
            else:
                body = data

        http_resp = pm.request(
            method.upper(),
            final_url,
            body=body,
            headers=req_headers or None,
            timeout=urllib3.Timeout(connect=timeout, read=timeout),
            retries=False,
            preload_content=True,
        )

        r = requests.Response()
        r.status_code = int(getattr(http_resp, "status", 0))
        r._content = http_resp.data or b""
        r.url = final_url
        r.headers = CaseInsensitiveDict(dict(http_resp.headers or {}))
        return r

    def _proxy_request_with_upstream(
        self,
        method: str,
        url: str,
        *,
        proxy_config: ProxyConfig,
        timeout: int,
        headers: dict[str, str] | None = None,
        params: dict[str, Any] | None = None,
        data: Any = None,
        upstream_config: dict[str, Any],
    ) -> requests.Response:
        if not HAS_PYSOCKS:
            raise ThordataConfigError("PySocks required for upstream proxy support.")

        req = requests.Request(method=method.upper(), url=url, params=params)
        prepped = self._proxy_session.prepare_request(req)
        final_url = prepped.url or url

        parsed_target = urlparse(final_url)
        target_host = parsed_target.hostname or ""
        target_port = parsed_target.port or (
            443 if parsed_target.scheme == "https" else 80
        )

        thordata_host = proxy_config.host or "pr.thordata.net"
        thordata_port = proxy_config.port or 9999
        thordata_user = proxy_config.build_username()
        thordata_pass = proxy_config.password

        # 1. Connect to Upstream -> Thordata Node
        factory = UpstreamProxySocketFactory(upstream_config)
        raw_sock = factory.create_connection(
            (thordata_host, thordata_port),
            timeout=float(timeout),
        )

        try:
            protocol = proxy_config.protocol.lower().replace("socks5", "socks5h")

            # 2. Handshake with Thordata
            if protocol.startswith("socks"):
                sock = socks5_handshake(
                    raw_sock, target_host, target_port, thordata_user, thordata_pass
                )
                if parsed_target.scheme == "https":
                    ctx = ssl.create_default_context()
                    sock = ctx.wrap_socket(sock, server_hostname=target_host)
            else:
                # HTTP/HTTPS Tunnel
                if protocol == "https":
                    ctx = ssl.create_default_context()
                    sock = ctx.wrap_socket(raw_sock, server_hostname=thordata_host)
                else:
                    sock = raw_sock

                # CONNECT to Thordata
                connect_req = f"CONNECT {target_host}:{target_port} HTTP/1.1\r\n"
                connect_req += f"Host: {target_host}:{target_port}\r\n"
                auth = base64.b64encode(
                    f"{thordata_user}:{thordata_pass}".encode()
                ).decode()
                connect_req += f"Proxy-Authorization: Basic {auth}\r\n\r\n"
                sock.sendall(connect_req.encode())

                resp = b""
                while b"\r\n\r\n" not in resp:
                    resp += sock.recv(1024)
                if b"200" not in resp.split(b"\r\n")[0]:
                    raise ConnectionError("Thordata CONNECT failed")

                # 3. If Target is HTTPS, wrap TLS inside the tunnel
                if parsed_target.scheme == "https":
                    if isinstance(sock, ssl.SSLSocket):
                        sock = create_tls_in_tls(sock, target_host, float(timeout))
                    else:
                        ctx = ssl.create_default_context()
                        sock = ctx.wrap_socket(sock, server_hostname=target_host)

            # 4. Send actual Request
            return self._send_http_via_socket(
                sock, method, parsed_target, headers, data, final_url, timeout
            )

        except Exception:
            raw_sock.close()
            raise

    def _send_http_via_socket(
        self,
        sock: Union[socket.socket, Any],  # Fix for TLSInTLSSocket typing issue
        method: str,
        parsed: Any,
        headers: Any,
        data: Any,
        final_url: str,
        timeout: int,
    ) -> requests.Response:
        req_headers = dict(headers or {})
        req_headers.setdefault("Host", parsed.hostname)
        req_headers.setdefault("User-Agent", "python-thordata-sdk")
        req_headers.setdefault("Connection", "close")

        path = parsed.path or "/"
        if parsed.query:
            path += f"?{parsed.query}"

        msg = f"{method} {path} HTTP/1.1\r\n"
        for k, v in req_headers.items():
            msg += f"{k}: {v}\r\n"

        body = b""
        if data:
            if isinstance(data, dict):
                body = urlencode(data).encode()
                msg += "Content-Type: application/x-www-form-urlencoded\r\n"
            elif isinstance(data, bytes):
                body = data
            else:
                body = str(data).encode()
            msg += f"Content-Length: {len(body)}\r\n"

        msg += "\r\n"
        sock.sendall(msg.encode())
        if body:
            sock.sendall(body)

        # Read Response
        resp_data = b""
        while True:
            try:
                chunk = sock.recv(4096)
                if not chunk:
                    break
                resp_data += chunk
            except socket.timeout:
                break

        if b"\r\n\r\n" in resp_data:
            head, content = resp_data.split(b"\r\n\r\n", 1)
            status_line = head.split(b"\r\n")[0].decode()
            try:
                status_code = int(status_line.split(" ")[1])
            except (ValueError, IndexError):
                status_code = 0

            r = requests.Response()
            r.status_code = status_code
            r._content = content
            r.url = final_url
            return r
        raise ConnectionError("Empty response from socket")

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
