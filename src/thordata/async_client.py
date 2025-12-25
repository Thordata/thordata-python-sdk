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
import logging
import os
from datetime import date, datetime
from typing import Any, Dict, List, Optional, Union

import aiohttp

from . import __version__ as _sdk_version
from ._utils import (
    build_auth_headers,
    build_builder_headers,
    build_public_api_headers,
    build_sign_headers,
    build_user_agent,
    decode_base64_image,
    extract_error_message,
    parse_json_response,
)
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
    ProxyServer,
    ProxyUser,
    ProxyUserList,
    ScraperTaskConfig,
    SerpRequest,
    UniversalScrapeRequest,
    UsageStatistics,
    VideoTaskConfig,
)
from .retry import RetryConfig

logger = logging.getLogger(__name__)


class AsyncThordataClient:
    """
    The official asynchronous Python client for Thordata.

    Designed for high-concurrency AI agents and data pipelines.

    Args:
        scraper_token: The API token from your Dashboard.
        public_token: The public API token.
        public_key: The public API key.
        proxy_host: Custom proxy gateway host.
        proxy_port: Custom proxy gateway port.
        timeout: Default request timeout in seconds.
        retry_config: Configuration for automatic retries.

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
        scraper_token: str,
        public_token: Optional[str] = None,
        public_key: Optional[str] = None,
        sign: Optional[str] = None,
        api_key: Optional[str] = None,
        proxy_host: str = "pr.thordata.net",
        proxy_port: int = 9999,
        timeout: int = 30,
        api_timeout: int = 60,
        retry_config: Optional[RetryConfig] = None,
        auth_mode: str = "bearer",
        scraperapi_base_url: Optional[str] = None,
        universalapi_base_url: Optional[str] = None,
        web_scraper_api_base_url: Optional[str] = None,
        locations_base_url: Optional[str] = None,
    ) -> None:
        """Initialize the Async Thordata Client."""
        if not scraper_token:
            raise ThordataConfigError("scraper_token is required")

        self.scraper_token = scraper_token
        self.public_token = public_token
        self.public_key = public_key

        # Automatic Fallback Logic: If sign/api_key is not provided, try using public_token/key
        self.sign = sign or os.getenv("THORDATA_SIGN") or self.public_token
        self.api_key = api_key or os.getenv("THORDATA_API_KEY") or self.public_key

        # Public API authentication
        self.sign = sign or os.getenv("THORDATA_SIGN")
        self.api_key = api_key or os.getenv("THORDATA_API_KEY")

        # Proxy configuration
        self._proxy_host = proxy_host
        self._proxy_port = proxy_port
        self._default_timeout = aiohttp.ClientTimeout(total=timeout)

        # Timeout configuration
        self._default_timeout = aiohttp.ClientTimeout(total=timeout)
        self._api_timeout = aiohttp.ClientTimeout(total=api_timeout)

        # Retry configuration
        self._retry_config = retry_config or RetryConfig()

        # Authentication mode
        self._auth_mode = auth_mode.lower()
        if self._auth_mode not in ("bearer", "header_token"):
            raise ThordataConfigError(
                f"Invalid auth_mode: {auth_mode}. Must be 'bearer' or 'header_token'."
            )

        # Pre-calculate proxy auth
        self._proxy_url = f"http://{proxy_host}:{proxy_port}"
        self._proxy_auth = aiohttp.BasicAuth(
            login=f"td-customer-{scraper_token}", password=""
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
            "THORDATA_PROXY_API_BASE_URL", "https://api.thordata.com/api"
        )
        self._proxy_list_url = f"{proxy_api_base}/proxy/proxy-list"
        self._proxy_expiration_url = f"{proxy_api_base}/proxy/expiration-time"
        self._list_url = f"{web_scraper_api_base}/tasks-list"

        # Session initialized lazily
        self._session: Optional[aiohttp.ClientSession] = None

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
        proxy_config: Optional[ProxyConfig] = None,
        **kwargs: Any,
    ) -> aiohttp.ClientResponse:
        """
        Send an async GET request through the Proxy Network.

        Args:
            url: The target URL.
            proxy_config: Custom proxy configuration.
            **kwargs: Additional aiohttp arguments.

        Returns:
            The aiohttp response object.
        """
        session = self._get_session()

        logger.debug(f"Async Proxy GET: {url}")

        if proxy_config:
            proxy_url, proxy_auth = proxy_config.to_aiohttp_config()
        else:
            proxy_url = self._proxy_url
            proxy_auth = self._proxy_auth

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
        proxy_config: Optional[ProxyConfig] = None,
        **kwargs: Any,
    ) -> aiohttp.ClientResponse:
        """
        Send an async POST request through the Proxy Network.

        Args:
            url: The target URL.
            proxy_config: Custom proxy configuration.
            **kwargs: Additional aiohttp arguments.

        Returns:
            The aiohttp response object.
        """
        session = self._get_session()

        logger.debug(f"Async Proxy POST: {url}")

        if proxy_config:
            proxy_url, proxy_auth = proxy_config.to_aiohttp_config()
        else:
            proxy_url = self._proxy_url
            proxy_auth = self._proxy_auth

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
        engine: Union[Engine, str] = Engine.GOOGLE,
        num: int = 10,
        country: Optional[str] = None,
        language: Optional[str] = None,
        search_type: Optional[str] = None,
        device: Optional[str] = None,
        render_js: Optional[bool] = None,
        no_cache: Optional[bool] = None,
        output_format: str = "json",
        **kwargs: Any,
    ) -> Dict[str, Any]:
        """
        Execute an async SERP search.

        Args:
            query: Search keywords.
            engine: Search engine.
            num: Number of results.
            country: Country code for localization.
            language: Language code.
            search_type: Type of search.
            device: Device type ('desktop', 'mobile', 'tablet').
            render_js: Enable JavaScript rendering in SERP.
            no_cache: Disable internal caching.
            output_format: 'json' or 'html'.
            **kwargs: Additional parameters.

        Returns:
            Parsed JSON results or dict with 'html' key.
        """
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
        headers = build_auth_headers(self.scraper_token, mode=self._auth_mode)

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

    async def serp_search_advanced(self, request: SerpRequest) -> Dict[str, Any]:
        """
        Execute an async SERP search using a SerpRequest object.
        """
        session = self._get_session()

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
        country: Optional[str] = None,
        block_resources: Optional[str] = None,
        wait: Optional[int] = None,
        wait_for: Optional[str] = None,
        **kwargs: Any,
    ) -> Union[str, bytes]:
        """
        Async scrape using Universal API (Web Unlocker).

        Args:
            url: Target URL.
            js_render: Enable JavaScript rendering.
            output_format: "html" or "png".
            country: Geo-targeting country.
            block_resources: Resources to block.
            wait: Wait time in ms.
            wait_for: CSS selector to wait for.

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
    ) -> Union[str, bytes]:
        """
        Async scrape using a UniversalScrapeRequest object.
        """
        session = self._get_session()

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
    # Web Scraper API Methods
    # =========================================================================

    async def create_scraper_task(
        self,
        file_name: str,
        spider_id: str,
        spider_name: str,
        parameters: Dict[str, Any],
        universal_params: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Create an async Web Scraper task.
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
        """
        Create a task using ScraperTaskConfig.
        """
        self._require_public_credentials()
        session = self._get_session()

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
                data = await response.json()

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
        parameters: Dict[str, Any],
        common_settings: CommonSettings,
    ) -> str:
        """
        Create a YouTube video/audio download task.
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
        """
        Create a video task using VideoTaskConfig object.
        """

        self._require_public_credentials()
        session = self._get_session()

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
        """
        Check async task status.

        Raises:
            ThordataConfigError: If public credentials are missing.
            ThordataAPIError: If API returns a non-200 code in JSON payload.
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
                data = await response.json()

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
        """
        Backward-compatible status check.

        Returns:
            Status string, or "error" on any exception.
        """
        try:
            return await self.get_task_status(task_id)
        except Exception:
            return "error"

    async def get_task_result(self, task_id: str, file_type: str = "json") -> str:
        """
        Get download URL for completed task.
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
                data = await response.json()
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
    ) -> Dict[str, Any]:
        """
        List all Web Scraper tasks.

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
        payload: Dict[str, Any] = {}
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
                data = await response.json()

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
        """
        Wait for a task to complete.
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

    # =========================================================================
    # Proxy Account Management Methods
    # =========================================================================

    async def get_usage_statistics(
        self,
        from_date: Union[str, date],
        to_date: Union[str, date],
    ) -> UsageStatistics:
        """
        Get account usage statistics for a date range.

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

    async def get_residential_balance(self) -> Dict[str, Any]:
        """
        Get residential proxy balance (Public API NEW).

        Requires sign and apiKey credentials.

        Returns:
            Dict with 'balance' (bytes) and 'expire_time' (timestamp).
        """
        if not self.sign or not self.api_key:
            raise ThordataConfigError(
                "sign and api_key are required for Public API NEW. "
                "Set THORDATA_SIGN and THORDATA_API_KEY environment variables."
            )

        session = self._get_session()
        headers = build_sign_headers(self.sign, self.api_key)

        logger.info("Async getting residential proxy balance (API NEW)")

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
        start_time: Union[str, int],
        end_time: Union[str, int],
    ) -> Dict[str, Any]:
        """
        Get residential proxy usage records (Public API NEW).

        Args:
            start_time: Start timestamp (Unix timestamp or YYYY-MM-DD HH:MM:SS).
            end_time: End timestamp (Unix timestamp or YYYY-MM-DD HH:MM:SS).

        Returns:
            Dict with usage data including 'all_flow', 'all_used_flow', 'data' list.
        """
        if not self.sign or not self.api_key:
            raise ThordataConfigError(
                "sign and api_key are required for Public API NEW."
            )

        session = self._get_session()
        headers = build_sign_headers(self.sign, self.api_key)
        payload = {
            "start_time": str(start_time),
            "end_time": str(end_time),
        }

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

    async def list_proxy_users(
        self, proxy_type: Union[ProxyType, int] = ProxyType.RESIDENTIAL
    ) -> ProxyUserList:
        """List all proxy users (sub-accounts)."""

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
        proxy_type: Union[ProxyType, int] = ProxyType.RESIDENTIAL,
        traffic_limit: int = 0,
        status: bool = True,
    ) -> Dict[str, Any]:
        """Create a new proxy user (sub-account)."""
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

    async def add_whitelist_ip(
        self,
        ip: str,
        proxy_type: Union[ProxyType, int] = ProxyType.RESIDENTIAL,
        status: bool = True,
    ) -> Dict[str, Any]:
        """
        Add an IP to the whitelist for IP authentication.
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

    async def list_proxy_servers(
        self,
        proxy_type: int,
    ) -> List[ProxyServer]:
        """
        List ISP or Datacenter proxy servers.
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

    async def get_isp_regions(self) -> List[Dict[str, Any]]:
        """
        Get available ISP proxy regions (Public API NEW).

        Returns:
            List of regions with id, continent, country, city, num, pricing.
        """
        if not self.sign or not self.api_key:
            raise ThordataConfigError(
                "sign and api_key are required for Public API NEW."
            )

        session = self._get_session()
        headers = build_sign_headers(self.sign, self.api_key)

        logger.info("Async getting ISP regions (API NEW)")

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

    async def list_isp_proxies(self) -> List[Dict[str, Any]]:
        """
        List ISP proxies (Public API NEW).

        Returns:
            List of ISP proxies with ip, port, user, pwd, startTime, expireTime.
        """
        if not self.sign or not self.api_key:
            raise ThordataConfigError(
                "sign and api_key are required for Public API NEW."
            )

        session = self._get_session()
        headers = build_sign_headers(self.sign, self.api_key)

        logger.info("Async listing ISP proxies (API NEW)")

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

    async def get_wallet_balance(self) -> Dict[str, Any]:
        """
        Get wallet balance for ISP proxies (Public API NEW).

        Returns:
            Dict with 'walletBalance'.
        """
        if not self.sign or not self.api_key:
            raise ThordataConfigError(
                "sign and api_key are required for Public API NEW."
            )

        session = self._get_session()
        headers = build_sign_headers(self.sign, self.api_key)

        logger.info("Async getting wallet balance (API NEW)")

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

    async def get_proxy_expiration(
        self,
        ips: Union[str, List[str]],
        proxy_type: int,
    ) -> Dict[str, Any]:
        """
        Get expiration time for specific proxy IPs.
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

    # =========================================================================
    # Location API Methods
    # =========================================================================

    async def list_countries(
        self, proxy_type: Union[ProxyType, int] = ProxyType.RESIDENTIAL
    ) -> List[Dict[str, Any]]:
        """List supported countries."""
        return await self._get_locations(
            "countries",
            proxy_type=(
                int(proxy_type) if isinstance(proxy_type, ProxyType) else proxy_type
            ),
        )

    async def list_states(
        self,
        country_code: str,
        proxy_type: Union[ProxyType, int] = ProxyType.RESIDENTIAL,
    ) -> List[Dict[str, Any]]:
        """List supported states for a country."""
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
        state_code: Optional[str] = None,
        proxy_type: Union[ProxyType, int] = ProxyType.RESIDENTIAL,
    ) -> List[Dict[str, Any]]:
        """List supported cities."""
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
        proxy_type: Union[ProxyType, int] = ProxyType.RESIDENTIAL,
    ) -> List[Dict[str, Any]]:
        """List supported ASNs."""
        return await self._get_locations(
            "asn",
            proxy_type=(
                int(proxy_type) if isinstance(proxy_type, ProxyType) else proxy_type
            ),
            country_code=country_code,
        )

    async def _get_locations(
        self, endpoint: str, **kwargs: Any
    ) -> List[Dict[str, Any]]:
        """Internal async locations API call."""
        self._require_public_credentials()

        params = {
            "token": self.public_token,
            "key": self.public_key,
        }

        for key, value in kwargs.items():
            params[key] = str(value)

        url = f"{self._locations_base_url}/{endpoint}"

        logger.debug(f"Async Locations API: {url}")

        # Create temporary session for this request (no proxy needed)
        async with aiohttp.ClientSession(trust_env=True) as temp_session:
            async with temp_session.get(url, params=params) as response:
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

    # =========================================================================
    # Helper Methods
    # =========================================================================

    def _require_public_credentials(self) -> None:
        """Ensure public API credentials are available."""
        if not self.public_token or not self.public_key:
            raise ThordataConfigError(
                "public_token and public_key are required for this operation. "
                "Please provide them when initializing AsyncThordataClient."
            )
