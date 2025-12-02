"""
Custom exception types for the Thordata Python SDK.

These make it easier for callers to distinguish between:
- authentication / permission issues
- rate limit / quota issues
- generic API failures
"""

from __future__ import annotations

from typing import Any, Optional


class ThordataError(Exception):
    """Base error for all Thordata SDK issues."""


class ThordataAPIError(ThordataError):
    """
    Generic API error raised when the backend returns a non-success code
    or an unexpected response payload.

    Attributes:
        message:      Human-readable error message.
        status_code:  Optional HTTP status code from the underlying response.
        code:         Optional application-level code from the Thordata API.
        payload:      Optional raw payload (dict / str) returned by the API.
    """

    def __init__(
        self,
        message: str,
        *,
        status_code: Optional[int] = None,
        code: Optional[int] = None,
        payload: Any = None,
    ) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.code = code
        self.payload = payload


class ThordataAuthError(ThordataAPIError):
    """Authentication or authorization failures (e.g. HTTP 401/403)."""


class ThordataRateLimitError(ThordataAPIError):
    """
    Rate limiting or quota / balance issues (e.g. HTTP 402/429, or code=402
    in the JSON payload).
    """