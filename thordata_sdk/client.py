import requests
from requests.exceptions import RequestException
import logging
from typing import Optional, Dict, Any

# Configure basic logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ThordataClient:
    """
    Thordata Synchronous Client.
    
    Handles proxy authentication and simplifies sending HTTP requests via the Thordata network.
    Ideal for standard scripts and low-concurrency data collection tasks.
    """

    def __init__(self, api_key: str, proxy_host: str = "proxy.thordata.com:8000"):
        """
        Initialize the Thordata synchronous client.

        Args:
            api_key (str): Your Thordata API Key (used as the proxy username).
            proxy_host (str, optional): Thordata proxy gateway address. Defaults to "proxy.thordata.com:8000".
        """
        self.api_key = api_key
        self.proxy_host = proxy_host
        self.base_url = "https://api.thordata.com/v1"
        
        # Construct the proxy URL for internal use (Format: http://user:password@host:port)
        # Note: Thordata uses the API Key as the username and leaves the password empty.
        self.proxy_url = f"http://{self.api_key}:@{self.proxy_host}"
        
        # Initialize a persistent session for connection pooling and cookie persistence
        self.session = requests.Session()
        self._setup_proxy()

    def _setup_proxy(self):
        """Configure the requests Session to use Thordata proxy authentication."""
        self.session.proxies = {
            "http": self.proxy_url,
            "https": self.proxy_url,
        }

    def get(self, url: str, **kwargs) -> requests.Response:
        """
        Send a GET request through the Thordata proxy network.

        Args:
            url (str): The target URL to scrape.
            **kwargs: Arbitrary keyword arguments passed to `requests.Session.get` 
                      (e.g., headers, params, timeout).

        Returns:
            requests.Response: The response object from the target server.

        Raises:
            requests.RequestException: If the request fails due to network or proxy issues.
        """
        logger.debug(f"Requesting {url} via {self.proxy_host}")

        try:
            # Use the pre-configured session
            response = self.session.get(
                url, 
                timeout=30, # Default timeout to prevent hanging
                **kwargs
            )
            # Raise an error for 4xx/5xx responses
            response.raise_for_status()
            return response
            
        except RequestException as e:
            logger.error(f"Sync Request failed for {url}. Details: {e}")
            raise