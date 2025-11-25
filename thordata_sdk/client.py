import requests
import logging
import json
import base64
from typing import Dict, Any, Union, Optional

from .enums import Engine
from .parameters import normalize_serp_params

# Configure a library-specific logger
logger = logging.getLogger(__name__)


class ThordataClient:
    """
    The official synchronous Python client for Thordata.

    Handles authentication for:
    1. Proxy Network (HTTP/HTTPS)
    2. SERP API (Real-time Search)
    3. Universal Scraping API (Single Page)
    4. Web Scraper API (Async Task Management)
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
        Initialize the Thordata Client.

        Args:
            scraper_token (str): Token from Dashboard bottom.
            public_token (str): Token from Public API section.
            public_key (str): Key from Public API section.
            proxy_host (str): Proxy gateway host.
            proxy_port (int): Proxy gateway port.
        """
        self.scraper_token = scraper_token
        self.public_token = public_token
        self.public_key = public_key

        # Proxy Configuration
        self.proxy_url = (
            f"http://{self.scraper_token}:@{proxy_host}:{proxy_port}"
        )

        # API Endpoints
        self.base_url = "https://scraperapi.thordata.com"
        self.universal_url = "https://universalapi.thordata.com"
        self.api_url = "https://api.thordata.com/api/web-scraper-api"

        self.SERP_API_URL = f"{self.base_url}/request"
        self.UNIVERSAL_API_URL = f"{self.universal_url}/request"
        self.SCRAPER_BUILDER_URL = f"{self.base_url}/builder"
        self.SCRAPER_STATUS_URL = f"{self.api_url}/tasks-status"
        self.SCRAPER_DOWNLOAD_URL = f"{self.api_url}/tasks-download"

        self.session = requests.Session()
        self.session.proxies = {
            "http": self.proxy_url,
            "https": self.proxy_url,
        }

    def get(self, url: str, **kwargs) -> requests.Response:
        """
        Send a GET request through the Thordata Proxy Network.
        """
        logger.debug(f"Proxy Request: {url}")
        kwargs.setdefault("timeout", 30)
        return self.session.get(url, **kwargs)

    def serp_search(
        self, 
        query: str, 
        engine: Union[Engine, str] = Engine.GOOGLE, # 既可以是枚举，也可以是字符串
        num: int = 10, 
        **kwargs # 这里接收所有额外参数 (比如 type="maps")
    ) -> Dict[str, Any]:
        """
        Execute a real-time SERP search.
        
        Args:
            query: Keywords
            engine: 'google', 'bing', 'yandex' etc.
            num: Number of results (default 10)
            **kwargs: Extra parameters (e.g., type="shopping", location="London")
        """
        # 兼容处理：如果用户传的是枚举对象，取它的值；如果是字符串，转小写
        engine_str = engine.value if isinstance(engine, Engine) else engine.lower()

        # 调用 parameters.py 里的逻辑
        payload = normalize_serp_params(engine_str, query, num=num, **kwargs)

        headers = {
            "Authorization": f"Bearer {self.scraper_token}",
            "Content-Type": "application/x-www-form-urlencoded"
        }

        logger.info(f"SERP Search: {engine_str} - {query}")
        try:
            response = self.session.post(
                self.SERP_API_URL,
                data=payload,
                headers=headers,
                timeout=60
            )
            response.raise_for_status()
            
            data = response.json()
            if isinstance(data, str):
                try: data = json.loads(data)
                except: pass
            return data
        except Exception as e:
            logger.error(f"SERP Request Failed: {e}")
            raise


    def universal_scrape(
        self,
        url: str,
        js_render: bool = False,
        output_format: str = "HTML",
        country: str = None,
        block_resources: bool = False
    ) -> Union[str, bytes]:
        """
        Unlock target pages via the Universal Scraping API.
        """
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

        logger.info(f"Universal Scrape: {url}")

        try:
            response = self.session.post(
                self.UNIVERSAL_API_URL,
                data=payload,
                headers=headers,
                timeout=60
            )
            response.raise_for_status()

            # Parse JSON wrapper
            try:
                resp_json = response.json()
            except json.JSONDecodeError:
                # Fallback for raw response
                if output_format.upper() == "PNG":
                    return response.content
                return response.text

            # Check API errors
            if isinstance(resp_json, dict) and resp_json.get("code") \
                    and resp_json.get("code") != 200:
                raise Exception(f"Universal API Error: {resp_json}")

            # Extract HTML
            if "html" in resp_json:
                return resp_json["html"]

            # Extract PNG
            if "png" in resp_json:
                png_str = resp_json["png"]
                if not png_str:
                    raise Exception("API returned empty PNG data")

                # 🛠️ FIX: 移除 Data URI Scheme 前缀 (data:image/png;base64,)
                if "," in png_str:
                    png_str = png_str.split(",", 1)[1]

                # Base64 解码 (处理 padding)
                png_str = png_str.replace("\n", "").replace("\r", "")
                missing_padding = len(png_str) % 4
                if missing_padding:
                    png_str += '=' * (4 - missing_padding)

                return base64.b64decode(png_str)

            return str(resp_json)

        except Exception as e:
            logger.error(f"Universal Scrape Failed: {e}")
            raise

    def create_scraper_task(
        self,
        file_name: str,
        spider_id: str,     # 必须传，用户从仪表板获取
        spider_name: str,   # 必须传，例如 "youtube.com"
        individual_params: Dict[str, Any], # 用户把具体的参数打包在这个字典里传进来
        universal_params: Dict[str, Any] = None
    ) -> str:
        """
        Create a generic Web Scraper Task.
        
        Note: Check the Thordata Dashboard to get the correct 'spider_id' and 'spider_name'.
        """
        headers = {
            "Authorization": f"Bearer {self.scraper_token}",
            "Content-Type": "application/x-www-form-urlencoded"
        }

        # 直接打包发送，不替用户做太多复杂的校验，保证兼容性
        payload = {
            "spider_name": spider_name,
            "spider_id": spider_id,
            "spider_parameters": json.dumps([individual_params]),
            "spider_errors": "true",
            "file_name": file_name
        }
        if universal_params:
            payload["spider_universal"] = json.dumps(universal_params)

        logger.info(f"Creating Scraper Task: {spider_name} (ID: {spider_id})")
        try:
            response = self.session.post(
                self.SCRAPER_BUILDER_URL,
                data=payload,
                headers=headers
            )
            response.raise_for_status()
            data = response.json()

            if data.get("code") != 200:
                raise Exception(f"Creation failed: {data}")
            return data["data"]["task_id"]
        except Exception as e:
            logger.error(f"Task Creation Failed: {e}")
            raise

    def get_task_status(self, task_id: str) -> str:
        """
        Check the status of a task.
        """
        headers = {
            "token": self.public_token,
            "key": self.public_key,
            "Content-Type": "application/x-www-form-urlencoded"
        }
        payload = {"tasks_ids": task_id}

        try:
            response = self.session.post(
                self.SCRAPER_STATUS_URL,
                data=payload,
                headers=headers
            )
            response.raise_for_status()
            data = response.json()

            if data.get("code") == 200 and data.get("data"):
                for item in data["data"]:
                    if str(item.get("task_id")) == str(task_id):
                        return item["status"]
            return "Unknown"
        except Exception as e:
            logger.error(f"Status Check Failed: {e}")
            return "Error"

    def get_task_result(self, task_id: str, file_type: str = "json") -> str:
        """
        Retrieve the download URL for a completed task.
        """
        headers = {
            "token": self.public_token,
            "key": self.public_key,
            "Content-Type": "application/x-www-form-urlencoded"
        }
        payload = {"tasks_id": task_id, "type": file_type}

        logger.info(f"Getting result URL: {task_id}")
        try:
            response = self.session.post(
                self.SCRAPER_DOWNLOAD_URL,
                data=payload,
                headers=headers
            )
            response.raise_for_status()
            data = response.json()

            if data.get("code") == 200 and data.get("data"):
                return data["data"]["download"]
            raise Exception(f"API returned error: {data}")
        except Exception as e:
            logger.error(f"Get Result Failed: {e}")
            raise