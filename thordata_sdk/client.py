import requests
from requests.exceptions import RequestException
import logging
from typing import Optional, Dict, Any, List, Union
import json
import time

# Configure basic logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ThordataClient:
    """
    Thordata Synchronous Client.
    
    Provides access to:
    1. Proxy Network (via requests session configuration)
    2. SERP API (Search Engine Results)
    3. Web Scraper API (Task-based crawling)
    """

    def __init__(self, api_key: str, secret_key: str = None, proxy_host: str = "proxy.thordata.com:8000"):
        """
        Initialize the Thordata client.

        Args:
            api_key (str): Your primary API Token (Used for Proxy Auth and 'token' header in APIs).
            secret_key (str, optional): Your secondary API Key (Required for Web Scraper API 'key' param).
            proxy_host (str, optional): Thordata proxy gateway. Defaults to "proxy.thordata.com:8000".
        """
        self.api_key = api_key
        self.secret_key = secret_key
        self.proxy_host = proxy_host
        
        # API Endpoints (Derived from official documentation)
        self.SERP_API_URL = "https://scraperapi.thordata.com/request"
        self.SCRAPER_BUILDER_URL = "https://scraperapi.thordata.com/builder"
        self.SCRAPER_STATUS_URL = "https://api.thordata.com/api/web-scraper-api/tasks-status"
        self.SCRAPER_DOWNLOAD_URL = "https://api.thordata.com/api/web-scraper-api/tasks-download"

        # Proxy Configuration
        self.proxy_url = f"http://{self.api_key}:@{self.proxy_host}"
        self.session = requests.Session()
        self._setup_proxy()

    def _setup_proxy(self):
        """Configure the requests Session to use Thordata proxy authentication."""
        self.session.proxies = {
            "http": self.proxy_url,
            "https": self.proxy_url,
        }

    # --- Proxy Usage ---

    def get(self, url: str, **kwargs) -> requests.Response:
        """Send a standard GET request through the Thordata proxy network."""
        logger.debug(f"Requesting {url} via {self.proxy_host}")
        try:
            response = self.session.get(url, timeout=30, **kwargs)
            response.raise_for_status()
            return response
        except RequestException as e:
            logger.error(f"Sync Request failed for {url}. Details: {e}")
            raise

    # --- SERP API (Synchronous) ---

    def serp_search(self, 
                    query: str, 
                    engine: str = "google", 
                    num: int = 10,
                    **kwargs) -> Dict[str, Any]:
        """
        Perform a real-time search using Thordata SERP API.

        Args:
            query (str): The search query (e.g., "pizza").
            engine (str): Search engine ('google', 'bing', 'yandex', 'duckduckgo'). Default 'google'.
            num (int): Number of results.
            **kwargs: Additional engine-specific parameters (e.g., 'gl', 'hl', 'location').

        Returns:
            dict: The JSON response containing search results.
        """
        # Construct payload based on engine documentation
        payload = {
            "q": query,
            "num": str(num),
            "json": "1", # Force JSON output
            **kwargs
        }
        
        # Handle Engine-specific logic
        # Yandex uses 'text' instead of 'q', and 'url' param for domain
        if engine.lower() == 'yandex':
            payload['text'] = payload.pop('q') # Rename q to text
            if 'url' not in payload:
                payload['url'] = "yandex.com"
        
        # Set default domains for other engines if not provided by user
        elif 'url' not in payload:
             if engine == 'google': payload['url'] = "google.com"
             elif engine == 'bing': payload['url'] = "bing.com"
             elif engine == 'duckduckgo': payload['url'] = "duckduckgo.com"

        headers = {
            "token": self.api_key,
            "Content-Type": "application/json"
        }

        logger.info(f"SERP Search: {engine} - {query}")
        
        try:
            # SERP API uses POST according to docs
            response = requests.post(self.SERP_API_URL, json=payload, headers=headers, timeout=60)
            response.raise_for_status()
            return response.json()
        except RequestException as e:
            logger.error(f"SERP API request failed: {e}")
            raise

    # --- Web Scraper API (Asynchronous Task) ---

    def create_scraper_task(self, 
                            file_name: str, 
                            spider_id: str, 
                            individual_params: Dict[str, Any], 
                            common_settings: Dict[str, Any] = None) -> str:
        """
        Create a new Web Scraper task.

        Args:
            file_name (str): Name for the output file.
            spider_id (str): ID of the scraper (e.g., 'amazon', 'facebook').
            individual_params (dict): Target specific params (e.g., {'keyword': 'iphone'}).
            common_settings (dict, optional): General settings.

        Returns:
            str: The task_id of the created task.
        """
        if not self.secret_key:
            raise ValueError("secret_key is required for Web Scraper API. Please provide it during initialization.")

        headers = {
            "token": self.api_key,
            "key": self.secret_key,
            # The doc mentions 'Authorization' header for Dashboard lookups, but 'token'/'key' for API usage.
            # We include Authorization just in case, using api_key as Bearer token.
            "Authorization": f"Bearer {self.api_key}" 
        }

        # Documentation suggests 'individual_params' might need to be a stringified JSON or just text.
        # We handle dict to string conversion automatically for convenience.
        if isinstance(individual_params, dict):
            # Inject spider_id if missing, as doc says it's included in individual_params
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

        logger.info(f"Creating Scraper Task: {spider_id}")
        
        response = requests.post(self.SCRAPER_BUILDER_URL, json=payload, headers=headers)
        response.raise_for_status()
        data = response.json()
        
        # Check business logic error code (200 means success)
        if data.get("code") != 200:
            raise Exception(f"Task creation failed: {data}")
            
        return data["data"]["task_id"]

    def get_task_status(self, task_id: str) -> str:
        """Check the status of a scraping task (e.g., 'Running', 'Ready')."""
        if not self.secret_key: raise ValueError("secret_key required")

        headers = {"token": self.api_key, "key": self.secret_key}
        payload = {"tasks_ids": task_id}

        response = requests.post(self.SCRAPER_STATUS_URL, json=payload, headers=headers)
        data = response.json()
        
        if data.get("code") == 200 and data.get("data"):
            # data['data'] is a list of objects
            for item in data["data"]:
                if item["task_id"] == task_id:
                    return item["status"]
        return "Unknown"

    def get_task_result(self, task_id: str, file_type: str = "json") -> str:
        """Get the download link for a completed task."""
        if not self.secret_key: raise ValueError("secret_key required")

        headers = {"token": self.api_key, "key": self.secret_key}
        payload = {"tasks_id": task_id, "type": file_type} 

        response = requests.post(self.SCRAPER_DOWNLOAD_URL, json=payload, headers=headers)
        data = response.json()
        
        if data.get("code") == 200 and data.get("data"):
            return data["data"]["download"]
        raise Exception(f"Failed to get result: {data}")