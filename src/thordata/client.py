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

import base64
import contextlib
import hashlib
import json
import logging
import os
import socket
import ssl
from datetime import date
from typing import Any, cast
from urllib.parse import quote, urlencode, urlparse

import requests
import urllib3
from requests.structures import CaseInsensitiveDict

from .serp_engines import SerpNamespace
from .unlimited import UnlimitedNamespace

try:
    import socks

    HAS_PYSOCKS = True
except ImportError:
    HAS_PYSOCKS = False

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
from .retry import RetryConfig, with_retry

logger = logging.getLogger(__name__)


# =========================================================================
# Upstream Proxy Support (for users behind firewall)
# =========================================================================


def _parse_upstream_proxy() -> dict[str, Any] | None:
    """
    Parse THORDATA_UPSTREAM_PROXY environment variable.

    Supported formats:
        - http://127.0.0.1:7897
        - socks5://127.0.0.1:7897
        - socks5://user:pass@127.0.0.1:7897

    Returns:
        Dict with proxy config or None if not set.
    """
    upstream_url = os.environ.get("THORDATA_UPSTREAM_PROXY", "").strip()
    if not upstream_url:
        return None

    parsed = urlparse(upstream_url)
    scheme = (parsed.scheme or "").lower()

    if scheme not in ("http", "https", "socks5", "socks5h", "socks4"):
        logger.warning(f"Unsupported upstream proxy scheme: {scheme}")
        return None

    return {
        "scheme": scheme,
        "host": parsed.hostname or "127.0.0.1",
        "port": parsed.port or (1080 if scheme.startswith("socks") else 7897),
        "username": parsed.username,
        "password": parsed.password,
    }


class _UpstreamProxySocketFactory:
    """
    Socket factory that creates connections through an upstream proxy.
    Used for proxy chaining when accessing Thordata from behind a firewall.
    """

    def __init__(self, upstream_config: dict[str, Any]):
        self.config = upstream_config

    def create_connection(
        self,
        address: tuple[str, int],
        timeout: float | None = None,
        source_address: tuple[str, int] | None = None,
    ) -> socket.socket:
        """Create a socket connection through the upstream proxy."""
        scheme = self.config["scheme"]

        if scheme.startswith("socks"):
            return self._create_socks_connection(address, timeout)
        else:
            return self._create_http_tunnel(address, timeout)

    def _create_socks_connection(
        self,
        address: tuple[str, int],
        timeout: float | None = None,
    ) -> socket.socket:
        """Create connection through SOCKS proxy."""
        if not HAS_PYSOCKS:
            raise RuntimeError(
                "PySocks is required for SOCKS upstream proxy. "
                "Install with: pip install PySocks"
            )

        scheme = self.config["scheme"]
        proxy_type = socks.SOCKS5 if "socks5" in scheme else socks.SOCKS4

        sock = socks.socksocket(socket.AF_INET, socket.SOCK_STREAM)
        sock.set_proxy(
            proxy_type,
            self.config["host"],
            self.config["port"],
            rdns=True,
            username=self.config.get("username"),
            password=self.config.get("password"),
        )

        if timeout is not None:
            sock.settimeout(timeout)

        sock.connect(address)
        return sock

    def _create_http_tunnel(
        self,
        address: tuple[str, int],
        timeout: float | None = None,
    ) -> socket.socket:
        """Create connection through HTTP CONNECT tunnel."""
        # Connect to upstream proxy
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        if timeout is not None:
            sock.settimeout(timeout)

        sock.connect((self.config["host"], self.config["port"]))

        # Build CONNECT request
        target_host, target_port = address
        connect_req = f"CONNECT {target_host}:{target_port} HTTP/1.1\r\n"
        connect_req += f"Host: {target_host}:{target_port}\r\n"

        # Add proxy auth if provided
        if self.config.get("username"):
            credentials = f"{self.config['username']}:{self.config.get('password', '')}"
            encoded = base64.b64encode(credentials.encode()).decode()
            connect_req += f"Proxy-Authorization: Basic {encoded}\r\n"

        connect_req += "\r\n"

        sock.sendall(connect_req.encode())

        # Read response
        response = b""
        while b"\r\n\r\n" not in response:
            chunk = sock.recv(1024)
            if not chunk:
                raise ConnectionError("Upstream proxy closed connection")
            response += chunk

        # Check status
        status_line = response.split(b"\r\n")[0].decode()
        if "200" not in status_line:
            sock.close()
            raise ConnectionError(f"Upstream proxy CONNECT failed: {status_line}")

        return sock


