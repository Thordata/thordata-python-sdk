import aiohttp
import logging
import json
import base64
from typing import Optional, Dict, Any, Union

# Import shared logic
from .enums import Engine
from .parameters import normalize_serp_params
from .exceptions import (
    ThordataAPIError,
    ThordataAuthError,
    ThordataRateLimitError,
)

logger = logging.getLogger(__name__)


class AsyncThordataClient:
    """
    The official Asynchronous Python client for Thordata (built on aiohttp).
    Designed for high-concurrency AI agents and data pipelines.
    """

    def __init__(
        self,
        scraper_token: str,
        public_token: str,
        public_key: str,
        proxy_host: str = "gate.thordata.com",
        proxy_port: int = 22225
    ):
        """
        Initialize the Async Client.
        """
        self.scraper_token = scraper_token
        self.public_token = public_token
        self.public_key = public_key

        # Pre-calculate proxy auth for performance
        self.proxy_auth = aiohttp.BasicAuth(login=scraper_token, password='')
        self.proxy_url = f"http://{proxy_host}:{proxy_port}"

        # API Endpoints
        self.base_url = "https://scraperapi.thordata.com"
        self.universal_url = "https://universalapi.thordata.com"
        self.api_url = "https://api.thordata.com/api/web-scraper-api"

        self.SERP_API_URL = f"{self.base_url}/request"
        self.UNIVERSAL_API_URL = f"{self.universal_url}/request"
        self.SCRAPER_BUILDER_URL = f"{self.base_url}/builder"
        self.SCRAPER_STATUS_URL = f"{self.api_url}/tasks-status"
        self.SCRAPER_DOWNLOAD_URL = f"{self.api_url}/tasks-download"

        # Session is initialized lazily or via context manager
        self._session: Optional[aiohttp.ClientSession] = None

    async def __aenter__(self):
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession(trust_env=True)
        return self

    async def __aexit__(self, exc_type, exc, tb):
        await self.close()

    async def close(self):
        """Close the underlying aiohttp session."""
        if self._session and not self._session.closed:
            await self._session.close()
            self._session = None

    def _get_session(self) -> aiohttp.ClientSession:
        """Internal helper to ensure session exists."""
        if self._session is None or self._session.closed:
            raise RuntimeError(
                "Client session not initialized. Use 'async with AsyncThordataClient(...) as client:'"
            )
        return self._session

    async def get(self, url: str, **kwargs) -> aiohttp.ClientResponse:
        """
        Send an async GET request through the Proxy Network.
        """
        session = self._get_session()
        try:
            logger.debug(f"Async Proxy Request: {url}")
            return await session.get(
                url,
                proxy=self.proxy_url,
                proxy_auth=self.proxy_auth,
                **kwargs
            )
        except aiohttp.ClientError as e:
            logger.error(f"Async Request failed: {e}")
            raise

    async def serp_search(
        self, 
        query: str, 
        engine: Union[Engine, str] = Engine.GOOGLE, 
        num: int = 10, 
        **kwargs
    ) -> Dict[str, Any]:
        """
        Execute a real-time SERP search (Async).
        """
        session = self._get_session()

        # 1. Handle Enum conversion
        engine_str = engine.value if isinstance(engine, Engine) else engine.lower()

        # 2. Normalize parameters
        payload = normalize_serp_params(engine_str, query, num=num, **kwargs)

        headers = {
            "Authorization": f"Bearer {self.scraper_token}",
            "Content-Type": "application/x-www-form-urlencoded"
        }

        # 3. Execute Request
        logger.info(f"Async SERP Search: {engine_str} - {query}")
        async with session.post(
            self.SERP_API_URL, data=payload, headers=headers
        ) as response:
            response.raise_for_status()
            
            data = await response.json()
            # Handle double-encoded JSON strings if they occur
            if isinstance(data, str):
                try:
                    data = json.loads(data)
                except json.JSONDecodeError:
                    pass
            return data

    async def universal_scrape(
        self,
        url: str,
        js_render: bool = False,
        output_format: str = "HTML",
        country: Optional[str] = None,
        block_resources: bool = False
    ) -> Union[str, bytes]:
        """
        Async Universal Scraping (Bypass Cloudflare/CAPTCHA).
        """
        session = self._get_session()

        headers = {
            "Authorization": f"Bearer {self.scraper_token}",
            "Content-Type": "application/x-www-form-urlencoded"
        }

        payload = {
            "url": url,
            "js_render": "True" if js_render else "False",
            "type": output_format.lower(),
            "block_resources": "True" if block_resources else "False"
        }
        if country:
            payload["country"] = country

        logger.info(f"Async Universal Scrape: {url}")
        async with session.post(
            self.UNIVERSAL_API_URL, data=payload, headers=headers
        ) as response:
            response.raise_for_status()

            try:
                resp_json = await response.json()
            except json.JSONDecodeError:
                # Fallback for raw content
                if output_format.upper() == "PNG":
                    return await response.read()
                return await response.text()

            # Check API error codes
            if isinstance(resp_json, dict):
                code = resp_json.get("code")
                if code is not None and code != 200:
                    msg = f"Universal API Error: {resp_json}"
                    if code in (401, 403):
                        raise ThordataAuthError(msg, code=code, payload=resp_json)
                    if code in (402, 429):
                        raise ThordataRateLimitError(msg, code=code, payload=resp_json)
                    raise ThordataAPIError(msg, code=code, payload=resp_json)

            if "html" in resp_json:
                return resp_json["html"]

            if "png" in resp_json:
                png_str = resp_json["png"]
                if not png_str:
                    raise Exception("API returned empty PNG data")

                # Clean Data URI Scheme
                if "," in png_str:
                    png_str = png_str.split(",", 1)[1]

                # Fix Base64 Padding
                png_str = png_str.replace("\n", "").replace("\r", "")
                missing_padding = len(png_str) % 4
                if missing_padding:
                    png_str += '=' * (4 - missing_padding)
                
                return base64.b64decode(png_str)

            return str(resp_json)

    async def create_scraper_task(
        self,
        file_name: str,
        spider_id: str,
        spider_name: str,
        individual_params: Dict[str, Any],
        universal_params: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Create an Asynchronous Web Scraper Task.
        """
        session = self._get_session()

        headers = {
            "Authorization": f"Bearer {self.scraper_token}",
            "Content-Type": "application/x-www-form-urlencoded"
        }

        payload = {
            "file_name": file_name,
            "spider_id": spider_id,
            "spider_name": spider_name,
            "spider_parameters": json.dumps([individual_params]),
            "spider_errors": "true"
        }
        if universal_params:
            payload["spider_universal"] = json.dumps(universal_params)

        logger.info(f"Async Task Creation: {spider_name}")
        async with session.post(
            self.SCRAPER_BUILDER_URL, data=payload, headers=headers
        ) as response:
            response.raise_for_status()
            data = await response.json()
            code = data.get("code")

            if code != 200:
                msg = f"Creation failed: {data}"
                if code in (401, 403):
                    raise ThordataAuthError(msg, code=code, payload=data)
                if code in (402, 429):
                    # 402: balance/permissions; 429: rate limited
                    raise ThordataRateLimitError(msg, code=code, payload=data)
                raise ThordataAPIError(msg, code=code, payload=data)

            return data["data"]["task_id"]

    async def get_task_status(self, task_id: str) -> str:
        """
        Check task status.
        """
        session = self._get_session()

        headers = {
            "token": self.public_token,
            "key": self.public_key,
            "Content-Type": "application/x-www-form-urlencoded"
        }
        payload = {"tasks_ids": task_id}

        async with session.post(
            self.SCRAPER_STATUS_URL, data=payload, headers=headers
        ) as response:
            data = await response.json()
            if data.get("code") == 200 and data.get("data"):
                for item in data["data"]:
                    if str(item.get("task_id")) == str(task_id):
                        return item["status"]
            return "Unknown"

    async def get_task_result(self, task_id: str, file_type: str = "json") -> str:
        """
        Get the download URL for a finished task.
        """
        session = self._get_session()
        
        headers = {
            "token": self.public_token,
            "key": self.public_key,
            "Content-Type": "application/x-www-form-urlencoded"
        }
        # Fixed: Use the file_type argument instead of hardcoding "json"
        payload = {"tasks_id": task_id, "type": file_type}

        async with session.post(
            self.SCRAPER_DOWNLOAD_URL, data=payload, headers=headers
        ) as response:
            data = await response.json()
            code = data.get("code")

            if code == 200 and data.get("data"):
                return data["data"]["download"]

            msg = f"Result Error: {data}"
            if code in (401, 403):
                raise ThordataAuthError(msg, code=code, payload=data)
            if code in (402, 429):
                raise ThordataRateLimitError(msg, code=code, payload=data)
            raise ThordataAPIError(msg, code=code, payload=data)