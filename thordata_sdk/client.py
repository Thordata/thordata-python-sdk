import requests
import logging
import json
from typing import Dict, Any, Optional

# Use a library-specific logger
logger = logging.getLogger(__name__)

class ThordataClient:
    """
    The official synchronous Python client for Thordata.
    
    Handles authentication for:
    1. Proxy Network (HTTP/HTTPS)
    2. SERP API (Real-time Search)
    3. Web Scraper API (Async Task Management)
    """

    def __init__(self, scraper_token: str, public_token: str, public_key: str, 
                 proxy_host: str = "gate.thordata.com", proxy_port: int = 22225):
        """
        Initialize the Thordata Client.

        Args:
            scraper_token (str): Token from the bottom of the Dashboard (used for Creating Tasks & SERP).
            public_token (str): Token from the "Public API" section (used for Status/Download).
            public_key (str): Key from the "Public API" section.
            proxy_host (str): Proxy gateway host. Defaults to "gate.thordata.com".
            proxy_port (int): Proxy gateway port. Defaults to 22225.
        """
        self.scraper_token = scraper_token
        self.public_token = public_token
        self.public_key = public_key
        
        # Proxy Configuration (User: Scraper Token, Pass: Empty)
        self.proxy_url = f"http://{self.scraper_token}:@{proxy_host}:{proxy_port}"
        
        # API Endpoints
        self.SERP_API_URL = "https://scraperapi.thordata.com/request"
        self.SCRAPER_BUILDER_URL = "https://scraperapi.thordata.com/builder"
        self.SCRAPER_STATUS_URL = "https://api.thordata.com/api/web-scraper-api/tasks-status"
        self.SCRAPER_DOWNLOAD_URL = "https://api.thordata.com/api/web-scraper-api/tasks-download"

        self.session = requests.Session()
        self.session.proxies = {
            "http": self.proxy_url,
            "https": self.proxy_url,
        }

    def get(self, url: str, **kwargs) -> requests.Response:
        """
        Send a GET request through the Thordata Proxy Network.
        
        Args:
            url (str): The target URL.
            **kwargs: Additional arguments passed to requests.get().
        
        Returns:
            requests.Response: The HTTP response.
        """
        logger.debug(f"Proxy Request: {url}")
        kwargs.setdefault("timeout", 30)
        return self.session.get(url, **kwargs)

    def serp_search(self, query: str, engine: str = "google", num: int = 10, **kwargs) -> Dict[str, Any]:
        """
        Execute a real-time SERP search.

        Args:
            query (str): The search query.
            engine (str): Search engine (google, bing, yandex, duckduckgo).
            num (int): Number of results.
        
        Returns:
            Dict: The parsed JSON response containing search results.
        """
        payload = {"q": query, "num": str(num), "json": "1", "engine": engine.lower(), **kwargs}
        
        # Engine-specific parameter adjustments
        if engine.lower() == 'yandex':
            payload['text'] = payload.pop('q') 
            if 'url' not in payload: payload['url'] = "yandex.com"
        elif 'url' not in payload:
             if engine == 'google': payload['url'] = "google.com"
             elif engine == 'bing': payload['url'] = "bing.com"
             elif engine == 'duckduckgo': payload['url'] = "duckduckgo.com"

        headers = {
            "Authorization": f"Bearer {self.scraper_token}", 
            "Content-Type": "application/x-www-form-urlencoded"
        }
        
        logger.info(f"SERP Search: {engine} - {query}")
        try:
            response = self.session.post(self.SERP_API_URL, data=payload, headers=headers, timeout=60)
            response.raise_for_status()
            data = response.json()
            
            # Handle potential double-encoded JSON strings
            if isinstance(data, str):
                try: data = json.loads(data)
                except: pass 
            return data
        except Exception as e:
            logger.error(f"SERP Request Failed: {e}")
            raise

    def create_scraper_task(self, file_name: str, spider_id: str, individual_params: Dict[str, Any], 
                            spider_name: str = "youtube.com", universal_params: Dict[str, Any] = None) -> str:
        """
        Create an Asynchronous Web Scraper Task.
        """
        headers = {
            "Authorization": f"Bearer {self.scraper_token}",
            "Content-Type": "application/x-www-form-urlencoded"
        }
        
        payload = {
            "spider_name": spider_name,
            "spider_id": spider_id, 
            "spider_parameters": json.dumps([individual_params]), 
            "spider_errors": "true",
            "file_name": file_name
        }
        if universal_params: 
            payload["spider_universal"] = json.dumps(universal_params)
        
        logger.info(f"Creating Scraper Task: {spider_id}")
        try:
            response = self.session.post(self.SCRAPER_BUILDER_URL, data=payload, headers=headers)
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
        Returns: 'Running', 'Ready', 'Failed', or 'Unknown'.
        """
        headers = {
            "token": self.public_token,
            "key": self.public_key,
            "Content-Type": "application/x-www-form-urlencoded"
        }
        payload = {"tasks_ids": task_id}
        
        try:
            response = self.session.post(self.SCRAPER_STATUS_URL, data=payload, headers=headers)
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
            response = self.session.post(self.SCRAPER_DOWNLOAD_URL, data=payload, headers=headers)
            response.raise_for_status()
            data = response.json()
            
            if data.get("code") == 200 and data.get("data"):
                return data["data"]["download"]
            raise Exception(f"API returned error: {data}")
        except Exception as e:
            logger.error(f"Get Result Failed: {e}")
            raise