"""
Core HTTP Session management for Thordata SDK.
Handles authentication injection, retries, and session lifecycle.
"""

from __future__ import annotations

from typing import Any

import requests

from .. import __version__ as _sdk_version
from .._utils import build_user_agent
from ..exceptions import ThordataNetworkError, ThordataTimeoutError
from ..retry import RetryConfig, with_retry


class ThordataHttpSession:
    """
    Wrapper around requests.Session with built-in retry and Thordata headers.
    """

    def __init__(
        self,
        timeout: int = 30,
        retry_config: RetryConfig | None = None,
        trust_env: bool = True,
    ):
        self._session = requests.Session()
        self._session.trust_env = trust_env
        self._timeout = timeout
        self._retry_config = retry_config or RetryConfig()

        # Default Headers
        self._session.headers.update(
            {
                "User-Agent": build_user_agent(_sdk_version, "requests"),
                "Accept-Encoding": "gzip, deflate",
            }
        )

    def close(self) -> None:
        self._session.close()

    def request(
        self,
        method: str,
        url: str,
        params: dict[str, Any] | None = None,
        data: Any = None,
        headers: dict[str, str] | None = None,
        timeout: int | None = None,
        stream: bool = False,
    ) -> requests.Response:
        """
        Execute HTTP request with automatic retry logic.
        """
        effective_timeout = timeout if timeout is not None else self._timeout

        @with_retry(self._retry_config)
        def _do_request() -> requests.Response:
            return self._session.request(
                method=method,
                url=url,
                params=params,
                data=data,
                headers=headers,
                timeout=effective_timeout,
                stream=stream,
            )

        try:
            return _do_request()
        except requests.Timeout as e:
            raise ThordataTimeoutError(
                f"Request timed out: {e}", original_error=e
            ) from e
        except requests.RequestException as e:
            raise ThordataNetworkError(f"Request failed: {e}", original_error=e) from e
