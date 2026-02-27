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

from ._tools_registry import (
    get_tool_class_by_key as _get_tool_class_by_key,
)
from ._tools_registry import (
    get_tool_info as _get_tool_info,
)
from ._tools_registry import (
    list_tools_metadata as _list_tools_metadata,
)
from ._tools_registry import (
    resolve_tool_key as _resolve_tool_key,
)

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
from .constants import (
    APIBaseURL,
    ErrorMessage,
)
from .constants import (
    AuthMode as AuthModeConstant,
)

# Import Core
from .core.async_http_client import AsyncThordataHttpSession
from .enums import Engine
from .exceptions import (
    ThordataConfigError,
    ThordataNetworkError,
    ThordataTimeoutError,
    raise_for_code,
)
from .namespaces import (
    AccountNamespace,
    ProxyNamespace,
    UniversalNamespace,
    WebScraperNamespace,
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
    SerpTypedRequest,
    UniversalScrapeRequest,
    UsageStatistics,
    VideoTaskConfig,
)

logger = logging.getLogger(__name__)


class AsyncThordataClient:
    """The official asynchronous Python client for Thordata."""

    # API Endpoints (using constants for better maintainability)
    BASE_URL = APIBaseURL.SCRAPER_API
    UNIVERSAL_URL = APIBaseURL.UNIVERSAL_API
    API_URL = APIBaseURL.WEB_SCRAPER_API
    LOCATIONS_URL = APIBaseURL.LOCATIONS_API

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
        if self._auth_mode not in (
            AuthModeConstant.BEARER,
            AuthModeConstant.HEADER_TOKEN,
        ):
            raise ThordataConfigError(
                ErrorMessage.INVALID_AUTH_MODE.format(mode=auth_mode)
            )

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
        # New unified namespaces
        self.universal = UniversalNamespace(self)
        self.scraper = WebScraperNamespace(self)
        self.account = AccountNamespace(self)
        self.proxy = ProxyNamespace(self)

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
            raise ThordataConfigError(ErrorMessage.MISSING_PUBLIC_CREDENTIALS)

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

        # aiohttp has limited support for 'https://' style upstream proxies.
        # For such cases, the sync ThordataClient (requests-based) is recommended.
        if getattr(proxy_config, "protocol", "http").lower() == "https":
            raise ThordataConfigError(
                "aiohttp support for 'https://' proxies is limited. "
                "AsyncThordataClient currently does not support 'https://' upstream proxies. "
                "Please either use an 'http://' proxy endpoint, or switch to "
                "ThordataClient.get/post (sync client) for Proxy Network requests."
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
        start: int = 0,
        country: str | None = None,
        language: str | None = None,
        google_domain: str | None = None,
        countries_filter: str | None = None,
        languages_filter: str | None = None,
        location: str | None = None,
        uule: str | None = None,
        search_type: str | None = None,
        safe_search: bool | None = None,
        time_filter: str | None = None,
        no_autocorrect: bool = False,
        filter_duplicates: bool | None = None,
        device: str | None = None,
        render_js: bool | None = None,
        no_cache: bool | None = None,
        output_format: str = "json",
        ai_overview: bool = False,
        ludocid: str | None = None,
        kgmid: str | None = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        engine_str = engine.value if isinstance(engine, Engine) else engine.lower()
        request = SerpRequest(
            query=query,
            engine=engine_str,
            num=num,
            start=start,
            country=country,
            language=language,
            google_domain=google_domain,
            countries_filter=countries_filter,
            languages_filter=languages_filter,
            location=location,
            uule=uule,
            search_type=search_type,
            safe_search=safe_search,
            time_filter=time_filter,
            no_autocorrect=no_autocorrect,
            filter_duplicates=filter_duplicates,
            device=device,
            render_js=render_js,
            no_cache=no_cache,
            output_format=output_format,
            ai_overview=ai_overview,
            ludocid=ludocid,
            kgmid=kgmid,
            extra_params=kwargs,
        )
        return await self.serp_search_advanced(request)

    async def serp_search_advanced(self, request: SerpRequest) -> dict[str, Any]:
        if not self.scraper_token:
            raise ThordataConfigError("scraper_token is required for SERP API")
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

    async def serp_search_typed(self, request: SerpTypedRequest) -> dict[str, Any]:
        """
        Execute a strongly-typed SERP request (async).
        """
        return await self.serp_search_advanced(request.to_serp_request())

    async def serp_batch_search(
        self,
        requests: list[SerpRequest | dict[str, Any]],
        *,
        concurrency: int = 5,
    ) -> list[dict[str, Any]]:
        """Run multiple SERP queries concurrently (async).

        Args:
            requests: List of SerpRequest objects or dicts with query parameters
            concurrency: Maximum number of concurrent requests (1-20)

        Returns:
            List of results, each containing 'index', 'ok', 'query', and 'output' or 'error'
        """
        import asyncio

        if concurrency < 1:
            concurrency = 1
        if concurrency > 20:
            concurrency = 20

        sem = asyncio.Semaphore(concurrency)

        async def _one(i: int, req: SerpRequest | dict[str, Any]) -> dict[str, Any]:
            try:
                if isinstance(req, dict):
                    # Convert dict to SerpRequest
                    query = str(req.get("query", ""))
                    if not query:
                        return {
                            "index": i,
                            "ok": False,
                            "error": {
                                "type": "validation_error",
                                "message": "Missing query",
                            },
                        }
                    serp_req = SerpRequest(
                        query=query,
                        engine=req.get("engine", "google"),
                        num=req.get("num", 10),
                        country=req.get("country"),
                        language=req.get("language"),
                        search_type=req.get("search_type"),
                        device=req.get("device"),
                        render_js=req.get("render_js"),
                        no_cache=req.get("no_cache"),
                        output_format=req.get("output_format", "json"),
                        ai_overview=req.get("ai_overview", False),
                        extra_params=req.get("extra_params", {}),
                    )
                else:
                    serp_req = req

                async with sem:
                    data = await self.serp_search_advanced(serp_req)
                return {"index": i, "ok": True, "query": serp_req.query, "output": data}
            except Exception as e:
                return {
                    "index": i,
                    "ok": False,
                    "error": {"type": type(e).__name__, "message": str(e)},
                }

        results = await asyncio.gather(
            *[_one(i, req) for i, req in enumerate(requests)]
        )
        # Sort by index to maintain order
        results.sort(key=lambda x: x["index"])
        return results

    async def universal_scrape(
        self,
        url: str,
        *,
        js_render: bool = False,
        output_format: str | list[str] = "html",
        country: str | None = None,
        block_resources: str | None = None,
        clean_content: str | None = None,
        wait: int | None = None,  # Wait time in milliseconds (ms). Maximum: 100000 ms
        wait_for: str | None = None,  # CSS selector to wait for
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

    async def universal_scrape_markdown(
        self,
        url: str,
        *,
        js_render: bool = True,
        wait: int | None = None,  # Wait time in milliseconds (ms)
        max_chars: int = 20000,
        country: str | None = None,
        block_resources: str | None = None,
        wait_for: str | None = None,
        **kwargs: Any,
    ) -> str:
        """Fetch a URL via Universal Scrape and return cleaned Markdown text (async).

        Args:
            url: Target URL to scrape
            js_render: Whether to enable JavaScript rendering (default: True)
            wait: Wait time in milliseconds before capture
            max_chars: Maximum characters in returned Markdown (default: 20000)
            country: Country code for geolocation
            block_resources: Comma-separated resource types to block
            wait_for: CSS selector to wait for
            **kwargs: Additional parameters passed to universal_scrape

        Returns:
            Cleaned Markdown text
        """
        from ._utils import html_to_markdown

        html = await self.universal_scrape(
            url=url,
            js_render=js_render,
            output_format="html",
            country=country,
            block_resources=block_resources,
            wait=wait,
            wait_for=wait_for,
            **kwargs,
        )
        html_str = str(html) if not isinstance(html, str) else html
        return html_to_markdown(html_str, max_length=max_chars)

    async def universal_scrape_advanced(
        self, request: UniversalScrapeRequest
    ) -> str | bytes | dict[str, str | bytes]:
        if not self.scraper_token:
            raise ThordataConfigError("scraper_token is required for Universal API")
        payload = request.to_payload()
        headers = build_auth_headers(self.scraper_token, mode=self._auth_mode)

        response = await self._http.request(
            "POST", self._universal_url, data=payload, headers=headers
        )

        # Check HTTP status code before processing response
        if response.status != 200:
            # Try to get error message from response
            try:
                resp_json = await response.json()
                if isinstance(resp_json, dict):
                    code = resp_json.get("code")
                    msg = extract_error_message(resp_json)
                    raise_for_code(
                        f"Universal Error: {msg}",
                        status_code=response.status,
                        code=code if code is not None else response.status,
                        payload=resp_json,
                    )
            except ValueError:
                # If response is not JSON, raise with status code
                text = await response.text()
                raise_for_code(
                    f"Universal Error: HTTP {response.status}",
                    status_code=response.status,
                    payload={"raw": text[:500]},
                )

        # Process response with improved error handling
        try:
            resp_json = await response.json()
        except ValueError:
            # If not JSON, check if it's a valid HTML/text response
            # This can happen when js_render=False and API returns raw HTML
            content_type = response.headers.get("Content-Type", "").lower()
            if "text/html" in content_type or "text/plain" in content_type:
                # Return raw text content for non-JS rendering
                text = await response.text()
                if isinstance(request.output_format, list) or (
                    isinstance(request.output_format, str)
                    and "," in request.output_format
                ):
                    return {"html": text}
                fmt = (
                    request.output_format.lower()
                    if isinstance(request.output_format, str)
                    else str(request.output_format).lower()
                )
                return text if fmt == "html" else await response.read()
            # For other non-JSON responses, return raw content
            content = await response.read()
            if isinstance(request.output_format, list) or (
                isinstance(request.output_format, str) and "," in request.output_format
            ):
                return {"raw": content}
            fmt = (
                request.output_format.lower()
                if isinstance(request.output_format, str)
                else str(request.output_format).lower()
            )
            return content if fmt == "png" else await response.text()

        # Handle JSON response with improved error checking
        if isinstance(resp_json, dict):
            # Check for error codes even if HTTP status is 200
            code = resp_json.get("code")
            if code is not None and code != 200:
                msg = extract_error_message(resp_json)
                raise_for_code(
                    f"Universal Error: {msg}",
                    status_code=response.status,
                    code=code,
                    payload=resp_json,
                )

            # Check for error messages in response
            if "error" in resp_json or "message" in resp_json:
                error_msg = resp_json.get("error") or resp_json.get("message")
                # Only raise if it's actually an error (not a success message)
                if (
                    error_msg
                    and "success" not in str(error_msg).lower()
                    and (code is None or code != 200)
                ):
                    raise_for_code(
                        f"Universal Error: {error_msg}",
                        status_code=response.status,
                        code=code,
                        payload=resp_json,
                    )

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

        # Single format (backward compatibility)
        if "html" in resp_json:
            return resp_json["html"]
        if "png" in resp_json:
            return decode_base64_image(resp_json["png"])

        # If response is a string (unexpected but possible), return it
        if isinstance(resp_json, str):
            return resp_json

        # Last resort: return string representation
        return str(resp_json)

    async def universal_scrape_batch(
        self,
        requests: list[UniversalScrapeRequest | dict[str, Any]],
        *,
        concurrency: int = 5,
    ) -> list[dict[str, Any]]:
        """
        Batch Universal Scrape requests with simple concurrency control (async).

        Each request item can be either:
            - UniversalScrapeRequest instance, or
            - dict with the same keys as universal_scrape().
        """
        import asyncio

        if concurrency < 1:
            concurrency = 1
        if concurrency > 20:
            concurrency = 20

        sem = asyncio.Semaphore(concurrency)

        def _from_dict(i: int, cfg: dict[str, Any]) -> UniversalScrapeRequest:
            url = str(cfg.get("url", ""))
            if not url:
                raise ValueError(f"Request {i}: missing url")
            return UniversalScrapeRequest(
                url=url,
                js_render=bool(cfg.get("js_render", False)),
                output_format=cfg.get("output_format", "html"),
                country=cfg.get("country"),
                block_resources=cfg.get("block_resources"),
                clean_content=cfg.get("clean_content"),
                wait=cfg.get("wait"),
                wait_for=cfg.get("wait_for"),
                follow_redirect=cfg.get("follow_redirect"),
                headers=cfg.get("headers"),
                cookies=cfg.get("cookies"),
                extra_params=cfg.get("extra_params", {}),
            )

        async def _one(
            i: int, cfg: UniversalScrapeRequest | dict[str, Any]
        ) -> dict[str, Any]:
            try:
                req = _from_dict(i, cfg) if isinstance(cfg, dict) else cfg
                async with sem:
                    out = await self.universal_scrape_advanced(req)
                return {"index": i, "ok": True, "url": req.url, "output": out}
            except Exception as e:
                return {
                    "index": i,
                    "ok": False,
                    "url": (
                        cfg.get("url")
                        if isinstance(cfg, dict)
                        else getattr(cfg, "url", None)
                    ),
                    "error": {"type": type(e).__name__, "message": str(e)},
                }

        results = await asyncio.gather(
            *[_one(i, cfg) for i, cfg in enumerate(requests)]
        )
        results.sort(key=lambda x: x["index"])
        return results

    # =========================================================================
    # Task Management
    # =========================================================================

    # -------------------------------------------------------------------------
    # Tool discovery helpers
    # -------------------------------------------------------------------------

    async def list_tools(
        self,
        *,
        group: str | None = None,
        keyword: str | None = None,
    ) -> dict[str, Any]:
        """
        List available Web Scraper tools (metadata only).

        This mirrors the sync client's list_tools but is async for API symmetry.
        """
        tools, group_counts = _list_tools_metadata(group=group, keyword=keyword)
        return {
            "tools": tools,
            "meta": {"total": len(tools), "groups": group_counts},
        }

    async def get_tool_groups(self) -> dict[str, Any]:
        """
        Return discovered tool groups and counts (async variant).
        """
        tools, group_counts = _list_tools_metadata()
        return {
            "groups": [{"id": k, "count": v} for k, v in sorted(group_counts.items())],
            "total": len(tools),
        }

    async def search_tools(self, keyword: str) -> dict[str, Any]:
        """
        Search tools by keyword in key / spider_id / spider_name (async variant).
        """
        return await self.list_tools(keyword=keyword)

    async def resolve_tool_key(self, tool: str) -> str:
        """Resolve a tool key or raw spider_id to canonical '<group>.<spider_id>' (async symmetry)."""
        return _resolve_tool_key(tool)

    async def get_tool_info(self, tool: str) -> dict[str, Any]:
        """Get tool metadata (schema) by canonical key or raw spider_id (async symmetry)."""
        return _get_tool_info(tool)

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

    # -------------------------------------------------------------------------
    # Tool execution helpers
    # -------------------------------------------------------------------------

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

    async def run_tool_by_key(
        self,
        tool: str,
        params: dict[str, Any],
        *,
        file_name: str | None = None,
        universal_params: dict[str, Any] | None = None,
    ) -> str:
        """
        Run a Web Scraper tool by its key string instead of class instance (async).
        """
        cls = _get_tool_class_by_key(tool)
        tool_request = cls(**params)  # type: ignore[call-arg]
        return await self.run_tool(
            tool_request,
            file_name=file_name,
            universal_params=universal_params,
        )

    async def run_tools_batch(
        self,
        requests: list[dict[str, Any]],
        *,
        concurrency: int = 5,
    ) -> list[dict[str, Any]]:
        """
        Run multiple Web Scraper tools concurrently (async).

        Each request item should have:
            - "tool": tool key string
            - "params": dict of parameters
            - optional "file_name": custom file name
            - optional "universal_params": dict passed to universal params
        """
        import asyncio

        if concurrency < 1:
            concurrency = 1
        if concurrency > 20:
            concurrency = 20

        sem = asyncio.Semaphore(concurrency)

        async def _one(i: int, req: dict[str, Any]) -> dict[str, Any]:
            tool_key = str(req.get("tool", "")).strip()
            params = req.get("params") or {}
            file_name = req.get("file_name")
            universal_params = req.get("universal_params")

            if not tool_key:
                return {
                    "index": i,
                    "ok": False,
                    "task_id": None,
                    "error": {
                        "type": "validation_error",
                        "message": "Missing tool key",
                    },
                }
            if not isinstance(params, dict):
                return {
                    "index": i,
                    "ok": False,
                    "task_id": None,
                    "error": {
                        "type": "validation_error",
                        "message": "params must be a dict",
                    },
                }

            try:
                async with sem:
                    task_id = await self.run_tool_by_key(
                        tool_key,
                        params,
                        file_name=file_name,
                        universal_params=universal_params,
                    )
                return {
                    "index": i,
                    "ok": True,
                    "task_id": task_id,
                    "error": None,
                }
            except Exception as e:
                return {
                    "index": i,
                    "ok": False,
                    "task_id": None,
                    "error": {
                        "type": type(e).__name__,
                        "message": str(e),
                    },
                }

        results = await asyncio.gather(*[_one(i, r) for i, r in enumerate(requests)])
        results.sort(key=lambda x: x["index"])
        return results

    async def create_scraper_task_advanced(self, config: ScraperTaskConfig) -> str:
        self._require_public_credentials()
        if not self.scraper_token:
            raise ThordataConfigError("scraper_token is required for Task Builder")
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
            raise ThordataConfigError(
                "scraper_token is required for Video Task Builder"
            )
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

    @property
    def browser(self):
        """Get a browser session for automation.

        Requires playwright: pip install thordata[browser]

        Returns:
            BrowserSession instance

        Example:
            async with AsyncThordataClient() as client:
                session = client.browser
                await session.navigate("https://example.com")
                snapshot = await session.snapshot()
        """
        try:
            from .browser import BrowserSession

            return BrowserSession(self)
        except ImportError as e:
            raise ImportError(
                "Playwright is required for browser automation. "
                "Install it with: pip install thordata[browser]"
            ) from e
