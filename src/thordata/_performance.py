"""
Performance optimization utilities for Thordata SDK.

This module provides caching, connection pooling, and batch processing
optimizations to improve SDK performance.
"""

from __future__ import annotations

import functools
import time
from collections.abc import Callable
from typing import Any, TypeVar

T = TypeVar("T")


class SimpleCache:
    """
    Simple in-memory cache with TTL (Time To Live).

    Useful for caching API responses that don't change frequently.
    """

    def __init__(self, ttl: int = 300) -> None:
        """
        Initialize cache.

        Args:
            ttl: Time to live in seconds (default: 5 minutes).
        """
        self._cache: dict[str, tuple[Any, float]] = {}
        self._ttl = ttl

    def get(self, key: str) -> Any | None:
        """
        Get value from cache if not expired.

        Args:
            key: Cache key.

        Returns:
            Cached value or None if not found/expired.
        """
        if key not in self._cache:
            return None

        value, timestamp = self._cache[key]
        if time.time() - timestamp > self._ttl:
            del self._cache[key]
            return None

        return value

    def set(self, key: str, value: Any) -> None:
        """
        Set value in cache.

        Args:
            key: Cache key.
            value: Value to cache.
        """
        self._cache[key] = (value, time.time())

    def clear(self) -> None:
        """Clear all cached values."""
        self._cache.clear()

    def invalidate(self, key: str) -> None:
        """
        Invalidate a specific cache key.

        Args:
            key: Cache key to invalidate.
        """
        self._cache.pop(key, None)


def cached(ttl: int = 300, key_func: Callable[..., str] | None = None):
    """
    Decorator to cache function results.

    Args:
        ttl: Time to live in seconds.
        key_func: Optional function to generate cache key from arguments.

    Example:
        @cached(ttl=600)
        def get_balance():
            return client.get_traffic_balance()
    """

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        cache = SimpleCache(ttl=ttl)

        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> T:
            if key_func:
                cache_key = key_func(*args, **kwargs)
            else:
                # Default: use function name + args + kwargs
                cache_key = f"{func.__name__}:{str(args)}:{str(kwargs)}"

            cached_value = cache.get(cache_key)
            if cached_value is not None:
                return cached_value

            result = func(*args, **kwargs)
            cache.set(cache_key, result)
            return result

        wrapper.cache_clear = cache.clear  # type: ignore
        wrapper.cache_invalidate = cache.invalidate  # type: ignore
        return wrapper

    return decorator


class BatchProcessor:
    """
    Utility for processing multiple requests in batches.

    Helps optimize API usage by batching requests together.
    """

    def __init__(self, batch_size: int = 10, delay: float = 0.1) -> None:
        """
        Initialize batch processor.

        Args:
            batch_size: Maximum number of items per batch.
            delay: Delay between batches in seconds.
        """
        self.batch_size = batch_size
        self.delay = delay

    def process(
        self,
        items: list[Any],
        processor: Callable[[list[Any]], Any],
        *,
        parallel: bool = False,
    ) -> list[Any]:
        """
        Process items in batches.

        Args:
            items: List of items to process.
            processor: Function to process each batch.
            parallel: Whether to process batches in parallel (requires async).

        Returns:
            List of results.
        """
        results: list[Any] = []
        for i in range(0, len(items), self.batch_size):
            batch = items[i : i + self.batch_size]
            batch_results = processor(batch)
            if isinstance(batch_results, list):
                results.extend(batch_results)
            else:
                results.append(batch_results)

            # Add delay between batches to avoid rate limiting
            if i + self.batch_size < len(items):
                time.sleep(self.delay)

        return results


__all__ = ["SimpleCache", "cached", "BatchProcessor"]
