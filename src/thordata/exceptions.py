"""
Custom exception types for the Thordata Python SDK.

Exception Hierarchy:
    ThordataError (base)
    ├── ThordataConfigError      - Configuration/initialization issues
    ├── ThordataNetworkError     - Network connectivity issues (retryable)
    │   └── ThordataTimeoutError - Request timeout (retryable)
    └── ThordataAPIError         - API returned an error
        ├── ThordataAuthError        - 401/403 authentication issues
        ├── ThordataRateLimitError   - 429/402 rate limit/quota issues
        ├── ThordataServerError      - 5xx server errors (retryable)
        └── ThordataValidationError  - 400 bad request / validation errors
"""

from __future__ import annotations

from typing import Any, Optional, Set

# =============================================================================
# Base Exception
# =============================================================================


class ThordataError(Exception):
    """Base error for all Thordata SDK issues."""

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


# =============================================================================
# Configuration Errors
# =============================================================================


class ThordataConfigError(ThordataError):
    """
    Raised when the SDK is misconfigured.

    Examples:
        - Missing required tokens
        - Invalid parameter combinations
    """

    pass


# =============================================================================
# Network Errors (Usually Retryable)
# =============================================================================


class ThordataNetworkError(ThordataError):
    """
    Raised when a network-level error occurs.

    This is typically retryable (DNS failures, connection refused, etc.)
    """

    def __init__(
        self,
        message: str,
        *,
        original_error: Optional[Exception] = None,
    ) -> None:
        super().__init__(message)
        self.original_error = original_error


class ThordataTimeoutError(ThordataNetworkError):
    """
    Raised when a request times out.

    This is typically retryable.
    """

    pass


# =============================================================================
# API Errors
# =============================================================================


class ThordataAPIError(ThordataError):
    """
    Generic API error raised when the backend returns a non-success code
    or an unexpected response payload.

    Attributes:
        message:      Human-readable error message.
        status_code:  HTTP status code from the response (e.g., 401, 500).
        code:         Application-level code from the Thordata API JSON response.
        payload:      Raw payload (dict/str) returned by the API.
        request_id:   Optional request ID for debugging with support.
    """

    # HTTP status codes that indicate this error type
    HTTP_STATUS_CODES: Set[int] = set()

    def __init__(
        self,
        message: str,
        *,
        status_code: Optional[int] = None,
        code: Optional[int] = None,
        payload: Any = None,
        request_id: Optional[str] = None,
    ) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.code = code
        self.payload = payload
        self.request_id = request_id

    def __repr__(self) -> str:
        return (
            f"{self.__class__.__name__}("
            f"message={self.message!r}, "
            f"status_code={self.status_code}, "
            f"code={self.code}, "
            f"request_id={self.request_id!r})"
        )

    @property
    def is_retryable(self) -> bool:
        """Whether this error is typically safe to retry."""
        return False


class ThordataAuthError(ThordataAPIError):
    """
    Authentication or authorization failures.

    HTTP Status: 401, 403
    Common causes:
        - Invalid or expired token
        - Insufficient permissions
        - IP not whitelisted
    """

    HTTP_STATUS_CODES = {401, 403}

    @property
    def is_retryable(self) -> bool:
        return False  # Auth errors shouldn't be retried