class _TLSInTLSSocket:
    """
    A socket-like wrapper for TLS-in-TLS connections.

    Uses SSLObject + MemoryBIO to implement TLS over an existing TLS connection.
    """

    def __init__(
        self,
        outer_sock: ssl.SSLSocket,
        ssl_obj: ssl.SSLObject,
        incoming: ssl.MemoryBIO,
        outgoing: ssl.MemoryBIO,
    ):
        self._outer = outer_sock
        self._ssl = ssl_obj
        self._incoming = incoming
        self._outgoing = outgoing
        self._timeout: float | None = None

    def settimeout(self, timeout: float | None) -> None:
        self._timeout = timeout
        self._outer.settimeout(timeout)

    def sendall(self, data: bytes) -> None:
        """Send data through the inner TLS connection."""
        self._ssl.write(data)
        encrypted = self._outgoing.read()
        if encrypted:
            self._outer.sendall(encrypted)

    def recv(self, bufsize: int) -> bytes:
        """Receive data from the inner TLS connection."""
        while True:
            try:
                return self._ssl.read(bufsize)
            except ssl.SSLWantReadError:
                self._outer.settimeout(self._timeout)
                try:
                    received = self._outer.recv(8192)
                    if not received:
                        return b""
                    self._incoming.write(received)
                except socket.timeout:
                    return b""

    def close(self) -> None:
        with contextlib.suppress(Exception):
            self._outer.close()


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
        """Initialize the Thordata Client.

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

        self._proxy_session = requests.Session()
        self._proxy_session.trust_env = False
        self._proxy_managers: dict[str, urllib3.PoolManager] = {}

        self._api_session = requests.Session()
        self._api_session.trust_env = True
        self._api_session.headers.update(
            {"User-Agent": build_user_agent(_sdk_version, "requests")}
        )

        # Base URLs
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
        self._gateway_base_url = gateway_base
        self._child_base_url = os.getenv(
            "THORDATA_CHILD_BASE_URL", "https://api.thordata.com/api/child"
        )

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

        # Initialize Namespaces AFTER all base URLs are set
        self.serp = SerpNamespace(self)
        self.unlimited = UnlimitedNamespace(self)

    # =========================================================================
    # Context Manager
    # =========================================================================

    def close(self) -> None:
        """Close the client and release resources."""
        self._proxy_session.close()
        self._api_session.close()
        for pm in self._proxy_managers.values():
            pm.clear()
        self._proxy_managers.clear()

    def __enter__(self) -> ThordataClient:
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.close()

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
        """Make a GET request through the proxy network.

        Args:
            url: Target URL to request.
            proxy_config: Proxy configuration. If not provided, uses environment variables.
            timeout: Request timeout in seconds.
            **kwargs: Additional arguments passed to requests.

        Returns:
            Response object.
        """
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
        """Make a POST request through the proxy network.

        Args:
            url: Target URL to request.
            proxy_config: Proxy configuration. If not provided, uses environment variables.
            timeout: Request timeout in seconds.
            **kwargs: Additional arguments passed to requests.

        Returns:
            Response object.
        """
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
        """Build a proxy URL with location and session parameters.

        Args:
            username: Proxy username.
            password: Proxy password.
            country: Country code (e.g., "us", "uk").
            state: State/region code (e.g., "ca", "ny").
            city: City name (e.g., "new-york", "london").
            session_id: Session identifier for sticky sessions.
            session_duration: Session duration in minutes (1-90).
            product: Proxy product type (RESIDENTIAL, DATACENTER, MOBILE).

        Returns:
            Formatted proxy URL.
        """
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
        """Perform a search engine query using SERP API.

        Args:
            query: Search query string.
            engine: Search engine (GOOGLE, BING, YAHOO, etc.).
            num: Number of results to return.
            country: Country code for localized results.
            language: Language code for interface.
            search_type: Type of search (images, news, video, etc.).
            device: Device type (desktop, mobile).
            render_js: Whether to render JavaScript.
            no_cache: Bypass cache.
            output_format: Output format ("json" or "html").
            **kwargs: Additional engine-specific parameters.

        Returns:
            Search results as dictionary.
        """
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
        """Perform advanced search with a SerpRequest object.

        Args:
            request: SerpRequest object with search parameters.

        Returns:
            Search results as dictionary.
        """
        if not self.scraper_token:
            raise ThordataConfigError("scraper_token is required for SERP API")

        payload = request.to_payload()
        headers = build_auth_headers(self.scraper_token, mode=self._auth_mode)

        logger.info(f"SERP Advanced Search: {request.engine} - {request.query[:50]}")

        try:
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

        except requests.Timeout as e:
            raise ThordataTimeoutError(f"SERP timeout: {e}", original_error=e) from e
        except requests.RequestException as e:
            raise ThordataNetworkError(f"SERP failed: {e}", original_error=e) from e

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
        """Scrape a URL using Universal Scraping API.

        Args:
            url: Target URL to scrape.
            js_render: Whether to render JavaScript.
            output_format: Output format ("html" or "png").
            country: Country for IP geolocation.
            block_resources: Block specific resources (e.g., "script,css").
            wait: Wait time in milliseconds before fetching.
            wait_for: CSS selector to wait for before fetching.
            **kwargs: Additional parameters.

        Returns:
            Scraped content as string (HTML) or bytes (PNG).
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

    def universal_scrape_advanced(self, request: UniversalScrapeRequest) -> str | bytes:
        """Scrape with advanced options using UniversalScrapeRequest.

        Args:
            request: UniversalScrapeRequest object with scrape parameters.

        Returns:
            Scraped content as string (HTML) or bytes (PNG).
        """
        if not self.scraper_token:
            raise ThordataConfigError("scraper_token is required for Universal API")

        payload = request.to_payload()
        headers = build_auth_headers(self.scraper_token, mode=self._auth_mode)

        logger.info(f"Universal Scrape: {request.url}")

        try:
            response = self._api_request_with_retry(
                "POST",
                self._universal_url,
                data=payload,
                headers=headers,
            )
            response.raise_for_status()
            return self._process_universal_response(response, request.output_format)

        except requests.Timeout as e:
            raise ThordataTimeoutError(
                f"Universal timeout: {e}", original_error=e
            ) from e
        except requests.RequestException as e:
            raise ThordataNetworkError(
                f"Universal failed: {e}", original_error=e
            ) from e

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
        """Create a web scraping task.

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
        return self.create_scraper_task_advanced(config)

    def create_scraper_task_advanced(self, config: ScraperTaskConfig) -> str:
        """Create a web scraping task with advanced configuration.

        Args:
            config: ScraperTaskConfig object with task configuration.

        Returns:
            Task ID.
        """
        self._require_public_credentials()
        if not self.scraper_token:
            raise ThordataConfigError("scraper_token is required for Task Builder")
        payload = config.to_payload()
        headers = build_builder_headers(
            self.scraper_token, self.public_token or "", self.public_key or ""
        )

        try:
            response = self._api_request_with_retry(
                "POST", self._builder_url, data=payload, headers=headers
            )
            response.raise_for_status()
            data = response.json()
            if data.get("code") != 200:
                raise_for_code(
                    "Task creation failed", code=data.get("code"), payload=data
                )
            return data["data"]["task_id"]
        except requests.RequestException as e:
            raise ThordataNetworkError(
                f"Task creation failed: {e}", original_error=e
            ) from e

    def create_video_task(
        self,
        file_name: str,
        spider_id: str,
        spider_name: str,
        parameters: dict[str, Any],
        common_settings: CommonSettings,
    ) -> str:
        """Create a video/audio download task (YouTube, etc.).

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
        return self.create_video_task_advanced(config)

    def create_video_task_advanced(self, config: VideoTaskConfig) -> str:
        """Create a video task with advanced configuration.

        Args:
            config: VideoTaskConfig object with task configuration.

        Returns:
            Task ID.
        """
        self._require_public_credentials()
        if not self.scraper_token:
            raise ThordataConfigError(
                "scraper_token is required for Video Task Builder"
            )

        payload = config.to_payload()
        headers = build_builder_headers(
            self.scraper_token, self.public_token or "", self.public_key or ""
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
        """Get the status of a scraping task.

        Args:
            task_id: Task identifier.

        Returns:
            Status string (running, success, failed, etc.).
        """
        self._require_public_credentials()
        headers = build_public_api_headers(
            self.public_token or "", self.public_key or ""
        )
        try:
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
        except requests.RequestException as e:
            raise ThordataNetworkError(
                f"Status check failed: {e}", original_error=e
            ) from e

    def safe_get_task_status(self, task_id: str) -> str:
        """Get task status with error handling.

        Args:
            task_id: Task identifier.

        Returns:
            Status string or "error" on failure.
        """
        try:
            return self.get_task_status(task_id)
        except Exception:
            return "error"

    def get_task_result(self, task_id: str, file_type: str = "json") -> str:
        """Get the download URL for a completed task.

        Args:
            task_id: Task identifier.
            file_type: File type to download (json, csv, video, audio, subtitle).

        Returns:
            Download URL.
        """
        self._require_public_credentials()
        headers = build_public_api_headers(
            self.public_token or "", self.public_key or ""
        )
        try:
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
        except requests.RequestException as e:
            raise ThordataNetworkError(
                f"Get result failed: {e}", original_error=e
            ) from e

    def list_tasks(self, page: int = 1, size: int = 20) -> dict[str, Any]:
        """List all scraping tasks.

        Args:
            page: Page number for pagination.
            size: Number of items per page.

        Returns:
            Dictionary with count and list of tasks.
        """
        self._require_public_credentials()
        headers = build_public_api_headers(
            self.public_token or "", self.public_key or ""
        )
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
        # New parameters
        task_type: str = "web",  # "web" or "video"
        common_settings: CommonSettings | None = None,
    ) -> str:
        """High-level wrapper to run a task and wait for result.

        This method handles the entire lifecycle:
        1. Create Task
        2. Poll status (with exponential backoff)
        3. Get download URL when ready

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
            The download URL for the task result.

        Raises:
            ThordataTimeoutError: If task takes longer than max_wait.
            ThordataAPIError: If task fails or is cancelled.
        """
        import time

        # 1. Create Task
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

        logger.info(f"Task created successfully: {task_id}. Waiting for completion...")

        # 2. Poll Status (Smart Backoff)
        start_time = time.monotonic()
        current_poll = initial_poll_interval

        while (time.monotonic() - start_time) < max_wait:
            status = self.get_task_status(task_id)
            status_lower = status.lower()

            if status_lower in {"ready", "success", "finished"}:
                logger.info(f"Task {task_id} finished. Status: {status}")
                # 3. Get Result
                return self.get_task_result(task_id)

            if status_lower in {"failed", "error", "cancelled"}:
                raise ThordataNetworkError(
                    f"Task {task_id} ended with failed status: {status}"
                )

            # Wait and increase interval (capped)
            time.sleep(current_poll)
            current_poll = min(current_poll * 1.5, max_poll_interval)

        raise ThordataTimeoutError(f"Task {task_id} timed out after {max_wait} seconds")

    # =========================================================================
    # Account & Usage Methods
    # =========================================================================

    def get_usage_statistics(
        self,
        from_date: str | date,
        to_date: str | date,
    ) -> UsageStatistics:
        """Get usage statistics for a date range.

        Args:
            from_date: Start date (YYYY-MM-DD format or date object).
            to_date: End date (YYYY-MM-DD format or date object).

        Returns:
            UsageStatistics object with traffic data.
        """
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
        """
        Get the current traffic balance in KB via Public API.
        """
        self._require_public_credentials()
        # FIX: Auth params must be in Query, NOT Headers
        params = {
            "token": self.public_token,
            "key": self.public_key,
        }
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
        """
        Get the current wallet balance via Public API.
        """
        self._require_public_credentials()
        # FIX: Auth params must be in Query, NOT Headers
        params = {
            "token": self.public_token,
            "key": self.public_key,
        }
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
        """
        Get traffic usage statistics for a specific proxy user.

        Args:
            username: Sub-account username.
            start_date: Start date (YYYY-MM-DD).
            end_date: End date (YYYY-MM-DD).
            proxy_type: Proxy product type.

        Returns:
            List of daily usage records.
        """
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

        # Structure: { "data": [ { "date": "...", "usage_traffic": ... } ] }
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
        product: str = "residential",  # residential or unlimited
    ) -> list[str]:
        """
        Extract proxy IP list via API (get-ip.thordata.net).
        Requires IP whitelist configuration.

        Args:
            num: Number of IPs to extract.
            country: Country code.
            state: State code.
            city: City name.
            time_limit: Session duration (1-90 mins).
            port: Specific port.
            return_type: "txt" or "json".
            protocol: "http" or "socks5".
            sep: Separator for txt output.
            product: "residential" or "unlimited".

        Returns:
            List of "IP:Port" strings.
        """
        # Determine endpoint based on product
        base_url = "https://get-ip.thordata.net"
        endpoint = "/unlimited_api" if product == "unlimited" else "/api"

        # Build params
        params: dict[str, Any] = {
            "num": str(num),
            "return_type": return_type,
            "protocol": protocol,
            "sep": sep,
        }

        # Add optional params
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

        response = self._api_session.get(
            f"{base_url}{endpoint}", params=params, timeout=self._default_timeout
        )
        response.raise_for_status()

        # Parse result
        if return_type == "json":
            data = response.json()
            # JSON format: { "code": 0, "data": [ { "ip": "...", "port": ... } ] }
            if isinstance(data, dict):
                if data.get("code") == 0 or data.get("code") == 200:
                    raw_list = data.get("data") or []
                    return [f"{item['ip']}:{item['port']}" for item in raw_list]
                else:
                    raise_for_code(
                        "Extract IPs failed", code=data.get("code"), payload=data
                    )
            return []

        else:  # txt
            text = response.text.strip()
            # Check for error message in text (often starts with { or contains "error")
            if text.startswith("{") and "code" in text:
                # Try parsing as JSON error
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
            return [line.strip() for line in text.split(actual_sep) if line.strip()]

    # =========================================================================
    # Proxy Users Management (Sub-accounts)
    # =========================================================================

    def list_proxy_users(
        self, proxy_type: ProxyType | int = ProxyType.RESIDENTIAL
    ) -> ProxyUserList:
        """List all proxy sub-accounts.

        Args:
            proxy_type: Proxy product type.

        Returns:
            ProxyUserList with user information.
        """
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
        """Create a new proxy sub-account.

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
        pt = int(proxy_type) if isinstance(proxy_type, ProxyType) else proxy_type
        headers = build_public_api_headers(
            self.public_token or "", self.public_key or ""
        )
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
        password: str,  # Added password as required argument
        traffic_limit: int | None = None,
        status: bool | None = None,
        proxy_type: ProxyType | int = ProxyType.RESIDENTIAL,
    ) -> dict[str, Any]:
        """
        Update an existing proxy user's settings.

        Note: Password is required by the API even if not changing it.

        Args:
            username: The sub-account username.
            password: The sub-account password (required for update).
            traffic_limit: New traffic limit in MB (0 for unlimited). None to keep unchanged.
            status: New status (True=enabled, False=disabled). None to keep unchanged.
            proxy_type: Proxy product type.

        Returns:
            API response data.
        """
        self._require_public_credentials()
        pt = int(proxy_type) if isinstance(proxy_type, ProxyType) else proxy_type
        headers = build_public_api_headers(
            self.public_token or "", self.public_key or ""
        )

        payload = {
            "proxy_type": str(pt),
            "username": username,
            "password": password,  # Include password
        }
        if traffic_limit is not None:
            payload["traffic_limit"] = str(traffic_limit)
        if status is not None:
            payload["status"] = "true" if status else "false"

        response = self._api_request_with_retry(
            "POST",
            f"{self._proxy_users_url}/update-user",
            data=payload,
            headers=headers,
        )
        response.raise_for_status()
        data = response.json()
        if data.get("code") != 200:
            raise_for_code("Update user failed", code=data.get("code"), payload=data)
        return data.get("data", {})

    def delete_proxy_user(
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
        pt = int(proxy_type) if isinstance(proxy_type, ProxyType) else proxy_type
        headers = build_public_api_headers(
            self.public_token or "", self.public_key or ""
        )

        payload = {
            "proxy_type": str(pt),
            "username": username,
        }

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
        """Add an IP to the whitelist.

        Args:
            ip: IP address to whitelist.
            proxy_type: Proxy product type.
            status: Enable or disable the whitelist entry.

        Returns:
            API response data.
        """
        self._require_public_credentials()
        pt = int(proxy_type) if isinstance(proxy_type, ProxyType) else proxy_type
        headers = build_public_api_headers(
            self.public_token or "", self.public_key or ""
        )
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
        """Delete an IP from the whitelist.

        Args:
            ip: The IP address to remove.
            proxy_type: Proxy product type.

        Returns:
            API response data.
        """
        self._require_public_credentials()
        pt = int(proxy_type) if isinstance(proxy_type, ProxyType) else proxy_type
        headers = build_public_api_headers(
            self.public_token or "", self.public_key or ""
        )
        payload = {
            "proxy_type": str(pt),
            "ip": ip,
        }
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
        """List all whitelisted IPs.

        Args:
            proxy_type: Proxy product type.

        Returns:
            List of IP address strings.
        """
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

        # API usually returns {"data": ["1.1.1.1", ...]} OR {"data": [{"ip": "..."}]}
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

    def list_countries(
        self, proxy_type: ProxyType | int = ProxyType.RESIDENTIAL
    ) -> list[dict[str, Any]]:
        """List available countries for proxy locations.

        Args:
            proxy_type: Proxy product type.

        Returns:
            List of country dictionaries.
        """
        pt = int(proxy_type) if isinstance(proxy_type, ProxyType) else proxy_type
        return self._get_locations("countries", proxy_type=pt)

    def list_states(
        self,
        country_code: str,
        proxy_type: ProxyType | int = ProxyType.RESIDENTIAL,
    ) -> list[dict[str, Any]]:
        """List available states/provinces for a country.

        Args:
            country_code: Country code (e.g., "US", "GB").
            proxy_type: Proxy product type.

        Returns:
            List of state dictionaries.
        """
        pt = int(proxy_type) if isinstance(proxy_type, ProxyType) else proxy_type
        return self._get_locations("states", proxy_type=pt, country_code=country_code)

    def list_cities(
        self,
        country_code: str,
        state_code: str | None = None,
        proxy_type: ProxyType | int = ProxyType.RESIDENTIAL,
    ) -> list[dict[str, Any]]:
        """List available cities for a country/state.

        Args:
            country_code: Country code.
            state_code: State code (optional).
            proxy_type: Proxy product type.

        Returns:
            List of city dictionaries.
        """
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
        """List available ASN numbers for a country.

        Args:
            country_code: Country code.
            proxy_type: Proxy product type.

        Returns:
            List of ASN dictionaries.
        """
        pt = int(proxy_type) if isinstance(proxy_type, ProxyType) else proxy_type
        return self._get_locations("asn", proxy_type=pt, country_code=country_code)

    # =========================================================================
    # ISP & Datacenter Proxy Management
    # =========================================================================

    def list_proxy_servers(self, proxy_type: int) -> list[ProxyServer]:
        """List purchased proxy servers (ISP/Datacenter).

        Args:
            proxy_type: Proxy type (1=ISP, 2=Datacenter).

        Returns:
            List of ProxyServer objects.
        """
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
        """Get expiration time for proxy IPs.

        Args:
            ips: Single IP or comma-separated list of IPs.
            proxy_type: Proxy type (1=ISP, 2=Datacenter).

        Returns:
            Dictionary with IP expiration times.
        """
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
    # Internal Request Helpers
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
        """Make an API request with retry logic.

        Args:
            method: HTTP method.
            url: Request URL.
            data: Request body data.
            headers: Request headers.
            query_params: Query string parameters.

        Returns:
            Response object.
        """

        @with_retry(self._retry_config)
        def _do_request() -> requests.Response:
            return self._api_session.request(
                method,
                url,
                data=data,
                headers=headers,
                params=params,
                timeout=self._api_timeout,
            )

        try:
            return _do_request()
        except requests.Timeout as e:
            raise ThordataTimeoutError(
                f"API request timed out: {e}", original_error=e
            ) from e
        except requests.RequestException as e:
            raise ThordataNetworkError(
                f"API request failed: {e}", original_error=e
            ) from e

    def _require_public_credentials(self) -> None:
        """Check that public credentials are set."""
        if not self.public_token or not self.public_key:
            raise ThordataConfigError(
                "public_token and public_key are required for this operation."
            )

    def _get_locations(self, endpoint: str, **kwargs: Any) -> list[dict[str, Any]]:
        """Internal method to fetch location data.

        Args:
            endpoint: Location endpoint (countries, states, cities, asn).
            **kwargs: Query parameters.

        Returns:
            List of location dictionaries.
        """
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

    def _process_universal_response(
        self, response: requests.Response, output_format: str
    ) -> str | bytes:
        """Process Universal API response.

        Args:
            response: Response object.
            output_format: Expected output format.

        Returns:
            Processed content.
        """
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

    # =========================================================================
    # Proxy Implementation Details
    # =========================================================================

    def _proxy_verb(
        self,
        method: str,
        url: str,
        proxy_config: ProxyConfig | None,
        timeout: int | None,
        **kwargs: Any,
    ) -> requests.Response:
        """Internal method for proxy requests."""
        timeout = timeout or self._default_timeout

        if proxy_config is None:
            proxy_config = self._get_default_proxy_config_from_env()

        if proxy_config is None:
            raise ThordataConfigError(
                "Proxy credentials are missing. "
                "Pass proxy_config or set THORDATA_RESIDENTIAL_USERNAME/PASSWORD env vars."
            )

        kwargs.pop("proxies", None)

        @with_retry(self._retry_config)
        def _do() -> requests.Response:
            return self._proxy_request_with_proxy_manager(
                method,
                url,
                proxy_config=proxy_config,
                timeout=timeout,
                headers=kwargs.pop("headers", None),
                params=kwargs.pop("params", None),
                data=kwargs.pop("data", None),
            )

        try:
            return _do()
        except requests.Timeout as e:
            raise ThordataTimeoutError(
                f"Request timed out: {e}", original_error=e
            ) from e
        except Exception as e:
            raise ThordataNetworkError(f"Request failed: {e}", original_error=e) from e

    def _proxy_manager_key(self, proxy_endpoint: str, userpass: str | None) -> str:
        """Build a stable cache key for ProxyManager instances."""
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
        """Get or create a ProxyManager for the given proxy URL (Pooled)."""
        cached = self._proxy_managers.get(cache_key)
        if cached is not None:
            return cached

        if proxy_url.startswith(("socks5://", "socks5h://", "socks4://", "socks4a://")):
            try:
                from urllib3.contrib.socks import SOCKSProxyManager
            except Exception as e:
                raise ThordataConfigError(
                    "SOCKS proxy requested but SOCKS dependencies are missing. "
                    "Install: pip install 'urllib3[socks]' or pip install PySocks"
                ) from e

            pm_socks = SOCKSProxyManager(
                proxy_url,
                num_pools=10,
                maxsize=10,
            )
            pm = cast(urllib3.PoolManager, pm_socks)
            self._proxy_managers[cache_key] = pm
            return pm

        # HTTP/HTTPS proxies
        proxy_ssl_context = None
        if proxy_url.startswith("https://"):
            proxy_ssl_context = ssl.create_default_context()

        pm_http = urllib3.ProxyManager(
            proxy_url,
            proxy_headers=proxy_headers,
            proxy_ssl_context=proxy_ssl_context,
            num_pools=10,
            maxsize=10,
        )

        pm = cast(urllib3.PoolManager, pm_http)
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
        """Execute request through proxy, with optional upstream proxy support."""

        # Check for upstream proxy
        upstream_config = _parse_upstream_proxy()

        if upstream_config:
            return self._proxy_request_with_upstream(
                method,
                url,
                proxy_config=proxy_config,
                timeout=timeout,
                headers=headers,
                params=params,
                data=data,
                upstream_config=upstream_config,
            )

        # Original implementation (no upstream proxy)
        req = requests.Request(method=method.upper(), url=url, params=params)
        prepped = self._proxy_session.prepare_request(req)
        final_url = prepped.url or url

        proxy_endpoint = proxy_config.build_proxy_endpoint()
        is_socks = proxy_endpoint.startswith(
            ("socks5://", "socks5h://", "socks4://", "socks4a://")
        )

        if is_socks:
            proxy_url_for_manager = proxy_config.build_proxy_url()
            userpass = proxy_config.build_proxy_basic_auth()
            cache_key = self._proxy_manager_key(proxy_endpoint, userpass)

            pm = self._get_proxy_manager(
                proxy_url_for_manager,
                cache_key=cache_key,
                proxy_headers=None,
            )
        else:
            userpass = proxy_config.build_proxy_basic_auth()
            proxy_headers = urllib3.make_headers(proxy_basic_auth=userpass)
            cache_key = self._proxy_manager_key(proxy_endpoint, userpass)

            pm = self._get_proxy_manager(
                proxy_endpoint,
                cache_key=cache_key,
                proxy_headers=dict(proxy_headers),
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
        r.status_code = int(getattr(http_resp, "status", 0) or 0)
        r._content = http_resp.data or b""
        r.url = final_url
        r.headers = CaseInsensitiveDict(dict(http_resp.headers or {}))
        return r

    # =========================================================================
    # Upstream Proxy Support (Proxy Chaining)
    # =========================================================================

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
        """Execute request through proxy chain: Upstream -> Thordata -> Target."""
        if not HAS_PYSOCKS:
            raise ThordataConfigError(
                "PySocks is required for upstream proxy support. "
                "Install with: pip install PySocks"
            )

        req = requests.Request(method=method.upper(), url=url, params=params)
        prepped = self._proxy_session.prepare_request(req)
        final_url = prepped.url or url

        parsed_target = urlparse(final_url)
        target_host = parsed_target.hostname or ""
        target_port = parsed_target.port or (
            443 if parsed_target.scheme == "https" else 80
        )
        target_is_https = parsed_target.scheme == "https"

        protocol = proxy_config.protocol.lower()
        if protocol == "socks5":
            protocol = "socks5h"

        thordata_host = proxy_config.host or ""
        thordata_port = proxy_config.port or 9999
        thordata_username = proxy_config.build_username()
        thordata_password = proxy_config.password

        socket_factory = _UpstreamProxySocketFactory(upstream_config)

        logger.debug(
            f"Proxy chain: upstream({upstream_config['host']}:{upstream_config['port']}) "
            f"-> thordata({protocol}://{thordata_host}:{thordata_port}) "
            f"-> target({target_host}:{target_port})"
        )

        raw_sock = socket_factory.create_connection(
            (thordata_host, thordata_port),
            timeout=float(timeout),
        )

        try:
            if protocol.startswith("socks"):
                sock = self._socks5_handshake(
                    raw_sock,
                    target_host,
                    target_port,
                    thordata_username,
                    thordata_password,
                )
                if target_is_https:
                    context = ssl.create_default_context()
                    sock = context.wrap_socket(sock, server_hostname=target_host)

            elif protocol == "https":
                proxy_context = ssl.create_default_context()
                proxy_ssl_sock = proxy_context.wrap_socket(
                    raw_sock, server_hostname=thordata_host
                )

                self._send_connect_request(
                    proxy_ssl_sock,
                    target_host,
                    target_port,
                    thordata_username,
                    thordata_password,
                )

                if target_is_https:
                    # FIX: Add type ignore for MyPy because _TLSInTLSSocket is duck-typed as socket
                    sock = self._create_tls_in_tls_socket(
                        proxy_ssl_sock, target_host, timeout
                    )  # type: ignore[assignment]
                else:
                    sock = proxy_ssl_sock

            else:  # HTTP proxy
                self._send_connect_request(
                    raw_sock,
                    target_host,
                    target_port,
                    thordata_username,
                    thordata_password,
                )

                if target_is_https:
                    context = ssl.create_default_context()
                    sock = context.wrap_socket(raw_sock, server_hostname=target_host)
                else:
                    sock = raw_sock

            return self._send_http_request(
                sock, method, parsed_target, headers, data, final_url, timeout
            )

        finally:
            with contextlib.suppress(Exception):
                raw_sock.close()

    def _send_connect_request(
        self,
        sock: socket.socket,
        target_host: str,
        target_port: int,
        proxy_username: str,
        proxy_password: str,
    ) -> None:
        """Send HTTP CONNECT request to proxy and verify response."""
        connect_req = f"CONNECT {target_host}:{target_port} HTTP/1.1\r\n"
        connect_req += f"Host: {target_host}:{target_port}\r\n"

        credentials = f"{proxy_username}:{proxy_password}"
        encoded = base64.b64encode(credentials.encode()).decode()
        connect_req += f"Proxy-Authorization: Basic {encoded}\r\n"
        connect_req += "\r\n"

        sock.sendall(connect_req.encode())

        response = b""
        while b"\r\n\r\n" not in response:
            chunk = sock.recv(4096)
            if not chunk:
                raise ConnectionError("Proxy closed connection during CONNECT")
            response += chunk

        status_line = response.split(b"\r\n")[0].decode()
        if "200" not in status_line:
            raise ConnectionError(f"Proxy CONNECT failed: {status_line}")

    def _create_tls_in_tls_socket(
        self,
        outer_ssl_sock: ssl.SSLSocket,
        hostname: str,
        timeout: int,
    ) -> _TLSInTLSSocket:
        """Create a TLS connection over an existing TLS connection."""
        context = ssl.create_default_context()

        incoming = ssl.MemoryBIO()
        outgoing = ssl.MemoryBIO()

        ssl_obj = context.wrap_bio(incoming, outgoing, server_hostname=hostname)

        while True:
            try:
                ssl_obj.do_handshake()
                break
            except ssl.SSLWantReadError:
                data_to_send = outgoing.read()
                if data_to_send:
                    outer_ssl_sock.sendall(data_to_send)

                outer_ssl_sock.settimeout(float(timeout))
                try:
                    received = outer_ssl_sock.recv(8192)
                    if not received:
                        raise ConnectionError("Connection closed during TLS handshake")
                    incoming.write(received)
                except socket.timeout as e:
                    raise ConnectionError("Timeout during TLS handshake") from e
            except ssl.SSLWantWriteError:
                data_to_send = outgoing.read()
                if data_to_send:
                    outer_ssl_sock.sendall(data_to_send)

        data_to_send = outgoing.read()
        if data_to_send:
            outer_ssl_sock.sendall(data_to_send)

        return _TLSInTLSSocket(outer_ssl_sock, ssl_obj, incoming, outgoing)

    def _send_http_request(
        self,
        sock: socket.socket | ssl.SSLSocket | Any,
        method: str,
        parsed_url: Any,
        headers: dict[str, str] | None,
        data: Any,
        final_url: str,
        timeout: int,
    ) -> requests.Response:
        """Send HTTP request over established connection and parse response."""
        target_host = parsed_url.hostname

        req_headers = dict(headers or {})
        req_headers.setdefault("Host", target_host)
        req_headers.setdefault("User-Agent", build_user_agent(_sdk_version, "requests"))
        req_headers.setdefault("Connection", "close")

        path = parsed_url.path or "/"
        if parsed_url.query:
            path += f"?{parsed_url.query}"

        http_req = f"{method.upper()} {path} HTTP/1.1\r\n"
        for k, v in req_headers.items():
            http_req += f"{k}: {v}\r\n"

        body = None
        if data is not None:
            if isinstance(data, dict):
                body = urlencode({k: str(v) for k, v in data.items()}).encode()
                http_req += "Content-Type: application/x-www-form-urlencoded\r\n"
                http_req += f"Content-Length: {len(body)}\r\n"
            elif isinstance(data, bytes):
                body = data
                http_req += f"Content-Length: {len(body)}\r\n"
            else:
                body = str(data).encode()
                http_req += f"Content-Length: {len(body)}\r\n"

        http_req += "\r\n"
        sock.sendall(http_req.encode())

        if body:
            sock.sendall(body)

        if hasattr(sock, "settimeout"):
            sock.settimeout(float(timeout))

        response_data = b""
        try:
            while True:
                chunk = sock.recv(8192)
                if not chunk:
                    break
                response_data += chunk
                if b"\r\n\r\n" in response_data:
                    header_end = response_data.index(b"\r\n\r\n") + 4
                    headers_part = (
                        response_data[:header_end]
                        .decode("utf-8", errors="replace")
                        .lower()
                    )
                    if "content-length:" in headers_part:
                        for line in headers_part.split("\r\n"):
                            if line.startswith("content-length:"):
                                content_length = int(line.split(":")[1].strip())
                                if len(response_data) >= header_end + content_length:
                                    break
                    elif "transfer-encoding: chunked" not in headers_part:
                        break
        except socket.timeout:
            pass

        return self._parse_http_response(response_data, final_url)

    def _socks5_handshake(
        self,
        sock: socket.socket,
        target_host: str,
        target_port: int,
        username: str | None,
        password: str | None,
    ) -> socket.socket:
        """Perform SOCKS5 handshake over existing socket."""
        if username and password:
            sock.sendall(b"\x05\x02\x00\x02")
        else:
            sock.sendall(b"\x05\x01\x00")

        response = sock.recv(2)
        if len(response) < 2:
            raise ConnectionError("SOCKS5 handshake failed: incomplete response")

        if response[0] != 0x05:
            raise ConnectionError(f"SOCKS5 version mismatch: {response[0]}")

        auth_method = response[1]

        if auth_method == 0x02:
            if not username or not password:
                raise ConnectionError(
                    "SOCKS5 server requires auth but no credentials provided"
                )

            auth_req = bytes([0x01, len(username)]) + username.encode()
            auth_req += bytes([len(password)]) + password.encode()
            sock.sendall(auth_req)

            auth_resp = sock.recv(2)
            if len(auth_resp) < 2 or auth_resp[1] != 0x00:
                raise ConnectionError("SOCKS5 authentication failed")

        elif auth_method == 0xFF:
            raise ConnectionError("SOCKS5 no acceptable auth method")

        connect_req = b"\x05\x01\x00\x03"
        connect_req += bytes([len(target_host)]) + target_host.encode()
        connect_req += target_port.to_bytes(2, "big")
        sock.sendall(connect_req)

        resp = sock.recv(4)
        if len(resp) < 4:
            raise ConnectionError("SOCKS5 connect failed: incomplete response")

        if resp[1] != 0x00:
            error_codes = {
                0x01: "General failure",
                0x02: "Connection not allowed",
                0x03: "Network unreachable",
                0x04: "Host unreachable",
                0x05: "Connection refused",
                0x06: "TTL expired",
                0x07: "Command not supported",
                0x08: "Address type not supported",
            }
            error_msg = error_codes.get(resp[1], f"Unknown error {resp[1]}")
            raise ConnectionError(f"SOCKS5 connect failed: {error_msg}")

        addr_type = resp[3]
        if addr_type == 0x01:
            sock.recv(4 + 2)
        elif addr_type == 0x03:
            domain_len = sock.recv(1)[0]
            sock.recv(domain_len + 2)
        elif addr_type == 0x04:
            sock.recv(16 + 2)

        return sock

    def _parse_http_response(
        self,
        response_data: bytes,
        url: str,
    ) -> requests.Response:
        """Parse raw HTTP response into requests.Response."""
        if b"\r\n\r\n" in response_data:
            header_data, body = response_data.split(b"\r\n\r\n", 1)
        else:
            header_data = response_data
            body = b""

        header_lines = header_data.decode("utf-8", errors="replace").split("\r\n")

        status_line = header_lines[0] if header_lines else ""
        parts = status_line.split(" ", 2)
        status_code = int(parts[1]) if len(parts) > 1 else 0

        headers_dict = {}
        for line in header_lines[1:]:
            if ": " in line:
                k, v = line.split(": ", 1)
                headers_dict[k] = v

        if headers_dict.get("Transfer-Encoding", "").lower() == "chunked":
            body = self._decode_chunked(body)

        r = requests.Response()
        r.status_code = status_code
        r._content = body
        r.url = url
        r.headers = CaseInsensitiveDict(headers_dict)
        return r

    def _decode_chunked(self, data: bytes) -> bytes:
        """Decode chunked transfer encoding."""
        result = b""
        while data:
            if b"\r\n" not in data:
                break
            size_line, data = data.split(b"\r\n", 1)
            try:
                chunk_size = int(size_line.decode().strip(), 16)
            except ValueError:
                break

            if chunk_size == 0:
                break

            result += data[:chunk_size]
            data = data[chunk_size:]

            if data.startswith(b"\r\n"):
                data = data[2:]

        return result

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
            or "https"
        )
        port = int(port_raw) if port_raw and port_raw.isdigit() else None
        return host or None, port, protocol

    def _get_default_proxy_config_from_env(self) -> ProxyConfig | None:
        """Get proxy configuration from environment variables."""
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
        """
        Generate the WebSocket URL for connecting to Scraping Browser.

        Args:
            username: Proxy username (without 'td-customer-' prefix).
                      Defaults to THORDATA_BROWSER_USERNAME or THORDATA_RESIDENTIAL_USERNAME.
            password: Proxy password.

        Returns:
            WSS URL string suitable for playwright.connect_over_cdp().

        Raises:
            ThordataConfigError: If credentials are missing.
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
        final_user = f"{prefix}{user}" if not user.startswith(prefix) else user

        # URL encode
        safe_user = quote(final_user, safe="")
        safe_pass = quote(pwd, safe="")

        return f"wss://{safe_user}:{safe_pass}@ws-browser.thordata.com"
