"""
Retry mechanism for the Thordata Python SDK.

This module provides configurable retry logic for handling transient failures
in API requests, with support for exponential backoff and jitter.

Example:
    >>> from thordata.retry import RetryConfig, with_retry
    >>>
    >>> config = RetryConfig(max_retries=3, backoff_factor=1.0)
    >>>
    >>> @with_retry(config)
    >>> def make_request():
    ...     return requests.get("https://api.example.com")
"""

from __future__ import annotations

import logging
import random
import time
from dataclasses import dataclass, field
from functools import wraps
from typing import Any, Callable, Optional, Set, Tuple

from .exceptions import (
    ThordataNetworkError,
    ThordataRateLimitError,
    ThordataServerError,
    is_retryable_exception,
)

logger = logging.getLogger(__name__)


@dataclass
class RetryConfig:
    """
    Configuration for retry behavior.

    Attributes:
        max_retries: Maximum number of retry attempts (default: 3).
        backoff_factor: Multiplier for exponential backoff (default: 1.0).
            Wait time = backoff_factor * (2 ** attempt_number)
        max_backoff: Maximum wait time in seconds (default: 60).
        jitter: Add random jitter to prevent thundering herd (default: True).
        jitter_factor: Maximum jitter as fraction of wait time (default: 0.1).
        retry_on_status_codes: HTTP status codes to retry on.
        retry_on_exceptions: Exception types to retry on.

    Example:
        >>> config = RetryConfig(
        ...     max_retries=5,
        ...     backoff_factor=2.0,
        ...     max_backoff=120
        ... )
    """

    max_retries: int = 3
    backoff_factor: float = 1.0
    max_backoff: float = 60.0
    jitter: bool = True
    jitter_factor: float = 0.1

    # Status codes to retry on (5xx server errors + 429 rate limit)
    retry_on_status_codes: Set[int] = field(
        default_factory=lambda: {429, 500, 502, 503, 504}
    )
    retry_on_api_codes: Set[int] = field(
        default_factory=lambda: {300}  # API response body code
    )

    # Exception types to always retry on
    retry_on_exceptions: Tuple[type, ...] = field(
        default_factory=lambda: (
            ThordataNetworkError,
            ThordataServerError,
        )
    )

    def calculate_delay(self, attempt: int) -> float:
        """
        Calculate the delay before the next retry attempt.

        Args:
            attempt: Current attempt number (0-indexed).

        Returns:
            Delay in seconds.
        """
        # Exponential backoff
        delay = self.backoff_factor * (2**attempt)

        # Apply maximum cap
        delay = min(delay, self.max_backoff)

        # Add jitter if enabled
        if self.jitter:
            jitter_range = delay * self.jitter_factor
            delay += random.uniform(-jitter_range, jitter_range)
            delay = max(0.1, delay)  # Ensure positive delay

        return delay

    def should_retry(
        self, exception: Exception, attempt: int, status_code: Optional[int] = None
    ) -> bool:
        """
        Determine if a request should be retried.

        Args:
            exception: The exception that was raised.
            attempt: Current attempt number.
            status_code: HTTP status code if available.

        Returns:
            True if the request should be retried.
        """
        # Check if we've exceeded max retries
        if attempt >= self.max_retries:
            return False

        # Check status code
        if status_code and status_code in self.retry_on_status_codes:
            return True

        # Check exception type
        if isinstance(exception, self.retry_on_exceptions):
            return True

        # Check rate limit with retry_after
        if isinstance(exception, ThordataRateLimitError):
            return True

        # Use generic retryable check
        return is_retryable_exception(exception)


