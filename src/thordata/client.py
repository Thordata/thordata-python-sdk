import requests
import logging
import json
import base64
from typing import Dict, Any, Union, Optional, List

from .enums import Engine
from .parameters import normalize_serp_params

# Configure a library-specific logger to avoid interfering with user's logging
logger = logging.getLogger(__name__)


class ThordataClient:
    """
    The official synchronous Python client for Thordata.

    This client handles authentication and communication with:
    1. Proxy Network (Residential/Datacenter via HTTP/HTTPS)
    2. SERP API (Real-time Search Engine Results)
    3. Universal Scraping API (Single Page Rendering & Extraction)
    4. Web Scraper API (Async Task Management for large scale jobs)
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
            scraper_token (str): The secret token found at the bottom of the Dashboard.
            public_token (str): The token from the Public API section.
            public_key (str): The key from the Public API section.
            proxy_host (str): The proxy gateway host (default: gate.thordata.com).
            proxy_port (int): The proxy gateway port (default: 22225).
        """
        self.scraper_token = scraper_token
        self.public_token = public_token
        self.public_key = public_key

        # Proxy Configuration
        self.proxy_url = (
            f"http://{self.scraper_token}:@{proxy_host}:{proxy_port}"
        )

        # API Endpoints Definition
        self.base_url = "https://scraperapi.thordata.com"
        self.universal_url = "https://universalapi.thordata.com"
        self.api_url = "https://api.thordata.com/api/web-scraper-api"
        self.locations_url = "https://api.thordata.com/api/locations"

        self.SERP_API_URL = f"{self.base_url}/request"
        self.UNIVERSAL_API_URL = f"{self.universal_url}/request"
        self.SCRAPER_BUILDER_URL = f"{self.base_url}/builder"
        self.SCRAPER_STATUS_URL = f"{self.api_url}/tasks-status"
        self.SCRAPER_DOWNLOAD_URL = f"{self.api_url}/tasks-download"

        # Initialize Session with Proxy settings
        self.session = requests.Session()
        self.session.proxies = {
            "http": self.proxy_url,
            "https": self.proxy_url,
        }

    def get(self, url: str, **kwargs) -> requests.Response:
        """
        Send a standard GET request through the Thordata Residential Proxy Network.

        Args:
            url (str): The target URL.
            **kwargs: Arguments to pass to requests.get().

        Returns:
            requests.Response: The response object.
        """
        logger.debug(f"Proxy Request: {url}")
        kwargs.setdefault("timeout", 30)
        return self.session.get(url, **kwargs)

    def serp_search(
        self, 
        query: str, 
        engine: Union[Engine, str] = Engine.GOOGLE,
        num: int = 10, 
        **kwargs
    ) -> Dict[str, Any]:
        """
        Execute a real-time SERP (Search Engine Results Page) search.
        
        Args:
            query (str): The search keywords.
            engine (Union[Engine, str]): The search engine (e.g., 'google', 'bing').
            num (int): Number of results to retrieve (default 10).
            **kwargs: Additional parameters (e.g., type="shopping", location="London").

        Returns:
            Dict[str, Any]: The parsed JSON result from the search engine.
        """
        # Handle Enum or String input for engine
        engine_str = engine.value if isinstance(engine, Engine) else engine.lower()

        # Normalize parameters via internal helper
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
            # Handle cases where the API returns a stringified JSON
            if isinstance(data, str):
                try: 
                    data = json.loads(data)
                except json.JSONDecodeError: 
                    pass
            return data
        except Exception as e:
            logger.error(f"SERP Request Failed: {e}")
            raise

    def universal_scrape(
        self,
        url: str,
        js_render: bool = False,
        output_format: str = "HTML",
        country: Optional[str] = None,
        block_resources: bool = False
    ) -> Union[str, bytes]:
        """
        Unlock target pages via the Universal Scraping API.
        Bypasses Cloudflare, CAPTCHAs, and antibot systems automatically.

        Args:
            url (str): Target URL.
            js_render (bool): Whether to render JavaScript (Headless Browser).
            output_format (str): "HTML" or "PNG" (screenshot).
            country (Optional[str]): Geo-targeting country code (e.g., 'us').
            block_resources (bool): Block images/css to speed up loading.

        Returns:
            Union[str, bytes]: HTML string or PNG bytes.
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

        logger.info(f"Universal Scrape: {url} (Format: {output_format})")

        try:
            response = self.session.post(
                self.UNIVERSAL_API_URL,
                data=payload,
                headers=headers,
                timeout=60
            )
            response.raise_for_status()

            # Attempt to parse JSON wrapper
            try:
                resp_json = response.json()
            except json.JSONDecodeError:
                # Fallback: if the API returns raw content directly
                if output_format.upper() == "PNG":
                    return response.content
                return response.text

            # Check for API-level errors inside the JSON
            if isinstance(resp_json, dict) and resp_json.get("code") \
                    and resp_json.get("code") != 200:
                raise Exception(f"Universal API Error: {resp_json}")

            # Case 1: Return HTML
            if "html" in resp_json:
                return resp_json["html"]

            # Case 2: Return PNG Image
            if "png" in resp_json:
                png_str = resp_json["png"]
                if not png_str:
                    raise Exception("API returned empty PNG data")

                # Clean Data URI Scheme if present (e.g., data:image/png;base64,...)
                if "," in png_str:
                    png_str = png_str.split(",", 1)[1]

                # Fix Base64 Padding
                png_str = png_str.replace("\n", "").replace("\r", "")
                missing_padding = len(png_str) % 4
                if missing_padding:
                    png_str += '=' * (4 - missing_padding)

                return base64.b64decode(png_str)

            # Fallback
            return str(resp_json)

        except Exception as e:
            logger.error(f"Universal Scrape Failed: {e}")
            raise

    def create_scraper_task(
        self,
        file_name: str,
        spider_id: str,
        spider_name: str,
        individual_params: Dict[str, Any],
        universal_params: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Create a generic Web Scraper Task (Async).
        
        IMPORTANT: You must retrieve the correct 'spider_id' and 'spider_name' 
        from the Thordata Dashboard before calling this method.

        Args:
            file_name (str): Name for the output file.
            spider_id (str): The ID of the spider (from Dashboard).
            spider_name (str): The name of the spider (e.g., "youtube.com").
            individual_params (Dict): Parameters specific to the spider.
            universal_params (Optional[Dict]): Global settings for the scraper.

        Returns:
            str: The created task_id.
        """
        headers = {
            "Authorization": f"Bearer {self.scraper_token}",
            "Content-Type": "application/x-www-form-urlencoded"
        }

        # Payload construction
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
        Check the status of an asynchronous scraping task.

        Args:
            task_id (str): The ID returned by create_scraper_task.

        Returns:
            str: The status string (e.g., "finished", "running", "error").
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

        Args:
            task_id (str): The task ID.
            file_type (str): Format required (default "json").

        Returns:
            str: The URL to download the result file.
        """
        headers = {
            "token": self.public_token,
            "key": self.public_key,
            "Content-Type": "application/x-www-form-urlencoded"
        }
        payload = {"tasks_id": task_id, "type": file_type}

        logger.info(f"Getting result URL for Task: {task_id}")
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
        
    def _get_locations(self, endpoint: str, params: Dict[str, str]) -> List[Dict[str, Any]]:
        """
        Internal helper to call the public locations API.

        Args:
            endpoint: One of 'countries', 'states', 'cities', 'asn'.
            params: Query parameters (must include token, key, proxy_type, etc.)

        Returns:
            List of location records from the 'data' field.

        Raises:
            RuntimeError: If token/key are missing or API returns an error code.
        """
        if not self.public_token or not self.public_key:
            raise RuntimeError(
                "Public API token/key are required for locations endpoints. "
                "Please provide 'public_token' and 'public_key' when "
                "initializing ThordataClient."
            )

        url = f"{self.locations_url}/{endpoint}"
        logger.info("Locations API request: %s", url)

        # Use a direct requests.get here; no need to go through the proxy gateway.
        response = requests.get(
            url,
            params=params,
            timeout=30,
        )
        response.raise_for_status()

        data = response.json()
        if isinstance(data, dict):
            code = data.get("code")
            if code is not None and code != 200:
                msg = data.get("msg", "")
                raise RuntimeError(
                    f"Locations API error ({endpoint}): code={code}, msg={msg}"
                )
            return data.get("data") or []
        # Fallback: if backend ever returns a list directly
        if isinstance(data, list):
            return data
        return []
    
    def list_countries(self, proxy_type: int = 1) -> List[Dict[str, Any]]:
        """
        List supported countries for Thordata residential or unlimited proxies.

        Args:
            proxy_type (int): 1 for residential proxies, 2 for unlimited proxies.

        Returns:
            List[Dict[str, Any]]: Each record contains 'country_code' and 'country_name'.
        """
        params = {
            "token": self.public_token,
            "key": self.public_key,
            "proxy_type": str(proxy_type),
        }
        return self._get_locations("countries", params)

    def list_states(self, country_code: str, proxy_type: int = 1) -> List[Dict[str, Any]]:
        """
        List supported states for a given country.

        Args:
            country_code (str): Country code (e.g., 'US').
            proxy_type (int): 1 for residential proxies, 2 for unlimited proxies.

        Returns:
            List[Dict[str, Any]]: Each record contains 'state_code' and 'state_name'.
        """
        params = {
            "token": self.public_token,
            "key": self.public_key,
            "proxy_type": str(proxy_type),
            "country_code": country_code,
        }
        return self._get_locations("states", params)

    def list_cities(
        self,
        country_code: str,
        state_code: Optional[str] = None,
        proxy_type: int = 1,
    ) -> List[Dict[str, Any]]:
        """
        List supported cities for a given country (and optional state).

        Args:
            country_code (str): Country code (e.g., 'US').
            state_code (Optional[str]): State code (e.g., 'alabama'), if applicable.
            proxy_type (int): 1 for residential proxies, 2 for unlimited proxies.

        Returns:
            List[Dict[str, Any]]: Each record contains 'city_code' and 'city_name'.
        """
        params: Dict[str, str] = {
            "token": self.public_token,
            "key": self.public_key,
            "proxy_type": str(proxy_type),
            "country_code": country_code,
        }
        if state_code:
            params["state_code"] = state_code

        return self._get_locations("cities", params)

    def list_asn(
        self,
        country_code: str,
        proxy_type: int = 1,
    ) -> List[Dict[str, Any]]:
        """
        List supported ASNs for a given country.

        Args:
            country_code (str): Country code (e.g., 'US').
            proxy_type (int): 1 for residential proxies, 2 for unlimited proxies.

        Returns:
            List[Dict[str, Any]]: Each record contains 'asn_code' and 'asn_name'.
        """
        params = {
            "token": self.public_token,
            "key": self.public_key,
            "proxy_type": str(proxy_type),
            "country_code": country_code,
        }
        return self._get_locations("asn", params)