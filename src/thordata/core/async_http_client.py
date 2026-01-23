"""
Core Async HTTP Session management for Thordata SDK.
Wraps aiohttp.ClientSession with retry logic and standard headers.
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any, Dict, Optional

import aiohttp

from .. import __version__ as _sdk_version
from .._utils import build_user_agent
from ..exceptions import ThordataNetworkError, ThordataTimeoutError
from ..retry import RetryConfig, with_retry

logger = logging.getLogger(__name__)


class AsyncThordataHttpSession:
    """
    Async wrapper for HTTP requests with built-in retry logic.
    """

    def __init__(self, timeout: int = 30, retry_config: Optional[RetryConfig] = None):
        self._timeout = aiohttp.ClientTimeout(total=timeout)
        self._retry_config = retry_config or RetryConfig()
        self._session: Optional[aiohttp.ClientSession] = None
        self._headers = {
            "User-Agent": build_user_agent(_sdk_version, "aiohttp"),
            "Accept-Encoding": "gzip, deflate",
        }

    async def _ensure_session(self) -> aiohttp.ClientSession:
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession(
                timeout=self._timeout, headers=self._headers, trust_env=True
            )
        return self._session

    async def close(self) -> None:
        if self._session and not self._session.closed:
            await self._session.close()
            self._session = None

    async def request(
        self,
        method: str,
        url: str,
        params: Optional[Dict[str, Any]] = None,
        data: Any = None,
        headers: Optional[Dict[str, str]] = None,
        timeout: Optional[int] = None,
        proxy: Optional[str] = None,
        proxy_auth: Optional[aiohttp.BasicAuth] = None,
    ) -> aiohttp.ClientResponse:
        """
        Execute async HTTP request with automatic retry logic.
        """
        session = await self._ensure_session()

        # Determine timeout
        req_timeout = aiohttp.ClientTimeout(total=timeout) if timeout else self._timeout

        @with_retry(self._retry_config)
        async def _do_request() -> aiohttp.ClientResponse:
            try:
                return await session.request(
                    method=method,
                    url=url,
                    params=params,
                    data=data,
                    headers=headers,
                    timeout=req_timeout,
                    proxy=proxy,
                    proxy_auth=proxy_auth,
                )
            except asyncio.TimeoutError as e:
                # Map asyncio timeout to SDK timeout for retry handler
                raise ThordataTimeoutError(
                    f"Async request timed out: {e}", original_error=e
                ) from e
            except aiohttp.ClientError as e:
                # Map aiohttp errors to SDK network error
                raise ThordataNetworkError(
                    f"Async request failed: {e}", original_error=e
                ) from e

        return await _do_request()