def with_retry(
    config: Optional[RetryConfig] = None,
    on_retry: Optional[Callable[[int, Exception, float], None]] = None,
) -> Callable:
    """
    Decorator to add retry logic to a function.

    Args:
        config: Retry configuration. Uses defaults if not provided.
        on_retry: Optional callback called before each retry.
            Receives (attempt, exception, delay).

    Returns:
        Decorated function with retry logic.

    Example:
        >>> @with_retry(RetryConfig(max_retries=3))
        ... def fetch_data():
        ...     return requests.get("https://api.example.com")

        >>> @with_retry()
        ... async def async_fetch():
        ...     async with aiohttp.ClientSession() as session:
        ...         return await session.get("https://api.example.com")
    """
    if config is None:
        config = RetryConfig()

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
            last_exception: Optional[Exception] = None

            for attempt in range(config.max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e

                    status_code = _extract_status_code(e)

                    if not config.should_retry(e, attempt, status_code):
                        raise

                    delay = config.calculate_delay(attempt)

                    if isinstance(e, ThordataRateLimitError) and e.retry_after:
                        delay = max(delay, e.retry_after)

                    logger.warning(
                        f"Retry attempt {attempt + 1}/{config.max_retries} "
                        f"after {delay:.2f}s due to: {e}"
                    )

                    if on_retry:
                        on_retry(attempt, e, delay)

                    time.sleep(delay)

            if last_exception:
                raise last_exception
            raise RuntimeError("Unexpected retry loop exit")

        @wraps(func)
        async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
            import asyncio

            last_exception: Optional[Exception] = None

            for attempt in range(config.max_retries + 1):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    last_exception = e

                    status_code = _extract_status_code(e)

                    if not config.should_retry(e, attempt, status_code):
                        raise

                    delay = config.calculate_delay(attempt)

                    if isinstance(e, ThordataRateLimitError) and e.retry_after:
                        delay = max(delay, e.retry_after)

                    logger.warning(
                        f"Async retry attempt {attempt + 1}/{config.max_retries} "
                        f"after {delay:.2f}s due to: {e}"
                    )

                    if on_retry:
                        on_retry(attempt, e, delay)

                    await asyncio.sleep(delay)

            if last_exception:
                raise last_exception
            raise RuntimeError("Unexpected retry loop exit")

        # Check if the function is async
        import asyncio

        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper

    return decorator


def _extract_status_code(exception: Exception) -> Optional[int]:
    """
    Extract HTTP status code from various exception types.

    Args:
        exception: The exception to extract from.

    Returns:
        HTTP status code if found, None otherwise.
    """
    # Unwrap nested/original errors (e.g., ThordataNetworkError(original_error=...))
    if hasattr(exception, "original_error") and exception.original_error:
        nested = exception.original_error
        if isinstance(nested, Exception):
            nested_code = _extract_status_code(nested)
            if nested_code is not None:
                return nested_code

    # Check Thordata exceptions
    if hasattr(exception, "status_code"):
        return exception.status_code
    if hasattr(exception, "code"):
        return exception.code

    # Check requests exceptions
    if hasattr(exception, "response"):
        response = exception.response
        if response is not None and hasattr(response, "status_code"):
            return response.status_code

    # Check aiohttp exceptions
    if hasattr(exception, "status"):
        return exception.status

    return None


class RetryableRequest:
    """
    Context manager for retryable requests with detailed control.

    This provides more control than the decorator approach, allowing
    you to check retry status during execution.

    Example:
        >>> config = RetryConfig(max_retries=3)
        >>> with RetryableRequest(config) as retry:
        ...     while True:
        ...         try:
        ...             response = requests.get("https://api.example.com")
        ...             response.raise_for_status()
        ...             break
        ...         except Exception as e:
        ...             if not retry.should_continue(e):
        ...                 raise
        ...             retry.wait()
    """

    def __init__(self, config: Optional[RetryConfig] = None) -> None:
        self.config = config or RetryConfig()
        self.attempt = 0
        self.last_exception: Optional[Exception] = None

    def __enter__(self) -> RetryableRequest:
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        pass

    def should_continue(
        self, exception: Exception, status_code: Optional[int] = None
    ) -> bool:
        """
        Check if we should continue retrying.

        Args:
            exception: The exception that occurred.
            status_code: HTTP status code if available.

        Returns:
            True if we should retry, False otherwise.
        """
        self.last_exception = exception

        if status_code is None:
            status_code = _extract_status_code(exception)

        should_retry = self.config.should_retry(exception, self.attempt, status_code)

        if should_retry:
            self.attempt += 1

        return should_retry

    def wait(self) -> float:
        """
        Wait before the next retry attempt.

        Returns:
            The actual delay used.
        """
        delay = self.config.calculate_delay(self.attempt - 1)

        # Handle rate limit retry_after
        if (
            isinstance(self.last_exception, ThordataRateLimitError)
            and self.last_exception.retry_after
        ):
            delay = max(delay, self.last_exception.retry_after)

        logger.debug(f"Waiting {delay:.2f}s before retry {self.attempt}")
        time.sleep(delay)

        return delay

    async def async_wait(self) -> float:
        """
        Async version of wait().

        Returns:
            The actual delay used.
        """
        import asyncio

        delay = self.config.calculate_delay(self.attempt - 1)

        if (
            isinstance(self.last_exception, ThordataRateLimitError)
            and self.last_exception.retry_after
        ):
            delay = max(delay, self.last_exception.retry_after)

        logger.debug(f"Async waiting {delay:.2f}s before retry {self.attempt}")
        await asyncio.sleep(delay)

        return delay
