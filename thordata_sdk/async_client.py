import aiohttp
import asyncio
from aiohttp.client_exceptions import ClientResponseError
from typing import Optional, Any
import logging

logger = logging.getLogger(__name__)

class AsyncThordataClient:
    """
    Thordata Asynchronous Client.
    
    Built on `aiohttp`, designed for high-concurrency, low-latency AI data collection tasks.
    Must be used within an `async` context manager to ensure proper resource management.

    Usage:
        async with AsyncThordataClient(api_key="...") as client:
            response = await client.get("https://example.com")
    """
    
    def __init__(self, api_key: str, proxy_host: str = "gate.thordata.com", port: int = 22225):
        """
        Initialize the asynchronous client.

        Args:
            api_key (str): Your Thordata API Key (used as the proxy username).
            proxy_host (str, optional): Thordata proxy gateway address. Defaults to "gate.thordata.com".
            port (int, optional): Proxy port. Defaults to 22225.
        """
        # Configure Basic Authentication for aiohttp (User: API Key, Pass: Empty)
        self.proxy_auth = aiohttp.BasicAuth(login=api_key, password='')
        self.proxy_url = f"http://{proxy_host}:{port}"
        self.api_key = api_key
        
        # Session will be initialized in __aenter__
        self._session: Optional[aiohttp.ClientSession] = None
        
    async def __aenter__(self):
        """Enter the async context manager and initialize the session."""
        if self._session is None or self._session.closed:
            # trust_env=True enables reading system proxy settings if needed
            self._session = aiohttp.ClientSession(trust_env=True)
        return self

    async def __aexit__(self, exc_type, exc, tb):
        """Exit the async context manager and close the session."""
        await self.close()
        
    async def close(self):
        """Explicitly close the client session to release resources."""
        if self._session and not self._session.closed:
            await self._session.close()
            self._session = None

    async def get(self, url: str, **kwargs) -> aiohttp.ClientResponse:
        """
        Send an asynchronous GET request through the Thordata proxy.

        Args:
            url (str): The target URL.
            **kwargs: Additional arguments passed to `session.get` (headers, cookies, etc.).

        Returns:
            aiohttp.ClientResponse: The response object.

        Raises:
            RuntimeError: If the client is used outside of a context manager.
            aiohttp.ClientError: If the request fails.
        """
        if self._session is None:
             raise RuntimeError("Client session not initialized. Please use 'async with AsyncThordataClient(...)' context manager.")
             
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