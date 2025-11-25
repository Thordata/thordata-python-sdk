import aiohttp
import logging
import json
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)


class AsyncThordataClient:
    """
    Thordata Asynchronous Client (built on aiohttp).
    Designed for high-concurrency and low-latency data collection tasks.

    Usage:
        async with AsyncThordataClient(...) as client:
            await client.get("http://example.com")
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
        Initialize the asynchronous client.
        """
        self.scraper_token = scraper_token
        self.public_token = public_token
        self.public_key = public_key

        # Proxy Authentication
        self.proxy_auth = aiohttp.BasicAuth(login=scraper_token, password='')
        self.proxy_url = f"http://{proxy_host}:{proxy_port}"

        # API Endpoints
        self.base_url = "https://scraperapi.thordata.com"
        self.api_url = "https://api.thordata.com/api/web-scraper-api"

        self.SERP_API_URL = f"{self.base_url}/request"
        self.SCRAPER_BUILDER_URL = f"{self.base_url}/builder"
        self.SCRAPER_STATUS_URL = f"{self.api_url}/tasks-status"
        self.SCRAPER_DOWNLOAD_URL = f"{self.api_url}/tasks-download"

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

    # --- Proxy Usage ---

    async def get(self, url: str, **kwargs) -> aiohttp.ClientResponse:
        """
        Send an asynchronous GET request through the Thordata Proxy.
        """
        if self._session is None:
            raise RuntimeError("Client session not initialized.")

        logger.debug(f"Async Proxy Request: {url}")
        try:
            return await self._session.get(
                url,
                proxy=self.proxy_url,
                proxy_auth=self.proxy_auth,
                **kwargs
            )
        except aiohttp.ClientError as e:
            logger.error(f"Async Request failed: {e}")
            raise

    # --- SERP API ---

    async def serp_search(
        self, query: str, engine: str = "google", num: int = 10, **kwargs
    ) -> Dict[str, Any]:
        """Async SERP search."""
        if self._session is None:
            raise RuntimeError("Client session not initialized.")

        payload = {
            "q": query,
            "num": str(num),
            "json": "1",
            "engine": engine.lower(),
            **kwargs
        }
        if engine.lower() == 'yandex':
            payload['text'] = payload.pop('q')
            if 'url' not in payload:
                payload['url'] = "yandex.com"
        elif 'url' not in payload:
            if engine == 'google':
                payload['url'] = "google.com"
            elif engine == 'bing':
                payload['url'] = "bing.com"

        headers = {
            "Authorization": f"Bearer {self.scraper_token}",
            "Content-Type": "application/x-www-form-urlencoded"
        }

        async with self._session.post(
            self.SERP_API_URL, data=payload, headers=headers
        ) as response:
            response.raise_for_status()
            data = await response.json()
            # Handle double-encoding
            if isinstance(data, str):
                try:
                    data = json.loads(data)
                except Exception:
                    pass
            return data

    # --- Web Scraper API ---

    async def create_scraper_task(
        self,
        file_name: str,
        spider_id: str,
        individual_params: Dict[str, Any],
        spider_name: str = "youtube.com",
        universal_params: Dict[str, Any] = None
    ) -> str:
        """Create an async scraping task."""
        if self._session is None:
            raise RuntimeError("Client session not initialized.")

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

        async with self._session.post(
            self.SCRAPER_BUILDER_URL, data=payload, headers=headers
        ) as response:
            response.raise_for_status()
            data = await response.json()
            if data.get("code") != 200:
                raise Exception(f"Creation failed: {data}")
            return data["data"]["task_id"]

    async def get_task_status(self, task_id: str) -> str:
        """Check task status."""
        headers = {
            "token": self.public_token,
            "key": self.public_key,
            "Content-Type": "application/x-www-form-urlencoded"
        }
        payload = {"tasks_ids": task_id}

        async with self._session.post(
            self.SCRAPER_STATUS_URL, data=payload, headers=headers
        ) as response:
            data = await response.json()
            if data.get("code") == 200 and data.get("data"):
                for item in data["data"]:
                    if str(item["task_id"]) == str(task_id):
                        return item["status"]
            return "Unknown"

    async def get_task_result(self, task_id: str, file_type: str = "json") -> str:
        """Get download link."""
        headers = {
            "token": self.public_token,
            "key": self.public_key,
            "Content-Type": "application/x-www-form-urlencoded"
        }
        payload = {"tasks_id": task_id, "type": "json"}

        async with self._session.post(
            self.SCRAPER_DOWNLOAD_URL, data=payload, headers=headers
        ) as response:
            data = await response.json()
            if data.get("code") == 200:
                return data["data"]["download"]
            raise Exception(f"Result Error: {data}")