class ThordataRateLimitError(ThordataAPIError):
    """
    Rate limiting or quota/balance issues.

    HTTP Status: 429, 402
    Common causes:
        - Too many requests per second
        - Insufficient account balance
        - Quota exceeded

    Attributes:
        retry_after: Suggested seconds to wait before retrying (if provided).
    """

    HTTP_STATUS_CODES = {429, 402}

    def __init__(
        self,
        message: str,
        *,
        retry_after: Optional[int] = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(message, **kwargs)
        self.retry_after = retry_after

    @property
    def is_retryable(self) -> bool:
        # Rate limits are retryable after waiting
        return True


class ThordataServerError(ThordataAPIError):
    """
    Server-side errors (5xx).

    HTTP Status: 500, 502, 503, 504
    These are typically transient and safe to retry.
    """

    HTTP_STATUS_CODES = {500, 502, 503, 504}

    @property
    def is_retryable(self) -> bool:
        return True


class ThordataValidationError(ThordataAPIError):
    """
    Request validation errors.

    HTTP Status: 400, 422
    Common causes:
        - Invalid parameters
        - Missing required fields
        - Malformed request body
    """

    HTTP_STATUS_CODES = {400, 422}

    @property
    def is_retryable(self) -> bool:
        return False  # Bad requests shouldn't be retried


class ThordataNotCollectedError(ThordataAPIError):
    """
    The request was accepted but no valid data could be collected/parsed.

    API Code: 300
    Billing: Not billed (per Thordata billing rules).
    This error is often transient and typically safe to retry.
    """

    API_CODES = {300}
    HTTP_STATUS_CODES: Set[int] = set()

    @property
    def is_retryable(self) -> bool:
        return True


# =============================================================================
# Exception Factory
# =============================================================================


def raise_for_code(
    message: str,
    *,
    status_code: Optional[int] = None,
    code: Optional[int] = None,
    payload: Any = None,
    request_id: Optional[str] = None,
) -> None:
    """
    Factory function to raise the appropriate exception based on status/code.

    This centralizes the error-mapping logic that was previously duplicated
    across multiple methods.

    Args:
        message: Human-readable error message.
        status_code: HTTP status code (if available).
        code: Application-level code from API response.
        payload: Raw API response payload.
        request_id: Optional request ID for debugging.

    Raises:
        ThordataAuthError: For 401/403 codes.
        ThordataRateLimitError: For 429/402 codes.
        ThordataServerError: For 5xx codes.
        ThordataValidationError: For 400/422 codes.
        ThordataAPIError: For all other error codes.
    """
    # Determine the effective error code.
    # Prefer payload `code` when present and not success (200),
    # otherwise fall back to HTTP status when it indicates an error.
    effective_code: Optional[int] = None

    if code is not None and code != 200:
        effective_code = code
    elif status_code is not None and status_code != 200:
        effective_code = status_code
    else:
        effective_code = code if code is not None else status_code

    kwargs = {
        "status_code": status_code,
        "code": code,
        "payload": payload,
        "request_id": request_id,
    }

    # Not collected (API payload code 300, often retryable, not billed)
    # Check this FIRST since 300 is in API_CODES, not HTTP_STATUS_CODES
    if effective_code in ThordataNotCollectedError.API_CODES:
        raise ThordataNotCollectedError(message, **kwargs)

    # Auth errors
    if effective_code in ThordataAuthError.HTTP_STATUS_CODES:
        raise ThordataAuthError(message, **kwargs)

    # Rate limit errors
    if effective_code in ThordataRateLimitError.HTTP_STATUS_CODES:
        # Try to extract retry_after from payload
        retry_after = None
        if isinstance(payload, dict):
            retry_after = payload.get("retry_after")
        raise ThordataRateLimitError(message, retry_after=retry_after, **kwargs)

    # Server errors
    if effective_code is not None and 500 <= effective_code < 600:
        raise ThordataServerError(message, **kwargs)

    # Validation errors
    if effective_code in ThordataValidationError.HTTP_STATUS_CODES:
        raise ThordataValidationError(message, **kwargs)

    # Generic API error
    raise ThordataAPIError(message, **kwargs)


# =============================================================================
# Retry Helper
# =============================================================================


def is_retryable_exception(exc: Exception) -> bool:
    """
    Check if an exception is safe to retry.

    Args:
        exc: The exception to check.

    Returns:
        True if the exception is typically safe to retry.
    """
    # Network errors are retryable
    if isinstance(exc, ThordataNetworkError):
        return True

    # Check API errors with is_retryable property
    if isinstance(exc, ThordataAPIError):
        return exc.is_retryable

    # requests/aiohttp specific exceptions
    # (imported dynamically to avoid hard dependency)
    try:
        import requests

        if isinstance(exc, (requests.Timeout, requests.ConnectionError)):
            return True
    except ImportError:
        pass

    try:
        import aiohttp

        if isinstance(exc, (aiohttp.ClientError, aiohttp.ServerTimeoutError)):
            return True
    except ImportError:
        pass

    return False
