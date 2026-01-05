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
import ssl
from datetime import date
from typing import Any, Dict, List, Optional, Union
from urllib.parse import urlencode

import requests
import urllib3

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
    WhitelistProxyConfig,
)
from .retry import RetryConfig, with_retry

logger = logging.getLogger(__name__)


class ThordataClient:
    # API Endpoints
    BASE_URL = "https://scraperapi.thordata.com"
    UNIVERSAL_URL = "https://universalapi.thordata.com"
    API_URL = "https://openapi.thordata.com/api/web-scraper-api"
    LOCATIONS_URL = "https://openapi.thordata.com/api/locations"

    def __init__(
        self,
        scraper_token: str,
        public_token: Optional[str] = None,
        public_key: Optional[str] = None,
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
        """Initialize the Thordata Client."""
        if not scraper_token:
            raise ThordataConfigError("scraper_token is required")

        # Core credentials
        self.scraper_token = scraper_token
        self.public_token = public_token
        self.public_key = public_key

        # Proxy configuration
        self._proxy_host = proxy_host
        self._proxy_port = proxy_port

        # Timeout configuration
        self._default_timeout = timeout
        self._api_timeout = api_timeout

        # Retry configuration
        self._retry_config = retry_config or RetryConfig()

        # Authentication mode (for scraping APIs)
        self._auth_mode = auth_mode.lower()
        if self._auth_mode not in ("bearer", "header_token"):
            raise ThordataConfigError(
                f"Invalid auth_mode: {auth_mode}. Must be 'bearer' or 'header_token'."
            )

        # HTTP Sessions
        self._proxy_session = requests.Session()
        self._proxy_session.trust_env = False

        # Cache for ProxyManagers (Connection Pooling Fix)
        # Key: proxy_url (str), Value: urllib3.ProxyManager
        self._proxy_managers: Dict[str, urllib3.ProxyManager] = {}

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
            "THORDATA_PROXY_API_BASE_URL", "https://api.thordata.com/api"
        )
        self._proxy_list_url = f"{proxy_api_base}/proxy/proxy-list"
        self._proxy_expiration_url = f"{proxy_api_base}/proxy/expiration-time"

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
        logger.debug(f"Proxy GET request: {url}")
        return self._proxy_verb("GET", url, proxy_config, timeout, **kwargs)

    def post(
        self,
        url: str,
        *,
        proxy_config: Optional[ProxyConfig] = None,
        timeout: Optional[int] = None,
        **kwargs: Any,
    ) -> requests.Response:
        logger.debug(f"Proxy POST request: {url}")
        return self._proxy_verb("POST", url, proxy_config, timeout, **kwargs)

    def _proxy_verb(
        self,
        method: str,
        url: str,
        proxy_config: Optional[ProxyConfig],
        timeout: Optional[int],
        **kwargs: Any,
    ) -> requests.Response:
        timeout = timeout or self._default_timeout

        if proxy_config is None:
            proxy_config = self._get_default_proxy_config_from_env()

        if proxy_config is None:
            raise ThordataConfigError(
                "Proxy credentials are missing. "
                "Pass proxy_config or set THORDATA_RESIDENTIAL_USERNAME/PASSWORD env vars."
            )

        # For requests/urllib3, we don't need 'proxies' dict in kwargs
        # because we use ProxyManager directly.
        # But we remove it if user accidentally passed it to avoid confusion.
        kwargs.pop("proxies", None)

        @with_retry(self._retry_config)
        def _do() -> requests.Response:
            return self._proxy_request_with_proxy_manager(
                method,
                url,
                proxy_config=proxy_config,  # type: ignore
                timeout=timeout,  # type: ignore
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

    def build_proxy_url(
        self,
        username: str,
        password: str,
        *,
        country: Optional[str] = None,
        state: Optional[str] = None,
        city: Optional[str] = None,
        session_id: Optional[str] = None,
        session_duration: Optional[int] = None,
        product: Union[ProxyProduct, str] = ProxyProduct.RESIDENTIAL,
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
    # Internal Request Helpers
    # =========================================================================
    def _api_request_with_retry(
        self,
        method: str,
        url: str,
        *,
        data: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        params: Optional[Dict[str, Any]] = None,
    ) -> requests.Response:
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

    def _get_proxy_manager(self, proxy_url: str) -> urllib3.ProxyManager:
        """Get or create a ProxyManager for the given proxy URL (Pooled)."""
        if proxy_url not in self._proxy_managers:
            # Create a new manager if not cached
            proxy_ssl_context = None
            if proxy_url.startswith("https://"):
                proxy_ssl_context = ssl.create_default_context()

            self._proxy_managers[proxy_url] = urllib3.ProxyManager(
                proxy_url,
                proxy_ssl_context=proxy_ssl_context,
                num_pools=10,  # Allow concurrency
                maxsize=10,
            )
        return self._proxy_managers[proxy_url]

    def _proxy_request_with_proxy_manager(
        self,
        method: str,
        url: str,
        *,
        proxy_config: ProxyConfig,
        timeout: int,
        headers: Optional[Dict[str, str]] = None,
        params: Optional[Dict[str, Any]] = None,
        data: Any = None,
    ) -> requests.Response:
        # 1. Prepare URL and Body
        req = requests.Request(method=method.upper(), url=url, params=params)
        prepped = self._proxy_session.prepare_request(req)
        final_url = prepped.url or url

        # 2. Get Proxy Configuration
        proxy_url = proxy_config.build_proxy_endpoint()
        proxy_headers = urllib3.make_headers(
            proxy_basic_auth=proxy_config.build_proxy_basic_auth()
        )

        # 3. Get Cached Proxy Manager
        pm = self._get_proxy_manager(proxy_url)

        # 4. Prepare Request Headers/Body
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

        # 5. Execute Request via urllib3
        http_resp = pm.request(
            method.upper(),
            final_url,
            body=body,
            headers=req_headers or None,
            proxy_headers=proxy_headers,  # Attach Auth here
            timeout=urllib3.Timeout(connect=timeout, read=timeout),
            retries=False,  # We handle retries in _proxy_verb
            preload_content=True,
        )

        # 6. Convert back to requests.Response
        r = requests.Response()
        r.status_code = int(getattr(http_resp, "status", 0) or 0)
        r._content = http_resp.data or b""
        r.url = final_url
        r.headers = requests.structures.CaseInsensitiveDict(
            dict(http_resp.headers or {})
        )
        return r

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

    def serp_search_advanced(self, request: SerpRequest) -> Dict[str, Any]:
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
    # Universal Scraping API
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

    def _process_universal_response(
        self, response: requests.Response, output_format: str
    ) -> Union[str, bytes]:
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
    # Web Scraper API (Tasks)
    # =========================================================================
    def create_scraper_task(
        self,
        file_name: str,
        spider_id: str,
        spider_name: str,
        parameters: Dict[str, Any],
        universal_params: Optional[Dict[str, Any]] = None,
    ) -> str:
        config = ScraperTaskConfig(
            file_name=file_name,
            spider_id=spider_id,
            spider_name=spider_name,
            parameters=parameters,
            universal_params=universal_params,
        )
        return self.create_scraper_task_advanced(config)

    def create_scraper_task_advanced(self, config: ScraperTaskConfig) -> str:
        self._require_public_credentials()
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
        parameters: Dict[str, Any],
        common_settings: "CommonSettings",
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
        try:
            return self.get_task_status(task_id)
        except Exception:
            return "error"

    def get_task_result(self, task_id: str, file_type: str = "json") -> str:
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

    def list_tasks(self, page: int = 1, size: int = 20) -> Dict[str, Any]:
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

    # =========================================================================
    # Account / Locations / Utils
    # =========================================================================
    def get_usage_statistics(
        self,
        from_date: Union[str, date],
        to_date: Union[str, date],
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

    def list_proxy_users(
        self, proxy_type: Union[ProxyType, int] = ProxyType.RESIDENTIAL
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
        proxy_type: Union[ProxyType, int] = ProxyType.RESIDENTIAL,
        traffic_limit: int = 0,
        status: bool = True,
    ) -> Dict[str, Any]:
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

    def add_whitelist_ip(
        self,
        ip: str,
        proxy_type: Union[ProxyType, int] = ProxyType.RESIDENTIAL,
        status: bool = True,
    ) -> Dict[str, Any]:
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

    def list_proxy_servers(self, proxy_type: int) -> List[ProxyServer]:
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
        self, ips: Union[str, List[str]], proxy_type: int
    ) -> Dict[str, Any]:
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

    def list_countries(
        self, proxy_type: Union[ProxyType, int] = ProxyType.RESIDENTIAL
    ) -> List[Dict[str, Any]]:
        pt = int(proxy_type) if isinstance(proxy_type, ProxyType) else proxy_type
        return self._get_locations("countries", proxy_type=pt)

    def list_states(
        self,
        country_code: str,
        proxy_type: Union[ProxyType, int] = ProxyType.RESIDENTIAL,
    ) -> List[Dict[str, Any]]:
        pt = int(proxy_type) if isinstance(proxy_type, ProxyType) else proxy_type
        return self._get_locations("states", proxy_type=pt, country_code=country_code)

    def list_cities(
        self,
        country_code: str,
        state_code: Optional[str] = None,
        proxy_type: Union[ProxyType, int] = ProxyType.RESIDENTIAL,
    ) -> List[Dict[str, Any]]:
        pt = int(proxy_type) if isinstance(proxy_type, ProxyType) else proxy_type
        kwargs = {"proxy_type": pt, "country_code": country_code}
        if state_code:
            kwargs["state_code"] = state_code
        return self._get_locations("cities", **kwargs)

    def list_asn(
        self,
        country_code: str,
        proxy_type: Union[ProxyType, int] = ProxyType.RESIDENTIAL,
    ) -> List[Dict[str, Any]]:
        pt = int(proxy_type) if isinstance(proxy_type, ProxyType) else proxy_type
        return self._get_locations("asn", proxy_type=pt, country_code=country_code)

    def _get_locations(self, endpoint: str, **kwargs: Any) -> List[Dict[str, Any]]:
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

    def _require_public_credentials(self) -> None:
        if not self.public_token or not self.public_key:
            raise ThordataConfigError(
                "public_token and public_key are required for this operation."
            )

    def _get_proxy_endpoint_overrides(
        self, product: ProxyProduct
    ) -> tuple[Optional[str], Optional[int], str]:
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

    def _get_default_proxy_config_from_env(self) -> Optional[ProxyConfig]:
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

    def close(self) -> None:
        self._proxy_session.close()
        self._api_session.close()
        # Clean up connection pools
        for pm in self._proxy_managers.values():
            pm.clear()
        self._proxy_managers.clear()

    def __enter__(self) -> ThordataClient:
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.close()
