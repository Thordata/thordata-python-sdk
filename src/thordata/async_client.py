"""
Asynchronous client for the Thordata API.

This module provides the AsyncThordataClient for high-concurrency workloads,
built on aiohttp.

Example:
    >>> import asyncio
    >>> from thordata import AsyncThordataClient
    >>>
    >>> async def main():
    ...     async with AsyncThordataClient(
    ...         scraper_token="your_token",
    ...         public_token="your_public_token",
    ...         public_key="your_public_key"
    ...     ) as client:
    ...         response = await client.get("https://httpbin.org/ip")
    ...         print(await response.json())
    >>>
    >>> asyncio.run(main())
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
from datetime import date
from typing import Any
from urllib.parse import quote

import aiohttp

from . import __version__ as _sdk_version
from ._utils import (
    build_auth_headers,
    build_builder_headers,
    build_public_api_headers,
    build_user_agent,
    decode_base64_image,
    extract_error_message,
    parse_json_response,
)
from .async_unlimited import AsyncUnlimitedNamespace
from .enums import Engine, ProxyType
from .exceptions import (
    ThordataConfigError,
    ThordataNetworkError,
    ThordataTimeoutError,
    raise_for_code,
)
from .models import (
    CommonSettings,
    ProxyConfig,
    ProxyProduct,
    ProxyServer,
    ProxyUserList,
    ScraperTaskConfig,
    SerpRequest,
    UniversalScrapeRequest,
    UsageStatistics,
    VideoTaskConfig,
)
from .retry import RetryConfig
from .serp_engines import AsyncSerpNamespace

logger = logging.getLogger(__name__)


# =========================================================================
# Main Client Class
# =========================================================================


class AsyncThordataClient:
    """The official asynchronous Python client for Thordata.

    Designed for high-concurrency AI agents and data pipelines.

    Args:
        scraper_token: The API token from your Dashboard.
        public_token: The public API token.
        public_key: The public API key.
        proxy_host: Custom proxy gateway host.
        proxy_port: Custom proxy gateway port.
        timeout: Default request timeout in seconds.
        api_timeout: Default API request timeout in seconds.
        retry_config: Configuration for automatic retries.
        auth_mode: Authentication mode for scraping APIs ("bearer" or "header_token").
        scraperapi_base_url: Override base URL for SERP API.
        universalapi_base_url: Override base URL for Universal Scraping API.
        web_scraper_api_base_url: Override base URL for Web Scraper API.
        locations_base_url: Override base URL for Locations API.

    Example:
        >>> async with AsyncThordataClient(
        ...     scraper_token="token",
        ...     public_token="pub_token",
        ...     public_key="pub_key"
        ... ) as client:
        ...     results = await client.serp_search("python")
    """

    # API Endpoints (same as sync client)
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
        """Initialize the Async Thordata Client.

        Args:
            scraper_token: Token for SERP/Universal scraping APIs.
            public_token: Public API token for account/management operations.
            public_key: Public API key for account/management operations.
            proxy_host: Default proxy host for residential proxies.
            proxy_port: Default proxy port for residential proxies.
            timeout: Default timeout for proxy requests.
            api_timeout: Default timeout for API requests.
            retry_config: Configuration for retry behavior.
            auth_mode: Authentication mode for scraper_token ("bearer" or "header_token").
            scraperapi_base_url: Override base URL for SERP API.
            universalapi_base_url: Override base URL for Universal Scraping API.
            web_scraper_api_base_url: Override base URL for Web Scraper API.
            locations_base_url: Override base URL for Locations API.
        """
        self.scraper_token = scraper_token
        self.public_token = public_token
        self.public_key = public_key

        # Proxy configuration
        self._proxy_host = proxy_host
        self._proxy_port = proxy_port

        # Timeout configuration
        self._default_timeout = aiohttp.ClientTimeout(total=timeout)
        self._api_timeout = aiohttp.ClientTimeout(total=api_timeout)

        # Retry configuration
        self._retry_config = retry_config or RetryConfig()

        # Authentication mode (for scraping APIs)
        self._auth_mode = auth_mode.lower()
        if self._auth_mode not in ("bearer", "header_token"):
            raise ThordataConfigError(
                f"Invalid auth_mode: {auth_mode}. Must be 'bearer' or 'header_token'."
            )

        # Base URLs (allow override via args or env vars for testing and custom routing)
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

        # Keep these env overrides for now
        gateway_base = os.getenv(
            "THORDATA_GATEWAY_BASE_URL", "https://api.thordata.com/api/gateway"
        )
        child_base = os.getenv(
            "THORDATA_CHILD_BASE_URL", "https://api.thordata.com/api/child"
        )

        self._gateway_base_url = gateway_base
        self._child_base_url = child_base

        self._serp_url = f"{scraperapi_base}/request"
        self._builder_url = f"{scraperapi_base}/builder"
        self._video_builder_url = f"{scraperapi_base}/video_builder"
        self._universal_url = f"{universalapi_base}/request"

        self._status_url = f"{web_scraper_api_base}/tasks-status"
        self._download_url = f"{web_scraper_api_base}/tasks-download"
        self._list_url = f"{web_scraper_api_base}/tasks-list"

        self._locations_base_url = locations_base
        self._usage_stats_url = (
            f"{locations_base.replace('/locations', '')}/account/usage-statistics"
        )
        self._proxy_users_url = (
            f"{locations_base.replace('/locations', '')}/proxy-users"
        )

        whitelist_base = os.getenv(
            "THORDATA_WHITELIST_BASE_URL", "https://api.thordata.com/api"
        )
        self._whitelist_url = f"{whitelist_base}/whitelisted-ips"

        proxy_api_base = os.getenv(
            "THORDATA_PROXY_API_BASE_URL", "https://openapi.thordata.com/api"
        )
        self._proxy_list_url = f"{proxy_api_base}/proxy/proxy-list"
        self._proxy_expiration_url = f"{proxy_api_base}/proxy/expiration-time"

        # Session initialized lazily
        self._session: aiohttp.ClientSession | None = None

        # Namespaced Access (e.g. client.serp.google.maps(...))
        self.serp = AsyncSerpNamespace(self)
        self.unlimited = AsyncUnlimitedNamespace(self)

    # =========================================================================
    # Context Manager
    # =========================================================================

    async def __aenter__(self) -> AsyncThordataClient:
        """Async context manager entry."""
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession(
                timeout=self._api_timeout,
                trust_env=True,
                headers={"User-Agent": build_user_agent(_sdk_version, "aiohttp")},
            )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Async context manager exit."""
        await self.close()

    async def close(self) -> None:
        """Close the underlying aiohttp session."""
        if self._session and not self._session.closed:
            await self._session.close()
            self._session = None

    def _get_session(self) -> aiohttp.ClientSession:
        """Get the session, raising if not initialized."""
        if self._session is None or self._session.closed:
            raise RuntimeError(
                "Client session not initialized. "
                "Use 'async with AsyncThordataClient(...) as client:'"
            )
        return self._session

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
        """Send an async GET request through the Proxy Network.

        Args:
            url: The target URL.
            proxy_config: Custom proxy configuration.
            **kwargs: Additional aiohttp arguments.

        Returns:
            The aiohttp response object.

        Note:
            aiohttp has limited support for HTTPS proxies (TLS to proxy / TLS-in-TLS).
            For HTTPS proxy endpoints, please use ThordataClient.get/post (sync client).
        """
        session = self._get_session()

        logger.debug(f"Async Proxy GET: {url}")

        if proxy_config is None:
            proxy_config = self._get_default_proxy_config_from_env()

        if proxy_config is None:
            raise ThordataConfigError(
                "Proxy credentials are missing. "
                "Pass proxy_config=ProxyConfig(username=..., password=..., product=...) "
                "or set THORDATA_RESIDENTIAL_USERNAME/THORDATA_RESIDENTIAL_PASSWORD."
            )

        if getattr(proxy_config, "protocol", "http").lower() == "https":
            raise ThordataConfigError(
                "Proxy Network requires an HTTPS proxy endpoint. "
                "aiohttp support for 'https://' proxies is limited. "
                "Please use ThordataClient.get/post (sync client) for Proxy Network requests."
            )
        proxy_url, proxy_auth = proxy_config.to_aiohttp_config()

        try:
            return await session.get(
                url, proxy=proxy_url, proxy_auth=proxy_auth, **kwargs
            )
        except asyncio.TimeoutError as e:
            raise ThordataTimeoutError(
                f"Async request timed out: {e}", original_error=e
            ) from e
        except aiohttp.ClientError as e:
            raise ThordataNetworkError(
                f"Async request failed: {e}", original_error=e
            ) from e

    async def post(
        self,
        url: str,
        *,
        proxy_config: ProxyConfig | None = None,
        **kwargs: Any,
    ) -> aiohttp.ClientResponse:
        """Send an async POST request through the Proxy Network.

        Args:
            url: The target URL.
            proxy_config: Custom proxy configuration.
            **kwargs: Additional aiohttp arguments.

        Returns:
            The aiohttp response object.
        """
        session = self._get_session()

        logger.debug(f"Async Proxy POST: {url}")

        if proxy_config is None:
            proxy_config = self._get_default_proxy_config_from_env()

        if proxy_config is None:
            raise ThordataConfigError(
                "Proxy credentials are missing. "
                "Pass proxy_config=ProxyConfig(username=..., password=..., product=...) "
                "or set THORDATA_RESIDENTIAL_USERNAME/THORDATA_RESIDENTIAL_PASSWORD."
            )

        if getattr(proxy_config, "protocol", "http").lower() == "https":
            raise ThordataConfigError(
                "Proxy Network requires an HTTPS proxy endpoint. "
                "aiohttp support for 'https://' proxies is limited. "
                "Please use ThordataClient.get/post (sync client) for Proxy Network requests."
            )
        proxy_url, proxy_auth = proxy_config.to_aiohttp_config()

        try:
            return await session.post(
                url, proxy=proxy_url, proxy_auth=proxy_auth, **kwargs
            )
        except asyncio.TimeoutError as e:
            raise ThordataTimeoutError(
                f"Async request timed out: {e}", original_error=e
            ) from e
        except aiohttp.ClientError as e:
            raise ThordataNetworkError(
                f"Async request failed: {e}", original_error=e
            ) from e

    # =========================================================================
    # SERP API Methods
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
        """Execute an async SERP search.

        Args:
            query: Search keywords.
            engine: Search engine (GOOGLE, BING, etc.).
            num: Number of results.
            country: Country code for localization.
            language: Language code.
            search_type: Type of search (images, news, video, etc.).
            device: Device type ('desktop', 'mobile', 'tablet').
            render_js: Enable JavaScript rendering.
            no_cache: Disable internal caching.
            output_format: 'json' or 'html'.
            **kwargs: Additional parameters.

        Returns:
            Parsed JSON results or dict with 'html' key.
        """
        if not self.scraper_token:
            raise ThordataConfigError("scraper_token is required for SERP API")

        session = self._get_session()

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

        payload = request.to_payload()
        token = self.scraper_token or ""
        headers = build_auth_headers(token, mode=self._auth_mode)

        logger.info(f"Async SERP Search: {engine_str} - {query}")

        try:
            async with session.post(
                self._serp_url,
                data=payload,
                headers=headers,
            ) as response:
                response.raise_for_status()

                if output_format.lower() == "json":
                    data = await response.json()

                    if isinstance(data, dict):
                        code = data.get("code")
                        if code is not None and code != 200:
                            msg = extract_error_message(data)
                            raise_for_code(
                                f"SERP API Error: {msg}",
                                code=code,
                                payload=data,
                            )

                    return parse_json_response(data)

                text = await response.text()
                return {"html": text}

        except asyncio.TimeoutError as e:
            raise ThordataTimeoutError(
                f"SERP request timed out: {e}",
                original_error=e,
            ) from e
        except aiohttp.ClientError as e:
            raise ThordataNetworkError(
                f"SERP request failed: {e}",
                original_error=e,
            ) from e

    async def serp_search_advanced(self, request: SerpRequest) -> dict[str, Any]:
        """Execute an async SERP search using a SerpRequest object.

        Args:
            request: SerpRequest object with search parameters.

        Returns:
            Parsed search results.
        """
        session = self._get_session()
        if not self.scraper_token:
            raise ThordataConfigError("scraper_token is required for SERP API")

        payload = request.to_payload()
        headers = build_auth_headers(self.scraper_token, mode=self._auth_mode)

        logger.info(f"Async SERP Advanced: {request.engine} - {request.query}")

        try:
            async with session.post(
                self._serp_url,
                data=payload,
                headers=headers,
            ) as response:
                response.raise_for_status()

                if request.output_format.lower() == "json":
                    data = await response.json()

                    if isinstance(data, dict):
                        code = data.get("code")
                        if code is not None and code != 200:
                            msg = extract_error_message(data)
                            raise_for_code(
                                f"SERP API Error: {msg}",
                                code=code,
                                payload=data,
                            )

                    return parse_json_response(data)

                text = await response.text()
                return {"html": text}

        except asyncio.TimeoutError as e:
            raise ThordataTimeoutError(
                f"SERP request timed out: {e}",
                original_error=e,
            ) from e
        except aiohttp.ClientError as e:
            raise ThordataNetworkError(
                f"SERP request failed: {e}",
                original_error=e,
            ) from e

    # =========================================================================
    # Universal Scraping API Methods
    # =========================================================================

    async def universal_scrape(
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
        """Async scrape using Universal API (Web Unlocker).

        Args:
            url: Target URL.
            js_render: Enable JavaScript rendering.
            output_format: "html" or "png".
            country: Geo-targeting country.
            block_resources: Resources to block (e.g., "script,css").
            wait: Wait time in milliseconds before fetching.
            wait_for: CSS selector to wait for before fetching.

        Returns:
            HTML string or PNG bytes.
        """
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

        return await self.universal_scrape_advanced(request)

    async def universal_scrape_advanced(
        self, request: UniversalScrapeRequest
    ) -> str | bytes:
        """Async scrape using a UniversalScrapeRequest object.

        Args:
            request: UniversalScrapeRequest object with scrape parameters.

        Returns:
            HTML string or PNG bytes.
        """
        session = self._get_session()
        if not self.scraper_token:
            raise ThordataConfigError("scraper_token is required for Universal API")

        payload = request.to_payload()
        headers = build_auth_headers(self.scraper_token, mode=self._auth_mode)

        logger.info(f"Async Universal Scrape: {request.url}")

        try:
            async with session.post(
                self._universal_url, data=payload, headers=headers
            ) as response:
                response.raise_for_status()

                try:
                    resp_json = await response.json()
                except ValueError:
                    if request.output_format.lower() == "png":
                        return await response.read()
                    return await response.text()

                # Check for API errors
                if isinstance(resp_json, dict):
                    code = resp_json.get("code")
                    if code is not None and code != 200:
                        msg = extract_error_message(resp_json)
                        raise_for_code(
                            f"Universal API Error: {msg}", code=code, payload=resp_json
                        )

                if "html" in resp_json:
                    return resp_json["html"]

                if "png" in resp_json:
                    return decode_base64_image(resp_json["png"])

                return str(resp_json)

        except asyncio.TimeoutError as e:
            raise ThordataTimeoutError(
                f"Universal scrape timed out: {e}", original_error=e
            ) from e
        except aiohttp.ClientError as e:
            raise ThordataNetworkError(
                f"Universal scrape failed: {e}", original_error=e
            ) from e

    # =========================================================================
    # Web Scraper API - Task Management
    # =========================================================================

    async def create_scraper_task(
        self,
        file_name: str,
        spider_id: str,
        spider_name: str,
        parameters: dict[str, Any],
        universal_params: dict[str, Any] | None = None,
    ) -> str:
        """Create an async Web Scraper task.

        Args:
            file_name: Name for the output file (supports {{TasksID}} template).
            spider_id: Spider identifier from Dashboard.
            spider_name: Spider name (target domain, e.g., "amazon.com").
            parameters: Spider-specific parameters.
            universal_params: Global spider settings.

        Returns:
            Task ID.
        """
        config = ScraperTaskConfig(
            file_name=file_name,
            spider_id=spider_id,
            spider_name=spider_name,
            parameters=parameters,
            universal_params=universal_params,
        )

        return await self.create_scraper_task_advanced(config)

    async def create_scraper_task_advanced(self, config: ScraperTaskConfig) -> str:
        """Create a task using ScraperTaskConfig.

        Args:
            config: ScraperTaskConfig object with task configuration.

        Returns:
            Task ID.
        """
        self._require_public_credentials()
        session = self._get_session()
        if not self.scraper_token:
            raise ThordataConfigError("scraper_token is required for Task Builder")

        payload = config.to_payload()
        # Builder needs 3 headers: token, key, Authorization Bearer
        headers = build_builder_headers(
            self.scraper_token,
            self.public_token or "",
            self.public_key or "",
        )

        logger.info(f"Async Task Creation: {config.spider_name}")

        try:
            async with session.post(
                self._builder_url, data=payload, headers=headers
            ) as response:
                response.raise_for_status()
                data = await response.json(content_type=None)

                code = data.get("code")
                if code != 200:
                    msg = extract_error_message(data)
                    raise_for_code(
                        f"Task creation failed: {msg}", code=code, payload=data
                    )

                return data["data"]["task_id"]

        except aiohttp.ClientError as e:
            raise ThordataNetworkError(
                f"Task creation failed: {e}", original_error=e
            ) from e

    async def create_video_task(
        self,
        file_name: str,
        spider_id: str,
        spider_name: str,
        parameters: dict[str, Any],
        common_settings: CommonSettings,
    ) -> str:
        """Create a YouTube video/audio download task.

        Args:
            file_name: Name for the output file.
            spider_id: Spider identifier (e.g., "youtube_video_by-url").
            spider_name: Target site (e.g., "youtube.com").
            parameters: Spider-specific parameters (URLs, etc.).
            common_settings: Video/audio settings (resolution, subtitles, etc.).

        Returns:
            Task ID.
        """
        config = VideoTaskConfig(
            file_name=file_name,
            spider_id=spider_id,
            spider_name=spider_name,
            parameters=parameters,
            common_settings=common_settings,
        )

        return await self.create_video_task_advanced(config)

    async def create_video_task_advanced(self, config: VideoTaskConfig) -> str:
        """Create a video task using VideoTaskConfig object.

        Args:
            config: VideoTaskConfig object with task configuration.

        Returns:
            Task ID.
        """
        self._require_public_credentials()
        session = self._get_session()
        if not self.scraper_token:
            raise ThordataConfigError(
                "scraper_token is required for Video Task Builder"
            )

        payload = config.to_payload()
        headers = build_builder_headers(
            self.scraper_token,
            self.public_token or "",
            self.public_key or "",
        )

        logger.info(
            f"Async Video Task Creation: {config.spider_name} - {config.spider_id}"
        )

        try:
            async with session.post(
                self._video_builder_url,
                data=payload,
                headers=headers,
                timeout=self._api_timeout,
            ) as response:
                response.raise_for_status()
                data = await response.json()

                code = data.get("code")
                if code != 200:
                    msg = extract_error_message(data)
                    raise_for_code(
                        f"Video task creation failed: {msg}", code=code, payload=data
                    )

                return data["data"]["task_id"]

        except asyncio.TimeoutError as e:
            raise ThordataTimeoutError(
                f"Video task creation timed out: {e}", original_error=e
            ) from e
        except aiohttp.ClientError as e:
            raise ThordataNetworkError(
                f"Video task creation failed: {e}", original_error=e
            ) from e

    async def get_task_status(self, task_id: str) -> str:
        """Check async task status.

        Args:
            task_id: Task identifier.

        Returns:
            Status string (running, success, failed, etc.).

        Raises:
            ThordataConfigError: If public credentials are missing.
            ThordataAPIError: If API returns a non-200 code.
            ThordataNetworkError: If network/HTTP request fails.
        """
        self._require_public_credentials()
        session = self._get_session()

        headers = build_public_api_headers(
            self.public_token or "", self.public_key or ""
        )
        payload = {"tasks_ids": task_id}

        try:
            async with session.post(
                self._status_url, data=payload, headers=headers
            ) as response:
                response.raise_for_status()
                data = await response.json(content_type=None)

                if isinstance(data, dict):
                    code = data.get("code")
                    if code is not None and code != 200:
                        msg = extract_error_message(data)
                        raise_for_code(
                            f"Task status API Error: {msg}",
                            code=code,
                            payload=data,
                        )

                    items = data.get("data") or []
                    for item in items:
                        if str(item.get("task_id")) == str(task_id):
                            return item.get("status", "unknown")

                    return "unknown"

                raise ThordataNetworkError(
                    f"Unexpected task status response type: {type(data).__name__}",
                    original_error=None,
                )

        except asyncio.TimeoutError as e:
            raise ThordataTimeoutError(
                f"Async status check timed out: {e}", original_error=e
            ) from e
        except aiohttp.ClientError as e:
            raise ThordataNetworkError(
                f"Async status check failed: {e}", original_error=e
            ) from e

    async def safe_get_task_status(self, task_id: str) -> str:
        """Backward-compatible status check.

        Returns:
            Status string, or "error" on any exception.
        """
        try:
            return await self.get_task_status(task_id)
        except Exception:
            return "error"

    async def get_task_result(self, task_id: str, file_type: str = "json") -> str:
        """Get download URL for completed task.

        Args:
            task_id: Task identifier.
            file_type: File type to download (json, csv, video, audio, subtitle).

        Returns:
            Download URL.
        """
        self._require_public_credentials()
        session = self._get_session()

        headers = build_public_api_headers(
            self.public_token or "", self.public_key or ""
        )
        payload = {"tasks_id": task_id, "type": file_type}

        logger.info(f"Async getting result for Task: {task_id}")

        try:
            async with session.post(
                self._download_url, data=payload, headers=headers
            ) as response:
                data = await response.json(content_type=None)
                code = data.get("code")

                if code == 200 and data.get("data"):
                    return data["data"]["download"]

                msg = extract_error_message(data)
                raise_for_code(f"Get result failed: {msg}", code=code, payload=data)
                # This line won't be reached, but satisfies mypy
                raise RuntimeError("Unexpected state")

        except aiohttp.ClientError as e:
            raise ThordataNetworkError(
                f"Get result failed: {e}", original_error=e
            ) from e

    async def list_tasks(
        self,
        page: int = 1,
        size: int = 20,
    ) -> dict[str, Any]:
        """List all Web Scraper tasks.

        Args:
            page: Page number (starts from 1).
            size: Number of tasks per page.

        Returns:
            Dict containing 'count' and 'list' of tasks.
        """
        self._require_public_credentials()
        session = self._get_session()

        headers = build_public_api_headers(
            self.public_token or "", self.public_key or ""
        )
        payload: dict[str, Any] = {}
        if page:
            payload["page"] = str(page)
        if size:
            payload["size"] = str(size)

        logger.info(f"Async listing tasks: page={page}, size={size}")

        try:
            async with session.post(
                self._list_url,
                data=payload,
                headers=headers,
                timeout=self._api_timeout,
            ) as response:
                response.raise_for_status()
                data = await response.json(content_type=None)

                code = data.get("code")
                if code != 200:
                    msg = extract_error_message(data)
                    raise_for_code(f"List tasks failed: {msg}", code=code, payload=data)

                return data.get("data", {"count": 0, "list": []})

        except asyncio.TimeoutError as e:
            raise ThordataTimeoutError(
                f"List tasks timed out: {e}", original_error=e
            ) from e
        except aiohttp.ClientError as e:
            raise ThordataNetworkError(
                f"List tasks failed: {e}", original_error=e
            ) from e

    async def wait_for_task(
        self,
        task_id: str,
        *,
        poll_interval: float = 5.0,
        max_wait: float = 600.0,
    ) -> str:
        """Wait for a task to complete.

        Args:
            task_id: Task identifier.
            poll_interval: Polling interval in seconds.
            max_wait: Maximum time to wait in seconds.

        Returns:
            Final status of the task.
        """
        import time

        start = time.monotonic()

        while (time.monotonic() - start) < max_wait:
            status = await self.get_task_status(task_id)

            logger.debug(f"Task {task_id} status: {status}")

            terminal_statuses = {
                "ready",
                "success",
                "finished",
                "failed",
                "error",
                "cancelled",
            }

            if status.lower() in terminal_statuses:
                return status

            await asyncio.sleep(poll_interval)

        raise TimeoutError(f"Task {task_id} did not complete within {max_wait} seconds")

    async def run_task(
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
        """Async high-level wrapper to run a task and wait for result.

        Lifecycle: Create -> Poll (Backoff) -> Get Download URL.

        Args:
            file_name: Name for the output file.
            spider_id: Spider identifier from Dashboard.
            spider_name: Spider name (target domain).
            parameters: Spider-specific parameters.
            universal_params: Global spider settings.
            max_wait: Maximum seconds to wait for completion.
            initial_poll_interval: Starting poll interval in seconds.
            max_poll_interval: Maximum poll interval cap.
            include_errors: Whether to include error logs.

        Returns:
            The download URL.
        """
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
            task_id = await self.create_video_task_advanced(config_video)
        else:
            config = ScraperTaskConfig(
                file_name=file_name,
                spider_id=spider_id,
                spider_name=spider_name,
                parameters=parameters,
                universal_params=universal_params,
                include_errors=include_errors,
            )
            task_id = await self.create_scraper_task_advanced(config)

        logger.info(f"Async Task created: {task_id}. Polling...")

        # 2. Poll Status
        import time

        start_time = time.monotonic()
        current_poll = initial_poll_interval

        while (time.monotonic() - start_time) < max_wait:
            status = await self.get_task_status(task_id)
            status_lower = status.lower()

            if status_lower in {"ready", "success", "finished"}:
                logger.info(f"Task {task_id} ready.")
                return await self.get_task_result(task_id)

            if status_lower in {"failed", "error", "cancelled"}:
                raise ThordataNetworkError(
                    f"Task {task_id} failed with status: {status}"
                )

            await asyncio.sleep(current_poll)
            current_poll = min(current_poll * 1.5, max_poll_interval)

        raise ThordataTimeoutError(f"Async Task {task_id} timed out after {max_wait}s")

    # =========================================================================
    # Account & Usage Methods
    # =========================================================================

    async def get_usage_statistics(
        self,
        from_date: str | date,
        to_date: str | date,
    ) -> UsageStatistics:
        """Get account usage statistics for a date range.

        Args:
            from_date: Start date (YYYY-MM-DD string or date object).
            to_date: End date (YYYY-MM-DD string or date object).

        Returns:
            UsageStatistics object with traffic data.
        """
        self._require_public_credentials()
        session = self._get_session()

        # Convert dates to strings
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

        logger.info(f"Async getting usage statistics: {from_date} to {to_date}")

        try:
            async with session.get(
                self._usage_stats_url,
                params=params,
                timeout=self._api_timeout,
            ) as response:
                response.raise_for_status()
                data = await response.json()

                if isinstance(data, dict):
                    code = data.get("code")
                    if code is not None and code != 200:
                        msg = extract_error_message(data)
                        raise_for_code(
                            f"Usage statistics error: {msg}",
                            code=code,
                            payload=data,
                        )

                    usage_data = data.get("data", data)
                    return UsageStatistics.from_dict(usage_data)

                raise ThordataNetworkError(
                    f"Unexpected usage statistics response: {type(data).__name__}",
                    original_error=None,
                )

        except asyncio.TimeoutError as e:
            raise ThordataTimeoutError(
                f"Usage statistics timed out: {e}", original_error=e
            ) from e
        except aiohttp.ClientError as e:
            raise ThordataNetworkError(
                f"Usage statistics failed: {e}", original_error=e
            ) from e

    async def get_residential_balance(self) -> dict[str, Any]:
        """Get residential proxy balance.

        Uses public_token/public_key via gateway API.

        Returns:
            Balance data dictionary.
        """
        session = self._get_session()
        headers = self._build_gateway_headers()

        logger.info("Async getting residential proxy balance")

        try:
            async with session.post(
                f"{self._gateway_base_url}/getFlowBalance",
                headers=headers,
                data={},
                timeout=self._api_timeout,
            ) as response:
                response.raise_for_status()
                data = await response.json()

                code = data.get("code")
                if code != 200:
                    msg = extract_error_message(data)
                    raise_for_code(
                        f"Get balance failed: {msg}", code=code, payload=data
                    )

                return data.get("data", {})

        except asyncio.TimeoutError as e:
            raise ThordataTimeoutError(
                f"Get balance timed out: {e}", original_error=e
            ) from e
        except aiohttp.ClientError as e:
            raise ThordataNetworkError(
                f"Get balance failed: {e}", original_error=e
            ) from e

    async def get_residential_usage(
        self,
        start_time: str | int,
        end_time: str | int,
    ) -> dict[str, Any]:
        """Get residential proxy usage records.

        Uses public_token/public_key via gateway API.

        Args:
            start_time: Start timestamp or date string.
            end_time: End timestamp or date string.

        Returns:
            Usage data dictionary.
        """
        session = self._get_session()
        headers = self._build_gateway_headers()
        payload = {"start_time": str(start_time), "end_time": str(end_time)}

        logger.info(f"Async getting residential usage: {start_time} to {end_time}")

        try:
            async with session.post(
                f"{self._gateway_base_url}/usageRecord",
                headers=headers,
                data=payload,
                timeout=self._api_timeout,
            ) as response:
                response.raise_for_status()
                data = await response.json()

                code = data.get("code")
                if code != 200:
                    msg = extract_error_message(data)
                    raise_for_code(f"Get usage failed: {msg}", code=code, payload=data)

                return data.get("data", {})

        except asyncio.TimeoutError as e:
            raise ThordataTimeoutError(
                f"Get usage timed out: {e}", original_error=e
            ) from e
        except aiohttp.ClientError as e:
            raise ThordataNetworkError(
                f"Get usage failed: {e}", original_error=e
            ) from e

    async def get_traffic_balance(self) -> float:
        """Get traffic balance in KB via Public API."""
        self._require_public_credentials()
        # FIX: Ensure params are strings and dict structure satisfies type checker
        # _require_public_credentials ensures tokens are not None at runtime,
        # but for type checking we cast or assert.
        params = {
            "token": str(self.public_token),
            "key": str(self.public_key),
        }
        api_base = self._locations_base_url.replace("/locations", "")

        try:
            async with self._get_session().get(
                f"{api_base}/account/traffic-balance", params=params
            ) as resp:
                data = await resp.json()
                if data.get("code") != 200:
                    raise_for_code(
                        "Get traffic balance failed",
                        code=data.get("code"),
                        payload=data,
                    )
                return float(data.get("data", {}).get("traffic_balance", 0))
        except aiohttp.ClientError as e:
            raise ThordataNetworkError(f"Request failed: {e}", original_error=e) from e

    async def get_proxy_user_usage(
        self,
        username: str,
        start_date: str | date,
        end_date: str | date,
        proxy_type: ProxyType | int = ProxyType.RESIDENTIAL,
    ) -> list[dict[str, Any]]:
        """Get user usage statistics."""
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

        try:
            async with self._get_session().get(
                f"{self._proxy_users_url}/usage-statistics", params=params
            ) as resp:
                data = await resp.json()
                if data.get("code") != 200:
                    raise_for_code(
                        "Get user usage failed", code=data.get("code"), payload=data
                    )
                return data.get("data") or []
        except aiohttp.ClientError as e:
            raise ThordataNetworkError(f"Request failed: {e}", original_error=e) from e

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
        """Async extract IPs."""
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

        try:
            async with self._get_session().get(
                f"{base_url}{endpoint}", params=params
            ) as resp:
                if return_type == "json":
                    data = await resp.json()
                    if isinstance(data, dict):
                        if data.get("code") == 0 or data.get("code") == 200:
                            raw_list = data.get("data") or []
                            return [f"{item['ip']}:{item['port']}" for item in raw_list]
                        else:
                            raise_for_code(
                                "Extract IPs failed",
                                code=data.get("code"),
                                payload=data,
                            )
                    return []
                else:
                    text = await resp.text()
                    text = text.strip()
                    if text.startswith("{") and "code" in text:
                        try:
                            err_data = json.loads(text)
                            raise_for_code(
                                "Extract IPs failed",
                                code=err_data.get("code"),
                                payload=err_data,
                            )
                        except json.JSONDecodeError:
                            pass

                    actual_sep = sep.replace("\\r", "\r").replace("\\n", "\n")
                    return [
                        line.strip() for line in text.split(actual_sep) if line.strip()
                    ]

        except aiohttp.ClientError as e:
            raise ThordataNetworkError(f"Request failed: {e}", original_error=e) from e

    async def get_wallet_balance(self) -> float:
        """Get wallet balance via Public API."""
        self._require_public_credentials()
        # FIX: Ensure params are strings
        params = {
            "token": str(self.public_token),
            "key": str(self.public_key),
        }
        api_base = self._locations_base_url.replace("/locations", "")

        try:
            async with self._get_session().get(
                f"{api_base}/account/wallet-balance", params=params
            ) as resp:
                data = await resp.json()
                if data.get("code") != 200:
                    raise_for_code(
                        "Get wallet balance failed", code=data.get("code"), payload=data
                    )
                return float(data.get("data", {}).get("balance", 0))
        except aiohttp.ClientError as e:
            raise ThordataNetworkError(f"Request failed: {e}", original_error=e) from e

    # =========================================================================
    # Proxy Users Management (Sub-accounts)
    # =========================================================================

    async def list_proxy_users(
        self, proxy_type: ProxyType | int = ProxyType.RESIDENTIAL
    ) -> ProxyUserList:
        """List all proxy users (sub-accounts).

        Args:
            proxy_type: Proxy product type.

        Returns:
            ProxyUserList with user information.
        """
        self._require_public_credentials()
        session = self._get_session()

        params = {
            "token": self.public_token,
            "key": self.public_key,
            "proxy_type": str(
                int(proxy_type) if isinstance(proxy_type, ProxyType) else proxy_type
            ),
        }

        logger.info(f"Async listing proxy users: type={params['proxy_type']}")

        try:
            async with session.get(
                f"{self._proxy_users_url}/user-list",
                params=params,
                timeout=self._api_timeout,
            ) as response:
                response.raise_for_status()
                data = await response.json()

                if isinstance(data, dict):
                    code = data.get("code")
                    if code is not None and code != 200:
                        msg = extract_error_message(data)
                        raise_for_code(
                            f"List proxy users error: {msg}", code=code, payload=data
                        )

                    user_data = data.get("data", data)
                    return ProxyUserList.from_dict(user_data)

                raise ThordataNetworkError(
                    f"Unexpected proxy users response: {type(data).__name__}",
                    original_error=None,
                )

        except asyncio.TimeoutError as e:
            raise ThordataTimeoutError(
                f"List users timed out: {e}", original_error=e
            ) from e
        except aiohttp.ClientError as e:
            raise ThordataNetworkError(
                f"List users failed: {e}", original_error=e
            ) from e

    async def create_proxy_user(
        self,
        username: str,
        password: str,
        proxy_type: ProxyType | int = ProxyType.RESIDENTIAL,
        traffic_limit: int = 0,
        status: bool = True,
    ) -> dict[str, Any]:
        """Create a new proxy user (sub-account).

        Args:
            username: Sub-account username.
            password: Sub-account password.
            proxy_type: Proxy product type.
            traffic_limit: Traffic limit in MB (0 = unlimited).
            status: Enable or disable the account.

        Returns:
            API response data.
        """
        self._require_public_credentials()
        session = self._get_session()

        headers = build_public_api_headers(
            self.public_token or "", self.public_key or ""
        )

        payload = {
            "proxy_type": str(
                int(proxy_type) if isinstance(proxy_type, ProxyType) else proxy_type
            ),
            "username": username,
            "password": password,
            "traffic_limit": str(traffic_limit),
            "status": "true" if status else "false",
        }

        logger.info(f"Async creating proxy user: {username}")

        try:
            async with session.post(
                f"{self._proxy_users_url}/create-user",
                data=payload,
                headers=headers,
                timeout=self._api_timeout,
            ) as response:
                response.raise_for_status()
                data = await response.json()

                code = data.get("code")
                if code != 200:
                    msg = extract_error_message(data)
                    raise_for_code(
                        f"Create proxy user failed: {msg}", code=code, payload=data
                    )

                return data.get("data", {})

        except asyncio.TimeoutError as e:
            raise ThordataTimeoutError(
                f"Create user timed out: {e}", original_error=e
            ) from e
        except aiohttp.ClientError as e:
            raise ThordataNetworkError(
                f"Create user failed: {e}", original_error=e
            ) from e

    async def update_proxy_user(
        self,
        username: str,
        password: str,  # Added password
        traffic_limit: int | None = None,
        status: bool | None = None,
        proxy_type: ProxyType | int = ProxyType.RESIDENTIAL,
    ) -> dict[str, Any]:
        """Update a proxy user."""
        self._require_public_credentials()
        session = self._get_session()
        headers = build_public_api_headers(
            self.public_token or "", self.public_key or ""
        )

        payload = {
            "proxy_type": str(
                int(proxy_type) if isinstance(proxy_type, ProxyType) else proxy_type
            ),
            "username": username,
            "password": password,  # Include password
        }
        if traffic_limit is not None:
            payload["traffic_limit"] = str(traffic_limit)
        if status is not None:
            payload["status"] = "true" if status else "false"

        try:
            async with session.post(
                f"{self._proxy_users_url}/update-user",
                data=payload,
                headers=headers,
                timeout=self._api_timeout,
            ) as response:
                response.raise_for_status()
                data = await response.json()

                if data.get("code") != 200:
                    raise_for_code(
                        f"Update user failed: {data.get('msg')}",
                        code=data.get("code"),
                        payload=data,
                    )

                return data.get("data", {})

        except aiohttp.ClientError as e:
            raise ThordataNetworkError(
                f"Update user failed: {e}", original_error=e
            ) from e

    async def delete_proxy_user(
        self,
        username: str,
        proxy_type: ProxyType | int = ProxyType.RESIDENTIAL,
    ) -> dict[str, Any]:
        """Delete a proxy user.

        Args:
            username: The sub-account username.
            proxy_type: Proxy product type.

        Returns:
            API response data.
        """
        self._require_public_credentials()
        session = self._get_session()

        headers = build_public_api_headers(
            self.public_token or "", self.public_key or ""
        )

        payload = {
            "proxy_type": str(
                int(proxy_type) if isinstance(proxy_type, ProxyType) else proxy_type
            ),
            "username": username,
        }

        try:
            async with session.post(
                f"{self._proxy_users_url}/delete-user",
                data=payload,
                headers=headers,
                timeout=self._api_timeout,
            ) as response:
                response.raise_for_status()
                data = await response.json()

                code = data.get("code")
                if code != 200:
                    msg = extract_error_message(data)
                    raise_for_code(
                        f"Delete user failed: {msg}", code=code, payload=data
                    )

                return data.get("data", {})

        except asyncio.TimeoutError as e:
            raise ThordataTimeoutError(
                f"Delete user timed out: {e}", original_error=e
            ) from e
        except aiohttp.ClientError as e:
            raise ThordataNetworkError(
                f"Delete user failed: {e}", original_error=e
            ) from e

    # =========================================================================
    # Whitelist IP Management
    # =========================================================================

    async def add_whitelist_ip(
        self,
        ip: str,
        proxy_type: ProxyType | int = ProxyType.RESIDENTIAL,
        status: bool = True,
    ) -> dict[str, Any]:
        """Add an IP to the whitelist for IP authentication.

        Args:
            ip: IP address to whitelist.
            proxy_type: Proxy product type.
            status: Enable or disable the whitelist entry.

        Returns:
            API response data.
        """
        self._require_public_credentials()
        session = self._get_session()

        headers = build_public_api_headers(
            self.public_token or "", self.public_key or ""
        )

        proxy_type_int = (
            int(proxy_type) if isinstance(proxy_type, ProxyType) else proxy_type
        )

        payload = {
            "proxy_type": str(proxy_type_int),
            "ip": ip,
            "status": "true" if status else "false",
        }

        logger.info(f"Async adding whitelist IP: {ip}")

        try:
            async with session.post(
                f"{self._whitelist_url}/add-ip",
                data=payload,
                headers=headers,
                timeout=self._api_timeout,
            ) as response:
                response.raise_for_status()
                data = await response.json()

                code = data.get("code")
                if code != 200:
                    msg = extract_error_message(data)
                    raise_for_code(
                        f"Add whitelist IP failed: {msg}", code=code, payload=data
                    )

                return data.get("data", {})

        except asyncio.TimeoutError as e:
            raise ThordataTimeoutError(
                f"Add whitelist timed out: {e}", original_error=e
            ) from e
        except aiohttp.ClientError as e:
            raise ThordataNetworkError(
                f"Add whitelist failed: {e}", original_error=e
            ) from e

    async def delete_whitelist_ip(
        self,
        ip: str,
        proxy_type: ProxyType | int = ProxyType.RESIDENTIAL,
    ) -> dict[str, Any]:
        """Delete an IP from the whitelist.

        Args:
            ip: The IP address to remove.
            proxy_type: Proxy product type.

        Returns:
            API response data.
        """
        self._require_public_credentials()
        session = self._get_session()

        headers = build_public_api_headers(
            self.public_token or "", self.public_key or ""
        )

        payload = {
            "proxy_type": str(
                int(proxy_type) if isinstance(proxy_type, ProxyType) else proxy_type
            ),
            "ip": ip,
        }

        try:
            async with session.post(
                f"{self._whitelist_url}/delete-ip",
                data=payload,
                headers=headers,
                timeout=self._api_timeout,
            ) as response:
                response.raise_for_status()
                data = await response.json()

                code = data.get("code")
                if code != 200:
                    msg = extract_error_message(data)
                    raise_for_code(
                        f"Delete whitelist IP failed: {msg}", code=code, payload=data
                    )

                return data.get("data", {})

        except asyncio.TimeoutError as e:
            raise ThordataTimeoutError(
                f"Delete whitelist timed out: {e}", original_error=e
            ) from e
        except aiohttp.ClientError as e:
            raise ThordataNetworkError(
                f"Delete whitelist failed: {e}", original_error=e
            ) from e

    async def list_whitelist_ips(
        self,
        proxy_type: ProxyType | int = ProxyType.RESIDENTIAL,
    ) -> list[str]:
        """List all whitelisted IPs.

        Args:
            proxy_type: Proxy product type.

        Returns:
            List of IP address strings.
        """
        self._require_public_credentials()
        session = self._get_session()

        params = {
            k: v
            for k, v in {
                "token": self.public_token,
                "key": self.public_key,
                "proxy_type": str(
                    int(proxy_type) if isinstance(proxy_type, ProxyType) else proxy_type
                ),
            }.items()
            if v is not None
        }

        try:
            async with session.get(
                f"{self._whitelist_url}/ip-list",
                params=params,
                timeout=self._api_timeout,
            ) as response:
                response.raise_for_status()
                data = await response.json()

                if isinstance(data, dict):
                    code = data.get("code")
                    if code is not None and code != 200:
                        msg = extract_error_message(data)
                        raise_for_code(
                            f"List whitelist IPs error: {msg}", code=code, payload=data
                        )

                    items = data.get("data", [])
                    result = []
                    for item in items:
                        if isinstance(item, str):
                            result.append(item)
                        elif isinstance(item, dict) and "ip" in item:
                            result.append(str(item["ip"]))
                        else:
                            result.append(str(item))
                    return result

                raise ThordataNetworkError(
                    f"Unexpected whitelist response: {type(data).__name__}",
                    original_error=None,
                )

        except asyncio.TimeoutError as e:
            raise ThordataTimeoutError(
                f"List whitelist timed out: {e}", original_error=e
            ) from e
        except aiohttp.ClientError as e:
            raise ThordataNetworkError(
                f"List whitelist failed: {e}", original_error=e
            ) from e

    # =========================================================================
    # Locations & ASN Methods
    # =========================================================================

    async def list_countries(
        self, proxy_type: ProxyType | int = ProxyType.RESIDENTIAL
    ) -> list[dict[str, Any]]:
        """List supported countries for proxy locations.

        Args:
            proxy_type: Proxy product type.

        Returns:
            List of country dictionaries.
        """
        return await self._get_locations(
            "countries",
            proxy_type=(
                int(proxy_type) if isinstance(proxy_type, ProxyType) else proxy_type
            ),
        )

    async def list_states(
        self,
        country_code: str,
        proxy_type: ProxyType | int = ProxyType.RESIDENTIAL,
    ) -> list[dict[str, Any]]:
        """List supported states/provinces for a country.

        Args:
            country_code: Country code (e.g., "US", "GB").
            proxy_type: Proxy product type.

        Returns:
            List of state dictionaries.
        """
        return await self._get_locations(
            "states",
            proxy_type=(
                int(proxy_type) if isinstance(proxy_type, ProxyType) else proxy_type
            ),
            country_code=country_code,
        )

    async def list_cities(
        self,
        country_code: str,
        state_code: str | None = None,
        proxy_type: ProxyType | int = ProxyType.RESIDENTIAL,
    ) -> list[dict[str, Any]]:
        """List supported cities for a country/state.

        Args:
            country_code: Country code.
            state_code: State code (optional).
            proxy_type: Proxy product type.

        Returns:
            List of city dictionaries.
        """
        kwargs = {
            "proxy_type": (
                int(proxy_type) if isinstance(proxy_type, ProxyType) else proxy_type
            ),
            "country_code": country_code,
        }
        if state_code:
            kwargs["state_code"] = state_code

        return await self._get_locations("cities", **kwargs)

    async def list_asn(
        self,
        country_code: str,
        proxy_type: ProxyType | int = ProxyType.RESIDENTIAL,
    ) -> list[dict[str, Any]]:
        """List supported ASNs for a country.

        Args:
            country_code: Country code.
            proxy_type: Proxy product type.

        Returns:
            List of ASN dictionaries.
        """
        return await self._get_locations(
            "asn",
            proxy_type=(
                int(proxy_type) if isinstance(proxy_type, ProxyType) else proxy_type
            ),
            country_code=country_code,
        )

    # =========================================================================
    # ISP & Datacenter Proxy Management
    # =========================================================================

    async def list_proxy_servers(
        self,
        proxy_type: int,
    ) -> list[ProxyServer]:
        """List ISP or Datacenter proxy servers.

        Args:
            proxy_type: Proxy type (1=ISP, 2=Datacenter).

        Returns:
            List of ProxyServer objects.
        """
        self._require_public_credentials()
        session = self._get_session()

        params = {
            "token": self.public_token,
            "key": self.public_key,
            "proxy_type": str(proxy_type),
        }

        logger.info(f"Async listing proxy servers: type={proxy_type}")

        try:
            async with session.get(
                self._proxy_list_url,
                params=params,
                timeout=self._api_timeout,
            ) as response:
                response.raise_for_status()
                data = await response.json()

                if isinstance(data, dict):
                    code = data.get("code")
                    if code is not None and code != 200:
                        msg = extract_error_message(data)
                        raise_for_code(
                            f"List proxy servers error: {msg}", code=code, payload=data
                        )

                    server_list = data.get("data", data.get("list", []))
                elif isinstance(data, list):
                    server_list = data
                else:
                    raise ThordataNetworkError(
                        f"Unexpected proxy list response: {type(data).__name__}",
                        original_error=None,
                    )

                return [ProxyServer.from_dict(s) for s in server_list]

        except asyncio.TimeoutError as e:
            raise ThordataTimeoutError(
                f"List servers timed out: {e}", original_error=e
            ) from e
        except aiohttp.ClientError as e:
            raise ThordataNetworkError(
                f"List servers failed: {e}", original_error=e
            ) from e

    async def get_proxy_expiration(
        self,
        ips: str | list[str],
        proxy_type: int,
    ) -> dict[str, Any]:
        """Get expiration time for specific proxy IPs.

        Args:
            ips: Single IP or comma-separated list of IPs.
            proxy_type: Proxy type (1=ISP, 2=Datacenter).

        Returns:
            Dictionary with IP expiration times.
        """
        self._require_public_credentials()
        session = self._get_session()

        if isinstance(ips, list):
            ips = ",".join(ips)

        params = {
            "token": self.public_token,
            "key": self.public_key,
            "proxy_type": str(proxy_type),
            "ips": ips,
        }

        logger.info(f"Async getting proxy expiration: {ips}")

        try:
            async with session.get(
                self._proxy_expiration_url,
                params=params,
                timeout=self._api_timeout,
            ) as response:
                response.raise_for_status()
                data = await response.json()

                if isinstance(data, dict):
                    code = data.get("code")
                    if code is not None and code != 200:
                        msg = extract_error_message(data)
                        raise_for_code(
                            f"Get expiration error: {msg}", code=code, payload=data
                        )

                    return data.get("data", data)

                return data

        except asyncio.TimeoutError as e:
            raise ThordataTimeoutError(
                f"Get expiration timed out: {e}", original_error=e
            ) from e
        except aiohttp.ClientError as e:
            raise ThordataNetworkError(
                f"Get expiration failed: {e}", original_error=e
            ) from e

    async def get_isp_regions(self) -> list[dict[str, Any]]:
        """Get available ISP proxy regions.

        Uses public_token/public_key via gateway API.

        Returns:
            List of ISP region dictionaries.
        """
        session = self._get_session()
        headers = self._build_gateway_headers()

        logger.info("Async getting ISP regions")

        try:
            async with session.post(
                f"{self._gateway_base_url}/getRegionIsp",
                headers=headers,
                data={},
                timeout=self._api_timeout,
            ) as response:
                response.raise_for_status()
                data = await response.json()

                code = data.get("code")
                if code != 200:
                    msg = extract_error_message(data)
                    raise_for_code(
                        f"Get ISP regions failed: {msg}", code=code, payload=data
                    )

                return data.get("data", [])

        except asyncio.TimeoutError as e:
            raise ThordataTimeoutError(
                f"Get ISP regions timed out: {e}", original_error=e
            ) from e
        except aiohttp.ClientError as e:
            raise ThordataNetworkError(
                f"Get ISP regions failed: {e}", original_error=e
            ) from e

    async def list_isp_proxies(self) -> list[dict[str, Any]]:
        """List ISP proxies.

        Uses public_token/public_key via gateway API.

        Returns:
            List of ISP proxy dictionaries.
        """
        session = self._get_session()
        headers = self._build_gateway_headers()

        logger.info("Async listing ISP proxies")

        try:
            async with session.post(
                f"{self._gateway_base_url}/queryListIsp",
                headers=headers,
                data={},
                timeout=self._api_timeout,
            ) as response:
                response.raise_for_status()
                data = await response.json()

                code = data.get("code")
                if code != 200:
                    msg = extract_error_message(data)
                    raise_for_code(
                        f"List ISP proxies failed: {msg}", code=code, payload=data
                    )

                return data.get("data", [])

        except asyncio.TimeoutError as e:
            raise ThordataTimeoutError(
                f"List ISP proxies timed out: {e}", original_error=e
            ) from e
        except aiohttp.ClientError as e:
            raise ThordataNetworkError(
                f"List ISP proxies failed: {e}", original_error=e
            ) from e

    async def get_isp_wallet_balance(self) -> dict[str, Any]:
        """Get wallet balance for ISP proxies.

        Uses public_token/public_key via gateway API.

        Returns:
            Wallet balance data dictionary.
        """
        session = self._get_session()
        headers = self._build_gateway_headers()

        logger.info("Async getting wallet balance")

        try:
            async with session.post(
                f"{self._gateway_base_url}/getBalance",
                headers=headers,
                data={},
                timeout=self._api_timeout,
            ) as response:
                response.raise_for_status()
                data = await response.json()

                code = data.get("code")
                if code != 200:
                    msg = extract_error_message(data)
                    raise_for_code(
                        f"Get wallet balance failed: {msg}", code=code, payload=data
                    )

                return data.get("data", {})

        except asyncio.TimeoutError as e:
            raise ThordataTimeoutError(
                f"Get wallet balance timed out: {e}", original_error=e
            ) from e
        except aiohttp.ClientError as e:
            raise ThordataNetworkError(
                f"Get wallet balance failed: {e}", original_error=e
            ) from e

    # =========================================================================
    # Internal Helper Methods
    # =========================================================================

    def _require_public_credentials(self) -> None:
        """Ensure public API credentials are available."""
        if not self.public_token or not self.public_key:
            raise ThordataConfigError(
                "public_token and public_key are required for this operation. "
                "Please provide them when initializing AsyncThordataClient."
            )

    def _build_gateway_headers(self) -> dict[str, str]:
        """Headers for gateway-style endpoints."""
        self._require_public_credentials()
        return build_public_api_headers(self.public_token or "", self.public_key or "")

    async def _get_locations(
        self, endpoint: str, **kwargs: Any
    ) -> list[dict[str, Any]]:
        """Internal async locations API call.

        Args:
            endpoint: Location endpoint (countries, states, cities, asn).
            **kwargs: Query parameters.

        Returns:
            List of location dictionaries.
        """
        self._require_public_credentials()

        params = {
            "token": self.public_token or "",
            "key": self.public_key or "",
        }

        for key, value in kwargs.items():
            params[key] = str(value)

        url = f"{self._locations_base_url}/{endpoint}"

        logger.debug(f"Async Locations API: {url}")

        # Create temporary session for this request (no proxy needed)
        async with (
            aiohttp.ClientSession(trust_env=True) as temp_session,
            temp_session.get(url, params=params) as response,
        ):
            response.raise_for_status()
            data = await response.json()

            if isinstance(data, dict):
                code = data.get("code")
                if code is not None and code != 200:
                    msg = data.get("msg", "")
                    raise RuntimeError(
                        f"Locations API error ({endpoint}): code={code}, msg={msg}"
                    )
                return data.get("data") or []

            if isinstance(data, list):
                return data

            return []

    def _get_proxy_endpoint_overrides(
        self, product: ProxyProduct
    ) -> tuple[str | None, int | None, str]:
        """Get proxy endpoint overrides from environment variables."""
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

        port: int | None = None
        if port_raw:
            try:
                port = int(port_raw)
            except ValueError:
                port = None

        return host or None, port, protocol

    def _get_default_proxy_config_from_env(self) -> ProxyConfig | None:
        """Get proxy configuration from environment variables."""
        # Check RESIDENTIAL
        u = os.getenv("THORDATA_RESIDENTIAL_USERNAME")
        p = os.getenv("THORDATA_RESIDENTIAL_PASSWORD")
        if u and p:
            host, port, protocol = self._get_proxy_endpoint_overrides(
                ProxyProduct.RESIDENTIAL
            )
            return ProxyConfig(
                username=u,
                password=p,
                product=ProxyProduct.RESIDENTIAL,
                host=host,
                port=port,
                protocol=protocol,
            )

        # Check DATACENTER
        u = os.getenv("THORDATA_DATACENTER_USERNAME")
        p = os.getenv("THORDATA_DATACENTER_PASSWORD")
        if u and p:
            host, port, protocol = self._get_proxy_endpoint_overrides(
                ProxyProduct.DATACENTER
            )
            return ProxyConfig(
                username=u,
                password=p,
                product=ProxyProduct.DATACENTER,
                host=host,
                port=port,
                protocol=protocol,
            )

        # Check MOBILE
        u = os.getenv("THORDATA_MOBILE_USERNAME")
        p = os.getenv("THORDATA_MOBILE_PASSWORD")
        if u and p:
            host, port, protocol = self._get_proxy_endpoint_overrides(
                ProxyProduct.MOBILE
            )
            return ProxyConfig(
                username=u,
                password=p,
                product=ProxyProduct.MOBILE,
                host=host,
                port=port,
                protocol=protocol,
            )

        return None

    def get_browser_connection_url(
        self, username: str | None = None, password: str | None = None
    ) -> str:
        """
        Generate the WebSocket URL for connecting to Scraping Browser.

        Note: This method is synchronous as it only does string formatting.
        """
        user = (
            username
            or os.getenv("THORDATA_BROWSER_USERNAME")
            or os.getenv("THORDATA_RESIDENTIAL_USERNAME")
        )
        pwd = (
            password
            or os.getenv("THORDATA_BROWSER_PASSWORD")
            or os.getenv("THORDATA_RESIDENTIAL_PASSWORD")
        )

        if not user or not pwd:
            raise ThordataConfigError(
                "Browser credentials missing. Set THORDATA_BROWSER_USERNAME/PASSWORD or pass arguments."
            )

        prefix = "td-customer-"
        # Fixed SIM108 (ternary operator)
        final_user = f"{prefix}{user}" if not user.startswith(prefix) else user

        safe_user = quote(final_user, safe="")
        safe_pass = quote(pwd, safe="")

        return f"wss://{safe_user}:{safe_pass}@ws-browser.thordata.com"
