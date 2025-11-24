import aiohttp
import asyncio
from aiohttp.client_exceptions import ClientResponseError
from typing import Optional, Dict, Any, List, Union
import logging
import json

logger = logging.getLogger(__name__)

class AsyncThordataClient:
    """
    Thordata Asynchronous Client.
    
    Built on `aiohttp`, designed for high-concurrency, low-latency AI data collection tasks.
    Provides access to Proxy Network, SERP API, and Web Scraper API.
    
    Must be used within an `async` context manager.

    Usage:
        async with AsyncThordataClient(api_key="...") as client:
            # Proxy usage
            response = await client.get("https://example.com")
            
            # SERP usage
            results = await client.serp_search("thordata")
    """
    
    def __init__(self, api_key: str, secret_key: str = None, proxy_host: str = "gate.thordata.com", port: int = 22225):
        """
        Initialize the asynchronous client.

        Args:
            api_key (str): Your primary API Token.
            secret_key (str, optional): Your secondary API Key (Required for Web Scraper API).
            proxy_host (str, optional): Thordata proxy gateway. Defaults to "gate.thordata.com".
            port (int, optional): Proxy port. Defaults to 22225.
        """
        self.api_key = api_key
        self.secret_key = secret_key
        
        # Proxy Auth (User: API Key, Pass: Empty)
        self.proxy_auth = aiohttp.BasicAuth(login=api_key, password='')
        self.proxy_url = f"http://{proxy_host}:{port}"
        
        # API Endpoints
        self.SERP_API_URL = "https://scraperapi.thordata.com/request"
        self.SCRAPER_BUILDER_URL = "https://scraperapi.thordata.com/builder"
        self.SCRAPER_STATUS_URL = "https://api.thordata.com/api/web-scraper-api/tasks-status"
        self.SCRAPER_DOWNLOAD_URL = "https://api.thordata.com/api/web-scraper-api/tasks-download"
        
        self._session: Optional[aiohttp.ClientSession] = None
        
    async def __aenter__(self):
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession(trust_env=True)
        return self

    async def __aexit__(self, exc_type, exc, tb):
        await self.close()
        
    async def close(self):
        if self._session and not self._session.closed:
            await self._session.close()
            self._session = None

    # --- Proxy Usage ---

    async def get(self, url: str, **kwargs) -> aiohttp.ClientResponse:
        """Send an asynchronous GET request through the Thordata proxy."""
        if self._session is None:
             raise RuntimeError("Client session not initialized. Use 'async with'.")
             
        logger.debug(f"Async Requesting {url} via {self.proxy_url}")
        
        try:
            response = await self._session.get(
                url, 
                proxy=self.proxy_url, 
                proxy_auth=self.proxy_auth,
                timeout=aiohttp.ClientTimeout(total=30),
                **kwargs
            )
            response.raise_for_status()
            return response
        except aiohttp.ClientError as e:
            logger.error(f"Async Request failed for {url}. Details: {e}")
            raise

    # --- SERP API (Asynchronous) ---

    async def serp_search(self, 
                          query: str, 
                          engine: str = "google", 
                          num: int = 10, 
                          **kwargs) -> Dict[str, Any]:
        """
        Perform a real-time search using Thordata SERP API asynchronously.
        """
        if self._session is None: raise RuntimeError("Client session not initialized.")

        payload = {
            "q": query,
            "num": str(num),
            "json": "1",
            **kwargs
        }
        
        # Handle Engine-specific logic (Yandex uses 'text')
        if engine.lower() == 'yandex':
            payload['text'] = payload.pop('q')
            if 'url' not in payload: payload['url'] = "yandex.com"
        elif 'url' not in payload:
             if engine == 'google': payload['url'] = "google.com"
             elif engine == 'bing': payload['url'] = "bing.com"

        headers = {
            "token": self.api_key,
            "Content-Type": "application/json"
        }

        logger.info(f"Async SERP Search: {engine} - {query}")
        
        async with self._session.post(self.SERP_API_URL, json=payload, headers=headers) as response:
            response.raise_for_status()
            return await response.json()

    # --- Web Scraper API (Asynchronous) ---

    async def create_scraper_task(self, 
                                  file_name: str, 
                                  spider_id: str, 
                                  individual_params: Dict[str, Any], 
                                  common_settings: Dict[str, Any] = None) -> str:
        """Create a new Web Scraper task asynchronously."""
        if not self.secret_key: raise ValueError("secret_key required for Web Scraper API.")
        if self._session is None: raise RuntimeError("Client session not initialized.")

        headers = {
            "token": self.api_key,
            "key": self.secret_key,
            "Authorization": f"Bearer {self.api_key}"
        }

        if isinstance(individual_params, dict):
            if 'spider_id' not in individual_params:
                individual_params['spider_id'] = spider_id
            params_str = json.dumps(individual_params)
        else:
            params_str = str(individual_params)

        payload = {
            "file_name": file_name,
            "spider_id": spider_id,
            "individual_params": params_str,
            "common_settings": json.dumps(common_settings) if common_settings else "{}"
        }

        async with self._session.post(self.SCRAPER_BUILDER_URL, json=payload, headers=headers) as response:
            response.raise_for_status()
            data = await response.json()
            
            if data.get("code") != 200:
                raise Exception(f"Task creation failed: {data}")
            return data["data"]["task_id"]

    async def get_task_status(self, task_id: str) -> str:
        """Check status of a task."""
        if not self.secret_key: raise ValueError("secret_key required")
        
        headers = {"token": self.api_key, "key": self.secret_key}
        payload = {"tasks_ids": task_id}

        async with self._session.post(self.SCRAPER_STATUS_URL, json=payload, headers=headers) as response:
            data = await response.json()
            if data.get("code") == 200 and data.get("data"):
                for item in data["data"]:
                    if item["task_id"] == task_id:
                        return item["status"]
            return "Unknown"

    async def get_task_result(self, task_id: str, file_type: str = "json") -> str:
        """Get download link for completed task."""
        if not self.secret_key: raise ValueError("secret_key required")
        
        headers = {"token": self.api_key, "key": self.secret_key}
        payload = {"tasks_id": task_id, "type": file_type}

        async with self._session.post(self.SCRAPER_DOWNLOAD_URL, json=payload, headers=headers) as response:
            data = await response.json()
            if data.get("code") == 200 and data.get("data"):
                return data["data"]["download"]
            raise Exception(f"Failed to get result: {data}")