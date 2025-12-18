"""
Synchronous client for the Thordata API.

This module provides the main ThordataClient class for interacting with
Thordata's proxy network, SERP API, Universal Scraping API, and Web Scraper API.

Example:
    >>> from thordata import ThordataClient
    >>>
    >>> client = ThordataClient(
    ...     scraper_token="your_token",
    ...     public_token="your_public_token",
    ...     public_key="your_public_key"
    ... )
    >>>
    >>> # Use the proxy network
    >>> response = client.get("https://httpbin.org/ip")
    >>> print(response.json())
    >>>
    >>> # Search with SERP API
    >>> results = client.serp_search("python tutorial", engine="google")
"""

from __future__ import annotations

import logging
import os
from typing import Any, Dict, List, Optional, Union

import requests

from . import __version__ as _sdk_version
from ._utils import (
    build_auth_headers,
    build_public_api_headers,
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
    ProxyConfig,
    ProxyProduct,
    ScraperTaskConfig,
    SerpRequest,
    UniversalScrapeRequest,
)
from .retry import RetryConfig, with_retry

logger = logging.getLogger(__name__)


class ThordataClient:
    """
    The official synchronous Python client for Thordata.

    This client handles authentication and communication with:
    - Proxy Network (Residential/Datacenter/Mobile/ISP via HTTP/HTTPS)
    - SERP API (Real-time Search Engine Results)
    - Universal Scraping API (Web Unlocker - Single Page Rendering)
    - Web Scraper API (Async Task Management)

    Args:
        scraper_token: The API token from your Dashboard.
        public_token: The public API token (for task status, locations).
        public_key: The public API key.
        proxy_host: Custom proxy gateway host (optional).
        proxy_port: Custom proxy gateway port (optional).
        timeout: Default request timeout in seconds (default: 30).
        retry_config: Configuration for automatic retries (optional).

    Example:
        >>> client = ThordataClient(
        ...     scraper_token="your_scraper_token",
        ...     public_token="your_public_token",
        ...     public_key="your_public_key"
        ... )
    """

    # API Endpoints
    BASE_URL = "https://scraperapi.thordata.com"
    UNIVERSAL_URL = "https://universalapi.thordata.com"
    API_URL = "https://api.thordata.com/api/web-scraper-api"
    LOCATIONS_URL = "https://api.thordata.com/api/locations"

    def __init__(
        self,
        scraper_token: str,
        public_token: Optional[str] = None,
        public_key: Optional[str] = None,
        proxy_host: str = "pr.thordata.net",
        proxy_port: int = 9999,
        timeout: int = 30,
        retry_config: Optional[RetryConfig] = None,
        scraperapi_base_url: Optional[str] = None,
        universalapi_base_url: Optional[str] = None,
        web_scraper_api_base_url: Optional[str] = None,
        locations_base_url: Optional[str] = None,
    ) -> None:
        """Initialize the Thordata Client."""
        if not scraper_token:
            raise ThordataConfigError("scraper_token is required")

        self.scraper_token = scraper_token
        self.public_token = public_token
        self.public_key = public_key

        # Proxy configuration
        self._proxy_host = proxy_host
        self._proxy_port = proxy_port
        self._default_timeout = timeout

        # Retry configuration
        self._retry_config = retry_config or RetryConfig()

        # Build default proxy URL (for basic usage)
        self._default_proxy_url = (
            f"http://td-customer-{self.scraper_token}:@{proxy_host}:{proxy_port}"
        )

        # Sessions:
        # - _proxy_session: used for proxy network traffic to target sites
        # - _api_session: used for Thordata APIs (SERP/Universal/Tasks/Locations)
        #
        # We intentionally do NOT set session-level proxies for _api_session,
        # so developers can rely on system proxy settings (e.g., Clash) via env vars.
        self._proxy_session = requests.Session()
        self._proxy_session.trust_env = False
        self._proxy_session.proxies = {
            "http": self._default_proxy_url,
            "https": self._default_proxy_url,
        }

        self._api_session = requests.Session()
        self._api_session.trust_env = True

        self._api_session.headers.update(
            {"User-Agent": build_user_agent(_sdk_version, "requests")}
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

        self._serp_url = f"{scraperapi_base}/request"
        self._builder_url = f"{scraperapi_base}/builder"
        self._universal_url = f"{universalapi_base}/request"
        self._status_url = f"{web_scraper_api_base}/tasks-status"
        self._download_url = f"{web_scraper_api_base}/tasks-download"
        self._locations_base_url = locations_base

    # =========================================================================
    # Proxy Network Methods
    # =========================================================================

    def get(
        self,
        url: str,
        *,
        proxy_config: Optional[ProxyConfig] = None,
        timeout: Optional[int] = None,
        **kwargs: Any,
    ) -> requests.Response:
        """
        Send a GET request through the Thordata Proxy Network.

        Args:
            url: The target URL.
            proxy_config: Custom proxy configuration for geo-targeting/sessions.
            timeout: Request timeout in seconds.
            **kwargs: Additional arguments to pass to requests.get().

        Returns:
            The response object.

        Example:
            >>> # Basic request
            >>> response = client.get("https://httpbin.org/ip")
            >>>
            >>> # With geo-targeting
            >>> from thordata.models import ProxyConfig
            >>> config = ProxyConfig(
            ...     username="myuser",
            ...     password="mypass",
            ...     country="us",
            ...     city="seattle"
            ... )
            >>> response = client.get("https://httpbin.org/ip", proxy_config=config)
        """
        logger.debug(f"Proxy GET request: {url}")

        timeout = timeout or self._default_timeout

        if proxy_config:
            proxies = proxy_config.to_proxies_dict()
            kwargs["proxies"] = proxies

        return self._request_with_retry("GET", url, timeout=timeout, **kwargs)

    def post(
        self,
        url: str,
        *,
        proxy_config: Optional[ProxyConfig] = None,
        timeout: Optional[int] = None,
        **kwargs: Any,
    ) -> requests.Response:
        """
        Send a POST request through the Thordata Proxy Network.

        Args:
            url: The target URL.
            proxy_config: Custom proxy configuration.
            timeout: Request timeout in seconds.
            **kwargs: Additional arguments to pass to requests.post().

        Returns:
            The response object.
        """
        logger.debug(f"Proxy POST request: {url}")

        timeout = timeout or self._default_timeout

        if proxy_config:
            proxies = proxy_config.to_proxies_dict()
            kwargs["proxies"] = proxies

        return self._request_with_retry("POST", url, timeout=timeout, **kwargs)

    def build_proxy_url(
        self,
        *,
        country: Optional[str] = None,
        state: Optional[str] = None,
        city: Optional[str] = None,
        session_id: Optional[str] = None,
        session_duration: Optional[int] = None,
        product: Union[ProxyProduct, str] = ProxyProduct.RESIDENTIAL,
    ) -> str:
        """
        Build a proxy URL with custom targeting options.

        This is a convenience method for creating proxy URLs without
        manually constructing a ProxyConfig.

        Args:
            country: Target country code (e.g., 'us', 'gb').
            state: Target state (e.g., 'california').
            city: Target city (e.g., 'seattle').
            session_id: Session ID for sticky sessions.
            session_duration: Session duration in minutes (1-90).
            product: Proxy product type.

        Returns:
            The proxy URL string.

        Example:
            >>> url = client.build_proxy_url(country="us", city="seattle")
            >>> proxies = {"http": url, "https": url}
            >>> requests.get("https://example.com", proxies=proxies)
        """
        config = ProxyConfig(
            username=self.scraper_token,
            password="",
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
        Execute a real-time SERP (Search Engine Results Page) search.

        Args:
            query: The search keywords.
            engine: Search engine (google, bing, yandex, duckduckgo, baidu).
            num: Number of results to retrieve (default: 10).
            country: Country code for localized results (e.g., 'us').
            language: Language code for interface (e.g., 'en').
            search_type: Type of search (images, news, shopping, videos, etc.).
            device: Device type ('desktop', 'mobile', 'tablet').
            render_js: Enable JavaScript rendering in SERP (render_js=True).
            no_cache: Disable internal caching (no_cache=True).
            output_format: 'json' to return parsed JSON (default),
                           'html' to return HTML wrapped in {'html': ...}.
            **kwargs: Additional engine-specific parameters.

        Returns:
            Dict[str, Any]: Parsed JSON results or a dict with 'html' key.

        Example:
            >>> # Basic search
            >>> results = client.serp_search("python tutorial")
            >>>
            >>> # With options
            >>> results = client.serp_search(
            ...     "laptop reviews",
            ...     engine="google",
            ...     num=20,
            ...     country="us",
            ...     search_type="shopping",
            ...     device="mobile",
            ...     render_js=True,
            ...     no_cache=True,
            ... )
        """
        # Normalize engine
        engine_str = engine.value if isinstance(engine, Engine) else engine.lower()

        # Build request using model
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
        headers = build_auth_headers(self.scraper_token)

        logger.info(f"SERP Search: {engine_str} - {query}")

        try:
            response = self._api_session.post(
                self._serp_url,
                data=payload,
                headers=headers,
                timeout=60,
            )
            response.raise_for_status()

            # JSON mode (default)
            if output_format.lower() == "json":
                data = response.json()

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

            # HTML mode: wrap as dict to keep return type stable
            return {"html": response.text}

        except requests.Timeout as e:
            raise ThordataTimeoutError(
                f"SERP request timed out: {e}",
                original_error=e,
            ) from e
        except requests.RequestException as e:
            raise ThordataNetworkError(
                f"SERP request failed: {e}",
                original_error=e,
            ) from e

    def serp_search_advanced(self, request: SerpRequest) -> Dict[str, Any]:
        """
        Execute a SERP search using a SerpRequest object.

        This method provides full control over all search parameters.

        Args:
            request: A SerpRequest object with all parameters configured.

        Returns:
            Dict[str, Any]: Parsed JSON results or dict with 'html' key.

        Example:
            >>> from thordata.models import SerpRequest
            >>> request = SerpRequest(
            ...     query="python programming",
            ...     engine="google",
            ...     num=50,
            ...     country="us",
            ...     language="en",
            ...     search_type="news",
            ...     time_filter="week",
            ...     safe_search=True
            ... )
            >>> results = client.serp_search_advanced(request)
        """
        payload = request.to_payload()
        headers = build_auth_headers(self.scraper_token)

        logger.info(f"SERP Advanced Search: {request.engine} - {request.query}")

        try:
            response = self._api_session.post(
                self._serp_url,
                data=payload,
                headers=headers,
                timeout=60,
            )
            response.raise_for_status()

            if request.output_format.lower() == "json":
                data = response.json()

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

            return {"html": response.text}

        except requests.Timeout as e:
            raise ThordataTimeoutError(
                f"SERP request timed out: {e}",
                original_error=e,
            ) from e
        except requests.RequestException as e:
            raise ThordataNetworkError(
                f"SERP request failed: {e}",
                original_error=e,
            ) from e

    # =========================================================================
    # Universal Scraping API (Web Unlocker) Methods
    # =========================================================================

    def universal_scrape(
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
        Scrape a URL using the Universal Scraping API (Web Unlocker).

        Automatically bypasses Cloudflare, CAPTCHAs, and antibot systems.

        Args:
            url: Target URL.
            js_render: Enable JavaScript rendering (headless browser).
            output_format: "html" or "png" (screenshot).
            country: Geo-targeting country code.
            block_resources: Resources to block (e.g., 'script,image').
            wait: Wait time in milliseconds after page load.
            wait_for: CSS selector to wait for.
            **kwargs: Additional parameters.

        Returns:
            HTML string or PNG bytes depending on output_format.

        Example:
            >>> # Get HTML
            >>> html = client.universal_scrape("https://example.com", js_render=True)
            >>>
            >>> # Get screenshot
            >>> png = client.universal_scrape(
            ...     "https://example.com",
            ...     js_render=True,
            ...     output_format="png"
            ... )
            >>> with open("screenshot.png", "wb") as f:
            ...     f.write(png)
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

        return self.universal_scrape_advanced(request)

    def universal_scrape_advanced(
        self, request: UniversalScrapeRequest
    ) -> Union[str, bytes]:
        """
        Scrape using a UniversalScrapeRequest object for full control.

        Args:
            request: A UniversalScrapeRequest with all parameters.

        Returns:
            HTML string or PNG bytes.
        """
        payload = request.to_payload()
        headers = build_auth_headers(self.scraper_token)

        logger.info(
            f"Universal Scrape: {request.url} (format: {request.output_format})"
        )

        try:
            response = self._api_session.post(
                self._universal_url,
                data=payload,
                headers=headers,
                timeout=60,
            )
            response.raise_for_status()

            return self._process_universal_response(response, request.output_format)

        except requests.Timeout as e:
            raise ThordataTimeoutError(
                f"Universal scrape timed out: {e}", original_error=e
            ) from e
        except requests.RequestException as e:
            raise ThordataNetworkError(
                f"Universal scrape failed: {e}", original_error=e
            ) from e

    def _process_universal_response(
        self, response: requests.Response, output_format: str
    ) -> Union[str, bytes]:
        """Process the response from Universal API."""
        # Try to parse as JSON
        try:
            resp_json = response.json()
        except ValueError:
            # Raw content returned
            if output_format.lower() == "png":
                return response.content
            return response.text

        # Check for API-level errors
        if isinstance(resp_json, dict):
            code = resp_json.get("code")
            if code is not None and code != 200:
                msg = extract_error_message(resp_json)
                raise_for_code(
                    f"Universal API Error: {msg}", code=code, payload=resp_json
                )

        # Extract HTML
        if "html" in resp_json:
            return resp_json["html"]

        # Extract PNG
        if "png" in resp_json:
            return decode_base64_image(resp_json["png"])

        # Fallback
        return str(resp_json)

    # =========================================================================
    # Web Scraper API (Task-based) Methods
    # =========================================================================

    def create_scraper_task(
        self,
        file_name: str,
        spider_id: str,
        spider_name: str,
        parameters: Dict[str, Any],
        universal_params: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Create an asynchronous Web Scraper task.

        Note: Get spider_id and spider_name from the Thordata Dashboard.

        Args:
            file_name: Name for the output file.
            spider_id: Spider identifier from Dashboard.
            spider_name: Spider name (e.g., "youtube.com").
            parameters: Spider-specific parameters.
            universal_params: Global spider settings.

        Returns:
            The created task_id.

        Example:
            >>> task_id = client.create_scraper_task(
            ...     file_name="youtube_data",
            ...     spider_id="youtube_video-post_by-url",
            ...     spider_name="youtube.com",
            ...     parameters={"url": "https://youtube.com/@channel/videos"}
            ... )
        """
        config = ScraperTaskConfig(
            file_name=file_name,
            spider_id=spider_id,
            spider_name=spider_name,
            parameters=parameters,
            universal_params=universal_params,
        )

        return self.create_scraper_task_advanced(config)

    def create_scraper_task_advanced(self, config: ScraperTaskConfig) -> str:
        """
        Create a scraper task using a ScraperTaskConfig object.

        Args:
            config: Task configuration.

        Returns:
            The created task_id.
        """
        payload = config.to_payload()
        headers = build_auth_headers(self.scraper_token)

        logger.info(f"Creating Scraper Task: {config.spider_name}")

        try:
            response = self._api_session.post(
                self._builder_url,
                data=payload,
                headers=headers,
                timeout=30,
            )
            response.raise_for_status()

            data = response.json()
            code = data.get("code")

            if code != 200:
                msg = extract_error_message(data)
                raise_for_code(f"Task creation failed: {msg}", code=code, payload=data)

            return data["data"]["task_id"]

        except requests.RequestException as e:
            raise ThordataNetworkError(
                f"Task creation failed: {e}", original_error=e
            ) from e

    def get_task_status(self, task_id: str) -> str:
        """
        Check the status of an asynchronous scraping task.

        Returns:
            Status string (e.g., "running", "ready", "failed").

        Raises:
            ThordataConfigError: If public credentials are missing.
            ThordataAPIError: If API returns a non-200 code in JSON payload.
            ThordataNetworkError: If network/HTTP request fails.
        """
        self._require_public_credentials()

        headers = build_public_api_headers(
            self.public_token or "", self.public_key or ""
        )
        payload = {"tasks_ids": task_id}

        try:
            response = self._api_session.post(
                self._status_url,
                data=payload,
                headers=headers,
                timeout=30,
            )
            response.raise_for_status()
            data = response.json()

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

            # Unexpected payload type
            raise ThordataNetworkError(
                f"Unexpected task status response type: {type(data).__name__}",
                original_error=None,
            )

        except requests.Timeout as e:
            raise ThordataTimeoutError(
                f"Status check timed out: {e}", original_error=e
            ) from e
        except requests.RequestException as e:
            raise ThordataNetworkError(
                f"Status check failed: {e}", original_error=e
            ) from e

    def safe_get_task_status(self, task_id: str) -> str:
        """
        Backward-compatible status check.

        Returns:
            Status string, or "error" on any exception.
        """
        try:
            return self.get_task_status(task_id)
        except Exception:
            return "error"

    def get_task_result(self, task_id: str, file_type: str = "json") -> str:
        """
        Get the download URL for a completed task.
        """
        self._require_public_credentials()

        headers = build_public_api_headers(
            self.public_token or "", self.public_key or ""
        )
        payload = {"tasks_id": task_id, "type": file_type}

        logger.info(f"Getting result URL for Task: {task_id}")

        try:
            response = self._api_session.post(
                self._download_url,
                data=payload,
                headers=headers,
                timeout=30,
            )
            response.raise_for_status()

            data = response.json()
            code = data.get("code")

            if code == 200 and data.get("data"):
                return data["data"]["download"]

            msg = extract_error_message(data)
            raise_for_code(f"Get result failed: {msg}", code=code, payload=data)
            # This line won't be reached, but satisfies mypy
            raise RuntimeError("Unexpected state")

        except requests.RequestException as e:
            raise ThordataNetworkError(
                f"Get result failed: {e}", original_error=e
            ) from e

    def wait_for_task(
        self,
        task_id: str,
        *,
        poll_interval: float = 5.0,
        max_wait: float = 600.0,
    ) -> str:
        """
        Wait for a task to complete.

        Args:
            task_id: The task ID to wait for.
            poll_interval: Seconds between status checks.
            max_wait: Maximum seconds to wait.

        Returns:
            Final task status.

        Raises:
            TimeoutError: If max_wait is exceeded.

        Example:
            >>> task_id = client.create_scraper_task(...)
            >>> status = client.wait_for_task(task_id, max_wait=300)
            >>> if status in ("ready", "success"):
            ...     url = client.get_task_result(task_id)
        """
        import time

        start = time.monotonic()

        while (time.monotonic() - start) < max_wait:
            status = self.get_task_status(task_id)

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

            time.sleep(poll_interval)

        raise TimeoutError(f"Task {task_id} did not complete within {max_wait} seconds")

    # =========================================================================
    # Location API Methods
    # =========================================================================

    def list_countries(
        self, proxy_type: Union[ProxyType, int] = ProxyType.RESIDENTIAL
    ) -> List[Dict[str, Any]]:
        """
        List supported countries for proxies.

        Args:
            proxy_type: 1 for residential, 2 for unlimited.

        Returns:
            List of country records with 'country_code' and 'country_name'.
        """
        return self._get_locations(
            "countries",
            proxy_type=(
                int(proxy_type) if isinstance(proxy_type, ProxyType) else proxy_type
            ),
        )

    def list_states(
        self,
        country_code: str,
        proxy_type: Union[ProxyType, int] = ProxyType.RESIDENTIAL,
    ) -> List[Dict[str, Any]]:
        """
        List supported states for a country.

        Args:
            country_code: Country code (e.g., 'US').
            proxy_type: Proxy type.

        Returns:
            List of state records.
        """
        return self._get_locations(
            "states",
            proxy_type=(
                int(proxy_type) if isinstance(proxy_type, ProxyType) else proxy_type
            ),
            country_code=country_code,
        )

    def list_cities(
        self,
        country_code: str,
        state_code: Optional[str] = None,
        proxy_type: Union[ProxyType, int] = ProxyType.RESIDENTIAL,
    ) -> List[Dict[str, Any]]:
        """
        List supported cities for a country/state.

        Args:
            country_code: Country code.
            state_code: Optional state code.
            proxy_type: Proxy type.

        Returns:
            List of city records.
        """
        kwargs = {
            "proxy_type": (
                int(proxy_type) if isinstance(proxy_type, ProxyType) else proxy_type
            ),
            "country_code": country_code,
        }
        if state_code:
            kwargs["state_code"] = state_code

        return self._get_locations("cities", **kwargs)

    def list_asn(
        self,
        country_code: str,
        proxy_type: Union[ProxyType, int] = ProxyType.RESIDENTIAL,
    ) -> List[Dict[str, Any]]:
        """
        List supported ASNs for a country.

        Args:
            country_code: Country code.
            proxy_type: Proxy type.

        Returns:
            List of ASN records.
        """
        return self._get_locations(
            "asn",
            proxy_type=(
                int(proxy_type) if isinstance(proxy_type, ProxyType) else proxy_type
            ),
            country_code=country_code,
        )

    def _get_locations(self, endpoint: str, **kwargs: Any) -> List[Dict[str, Any]]:
        """Internal method to call locations API."""
        self._require_public_credentials()

        params = {
            "token": self.public_token,
            "key": self.public_key,
        }

        for key, value in kwargs.items():
            params[key] = str(value)

        url = f"{self._locations_base_url}/{endpoint}"

        logger.debug(f"Locations API request: {url}")

        # Use requests.get directly (no proxy needed for this API)
        response = self._api_session.get(url, params=params, timeout=30)
        response.raise_for_status()

        data = response.json()

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
                "Please provide them when initializing ThordataClient."
            )

    def _request_with_retry(
        self, method: str, url: str, **kwargs: Any
    ) -> requests.Response:
        """Make a request with automatic retry."""
        kwargs.setdefault("timeout", self._default_timeout)

        @with_retry(self._retry_config)
        def _do_request() -> requests.Response:
            return self._proxy_session.request(method, url, **kwargs)

        try:
            return _do_request()
        except requests.Timeout as e:
            raise ThordataTimeoutError(
                f"Request timed out: {e}", original_error=e
            ) from e
        except requests.RequestException as e:
            raise ThordataNetworkError(f"Request failed: {e}", original_error=e) from e

    def close(self) -> None:
        """Close the underlying session."""
        self._proxy_session.close()
        self._api_session.close()

    def __enter__(self) -> ThordataClient:
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.close()
