import aiohttp
import logging
import json
import base64
from typing import Optional, Dict, Any, Union

logger = logging.getLogger(__name__)


class AsyncThordataClient:
    """
    Thordata Asynchronous Client (built on aiohttp).
    """

    def __init__(
        self,
        scraper_token: str,
        public_token: str,
        public_key: str,
        proxy_host: str = "gate.thordata.com",
        proxy_port: int = 22225
    ):
        self.scraper_token = scraper_token
        self.public_token = public_token
        self.public_key = public_key

        self.proxy_auth = aiohttp.BasicAuth(login=scraper_token, password='')
        self.proxy_url = f"http://{proxy_host}:{proxy_port}"

        self.base_url = "https://scraperapi.thordata.com"
        self.universal_url = "https://universalapi.thordata.com"
        self.api_url = "https://api.thordata.com/api/web-scraper-api"

        self.SERP_API_URL = f"{self.base_url}/request"
        self.UNIVERSAL_API_URL = f"{self.universal_url}/request"
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
        if self._session and not self._session.closed:
            await self._session.close()
            self._session = None

    # --- Proxy ---
    async def get(self, url: str, **kwargs) -> aiohttp.ClientResponse:
        if self._session is None:
            raise RuntimeError("Client session not initialized.")
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

    # --- SERP ---
    async def serp_search(
        self, query: str, engine: str = "google", num: int = 10, **kwargs
    ) -> Dict[str, Any]:
        if self._session is None:
            raise RuntimeError("Client session not initialized.")

        payload = {
            "q": query, "num": str(num), "json": "1",
            "engine": engine.lower(), **kwargs
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
            if isinstance(data, str):
                try:
                    data = json.loads(data)
                except Exception:
                    pass
            return data

    # --- Universal ---
    async def universal_scrape(
        self,
        url: str,
        js_render: bool = False,
        output_format: str = "HTML",
        country: str = None,
        block_resources: bool = False
    ) -> Union[str, bytes]:
        if self._session is None:
            raise RuntimeError("Client session not initialized.")

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

        async with self._session.post(
            self.UNIVERSAL_API_URL, data=payload, headers=headers
        ) as response:
            response.raise_for_status()

            try:
                resp_json = await response.json()
            except Exception:
                if output_format.upper() == "PNG":
                    return await response.read()
                return await response.text()

            if isinstance(resp_json, dict) and resp_json.get("code") \
                    and resp_json.get("code") != 200:
                raise Exception(f"Universal API Error: {resp_json}")

            if "html" in resp_json:
                return resp_json["html"]

            if "png" in resp_json:
                png_str = resp_json["png"]
                if not png_str:
                    raise Exception("API returned empty PNG data")

                png_str = png_str.replace("\n", "").replace("\r", "")
                missing_padding = len(png_str) % 4
                if missing_padding:
                    png_str += '=' * (4 - missing_padding)
                return base64.b64decode(png_str)

            return str(resp_json)

    # --- Web Scraper ---
    async def create_scraper_task(
        self,
        file_name: str,
        spider_id: str,
        individual_params: Dict[str, Any],
        spider_name: str = "youtube.com",
        universal_params: Dict[str, Any] = None
    ) -> str:
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