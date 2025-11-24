# D:\Thordata_Work\thordata-python-sdk\thordata_sdk\client.py

import requests
import logging
import json
from typing import Dict, Any

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ThordataClient:
    """
    Thordata Python Client
    Handles authentication for both Scraper Builder API (Bearer Token) 
    and Public Status/Download API (Token+Key).
    """
    def __init__(self, scraper_token: str, public_token: str, public_key: str, proxy_host: str = "proxy.thordata.com:8000"):
        # 1. 抓取工具 Token (用于创建任务)
        self.scraper_token = scraper_token
        # 2. 公共 API 凭证 (用于查询状态/下载)
        self.public_token = public_token
        self.public_key = public_key
        
        # API Endpoints
        self.SERP_API_URL = "https://scraperapi.thordata.com/request"
        self.SCRAPER_BUILDER_URL = "https://scraperapi.thordata.com/builder"
        self.SCRAPER_STATUS_URL = "https://api.thordata.com/api/web-scraper-api/tasks-status"
        self.SCRAPER_DOWNLOAD_URL = "https://api.thordata.com/api/web-scraper-api/tasks-download"

        self.session = requests.Session()

    def serp_search(self, query: str, engine: str = "google", num: int = 10, **kwargs) -> Dict[str, Any]:
        """
        Execute a Real-time SERP search.
        """
        payload = {"q": query, "num": str(num), "json": "1", "engine": engine.lower(), **kwargs}
        # Engine specific adjustments
        if engine.lower() == 'yandex': payload['text'] = payload.pop('q') 
        if 'url' not in payload: payload['url'] = f"{engine}.com"

        headers = {
            "Authorization": f"Bearer {self.scraper_token}", 
            "Content-Type": "application/x-www-form-urlencoded"
        }
        
        logger.info(f"SERP Search: {engine} - {query}")
        try:
            response = self.session.post(self.SERP_API_URL, data=payload, headers=headers, timeout=60)
            response.raise_for_status()
            data = response.json()
            # Handle double-encoded JSON string if present
            if isinstance(data, str):
                try: data = json.loads(data)
                except: pass 
            return data
        except Exception as e:
            logger.error(f"SERP Request Failed: {e}")
            raise

    def create_scraper_task(self, file_name: str, spider_id: str, individual_params: Dict[str, Any], spider_name: str = "youtube.com", universal_params: Dict[str, Any] = None) -> str:
        """
        Create an Async Scraper Task.
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
        
        logger.info(f"Creating Task: {spider_id}")
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
        Check the status of a task. Returns: 'Running', 'Ready', 'Failed', etc.
        """
        headers = {
            "token": self.public_token,
            "key": self.public_key,
            "Content-Type": "application/x-www-form-urlencoded"
        }
        payload = {"tasks_ids": task_id}
        
        logger.info(f"Checking status: {task_id}")
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

    def get_task_result(self, task_id: str) -> str:
        """
        Get the download URL for a completed task.
        """
        headers = {
            "token": self.public_token,
            "key": self.public_key,
            "Content-Type": "application/x-www-form-urlencoded"
        }
        payload = {"tasks_id": task_id, "type": "json"} 

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