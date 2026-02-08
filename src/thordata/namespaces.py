"""
Unified namespace system for Thordata API organization.

This module provides a clean, organized namespace structure for all API operations,
making the SDK more intuitive and easier to use.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from .async_client import AsyncThordataClient
    from .client import ThordataClient


# =============================================================================
# Base Namespace Classes
# =============================================================================


class BaseNamespace:
    """Base class for all namespace implementations."""

    def __init__(self, client: ThordataClient | AsyncThordataClient) -> None:
        self._client = client
        # Check if client is async by checking class name
        self._is_async: bool = "Async" in type(client).__name__


# =============================================================================
# SERP Namespace (already exists, but we'll enhance it)
# =============================================================================

# SERP namespace is already well-implemented in serp_engines.py
# We'll keep it as-is but ensure it's properly integrated


# =============================================================================
# Universal Scraping Namespace
# =============================================================================


class UniversalNamespace(BaseNamespace):
    """
    Namespace for Universal Scraping API (Web Unlocker) operations.

    Provides a clean interface for web scraping with automatic JS rendering,
    CAPTCHA solving, and fingerprinting bypass.
    """

    def __init__(self, client: ThordataClient | AsyncThordataClient) -> None:
        super().__init__(client)

    def scrape(
        self,
        url: str,
        *,
        js_render: bool = True,
        country: str | None = None,
        wait_for: str | None = None,
        wait_time: int | None = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """
        Scrape a URL using Universal Scraping API.

        Args:
            url: The URL to scrape.
            js_render: Whether to enable JavaScript rendering.
            country: Country code for the request (e.g., "us", "jp").
            wait_for: CSS selector to wait for before returning.
            wait_time: Time to wait in seconds.
            **kwargs: Additional parameters.

        Returns:
            Scraped content as dictionary.
        """
        if self._is_async:
            raise TypeError("Use async method for AsyncThordataClient")
        return self._client.universal_scrape(  # type: ignore
            url=url,
            js_render=js_render,
            country=country,
            wait_for=wait_for,
            wait_time=wait_time,
            **kwargs,
        )

    async def scrape_async(
        self,
        url: str,
        *,
        js_render: bool = True,
        country: str | None = None,
        wait_for: str | None = None,
        wait_time: int | None = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """
        Async version of scrape.

        Args:
            url: The URL to scrape.
            js_render: Whether to enable JavaScript rendering.
            country: Country code for the request.
            wait_for: CSS selector to wait for.
            wait_time: Time to wait in seconds.
            **kwargs: Additional parameters.

        Returns:
            Scraped content as dictionary.
        """
        if not self._is_async:
            raise TypeError("Use sync method for ThordataClient")
        return await self._client.universal_scrape(  # type: ignore
            url=url,
            js_render=js_render,
            country=country,
            wait_for=wait_for,
            wait_time=wait_time,
            **kwargs,
        )


# =============================================================================
# Web Scraper Namespace
# =============================================================================


class WebScraperNamespace(BaseNamespace):
    """
    Namespace for Web Scraper API operations.

    Provides a clean interface for task management, tool execution,
    and result retrieval.
    """

    def create_task(
        self,
        file_name: str,
        spider_id: str,
        spider_name: str,
        parameters: dict[str, Any] | list[dict[str, Any]],
        *,
        common_settings: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> str:
        """
        Create a new scraping task.

        Args:
            file_name: Name for the task file.
            spider_id: The spider ID to use.
            spider_name: The spider name.
            parameters: Task parameters (dict or list of dicts).
            common_settings: Common settings for the task.
            **kwargs: Additional parameters.

        Returns:
            Task ID.
        """
        if self._is_async:
            raise TypeError("Use async method for AsyncThordataClient")
        return self._client.create_scraper_task(  # type: ignore
            file_name=file_name,
            spider_id=spider_id,
            spider_name=spider_name,
            parameters=parameters,
            common_settings=common_settings,
            **kwargs,
        )

    async def create_task_async(
        self,
        file_name: str,
        spider_id: str,
        spider_name: str,
        parameters: dict[str, Any] | list[dict[str, Any]],
        *,
        common_settings: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> str:
        """
        Async version of create_task.

        Args:
            file_name: Name for the task file.
            spider_id: The spider ID to use.
            spider_name: The spider name.
            parameters: Task parameters (dict or list of dicts).
            common_settings: Common settings for the task.
            **kwargs: Additional parameters.

        Returns:
            Task ID.
        """
        if not self._is_async:
            raise TypeError("Use sync method for ThordataClient")
        return await self._client.create_scraper_task(  # type: ignore
            file_name=file_name,
            spider_id=spider_id,
            spider_name=spider_name,
            parameters=parameters,
            common_settings=common_settings,
            **kwargs,
        )

    def get_status(self, task_id: str) -> dict[str, Any]:
        """Get task status."""
        if self._is_async:
            raise TypeError("Use async method for AsyncThordataClient")
        return self._client.get_task_status(task_id)  # type: ignore

    async def get_status_async(self, task_id: str) -> dict[str, Any]:
        """Get task status (async)."""
        if not self._is_async:
            raise TypeError("Use sync method for ThordataClient")
        return await self._client.get_task_status(task_id)  # type: ignore

    def get_result(self, task_id: str) -> str:
        """Get task result download URL."""
        if self._is_async:
            raise TypeError("Use async method for AsyncThordataClient")
        return self._client.get_task_result(task_id)  # type: ignore

    async def get_result_async(self, task_id: str) -> str:
        """Get task result download URL (async)."""
        if not self._is_async:
            raise TypeError("Use sync method for ThordataClient")
        return await self._client.get_task_result(task_id)  # type: ignore

    def wait_for_completion(
        self, task_id: str, *, max_wait: int = 600, poll_interval: int = 5
    ) -> str:
        """Wait for task completion."""
        if self._is_async:
            raise TypeError("Use async method for AsyncThordataClient")
        return self._client.wait_for_task(  # type: ignore
            task_id, max_wait=max_wait, poll_interval=poll_interval
        )

    async def wait_for_completion_async(
        self, task_id: str, *, max_wait: int = 600, poll_interval: int = 5
    ) -> str:
        """Wait for task completion (async)."""
        if not self._is_async:
            raise TypeError("Use sync method for ThordataClient")
        return await self._client.wait_for_task(  # type: ignore
            task_id, max_wait=max_wait, poll_interval=poll_interval
        )

    def list_tasks(
        self,
        *,
        page: int = 1,
        page_size: int = 20,
        start_time: int | None = None,
        end_time: int | None = None,
    ) -> dict[str, Any]:
        """List tasks."""
        if self._is_async:
            raise TypeError("Use async method for AsyncThordataClient")
        return self._client.list_tasks(  # type: ignore
            page=page, page_size=page_size, start_time=start_time, end_time=end_time
        )

    async def list_tasks_async(
        self,
        *,
        page: int = 1,
        page_size: int = 20,
        start_time: int | None = None,
        end_time: int | None = None,
    ) -> dict[str, Any]:
        """List tasks (async)."""
        if not self._is_async:
            raise TypeError("Use sync method for ThordataClient")
        return await self._client.list_tasks(  # type: ignore
            page=page, page_size=page_size, start_time=start_time, end_time=end_time
        )

    def run_tool(self, tool: Any) -> str:
        """Run a pre-built tool."""
        if self._is_async:
            raise TypeError("Use async method for AsyncThordataClient")
        return self._client.run_tool(tool)  # type: ignore

    async def run_tool_async(self, tool: Any) -> str:
        """Run a pre-built tool (async)."""
        if not self._is_async:
            raise TypeError("Use sync method for ThordataClient")
        return await self._client.run_tool(tool)  # type: ignore


# =============================================================================
# Account Management Namespace
# =============================================================================


class AccountNamespace(BaseNamespace):
    """
    Namespace for account management operations.

    Provides access to usage statistics, balance, and account configuration.
    """

    def __init__(self, client: ThordataClient | AsyncThordataClient) -> None:
        super().__init__(client)

    def get_usage_statistics(
        self,
        *,
        start_time: int | None = None,
        end_time: int | None = None,
        date: str | None = None,
    ) -> dict[str, Any]:
        """Get usage statistics."""
        if self._is_async:
            raise TypeError("Use async method for AsyncThordataClient")
        return self._client.get_traffic_balance(  # type: ignore
            start_time=start_time, end_time=end_time, date=date
        )

    async def get_usage_statistics_async(
        self,
        *,
        start_time: int | None = None,
        end_time: int | None = None,
        date: str | None = None,
    ) -> dict[str, Any]:
        """Get usage statistics (async)."""
        if not self._is_async:
            raise TypeError("Use sync method for ThordataClient")
        return await self._client.get_traffic_balance(  # type: ignore
            start_time=start_time, end_time=end_time, date=date
        )

    def get_balance(self) -> dict[str, Any]:
        """Get account balance."""
        if self._is_async:
            raise TypeError("Use async method for AsyncThordataClient")
        # get_traffic_balance returns float, convert to dict for consistency
        balance: float = self._client.get_traffic_balance()  # type: ignore
        return {"traffic_balance": balance}

    async def get_balance_async(self) -> dict[str, Any]:
        """Get account balance (async)."""
        if not self._is_async:
            raise TypeError("Use sync method for ThordataClient")
        # Async client returns float, convert to dict for consistency
        balance = await self._client.get_traffic_balance()  # type: ignore
        return {"traffic_balance": balance}


# =============================================================================
# Proxy Management Namespace
# =============================================================================


class ProxyNamespace(BaseNamespace):
    """
    Namespace for proxy management operations.

    Provides access to proxy user management, whitelist, and proxy configuration.
    """

    def __init__(self, client: ThordataClient | AsyncThordataClient) -> None:
        super().__init__(client)

    def list_users(
        self,
        *,
        page: int = 1,
        page_size: int = 20,
        username: str | None = None,
    ) -> dict[str, Any]:
        """List proxy users."""
        if self._is_async:
            raise TypeError("Use async method for AsyncThordataClient")
        return self._client.list_proxy_users(  # type: ignore
            page=page, page_size=page_size, username=username
        )

    async def list_users_async(
        self,
        *,
        page: int = 1,
        page_size: int = 20,
        username: str | None = None,
    ) -> dict[str, Any]:
        """List proxy users (async)."""
        if not self._is_async:
            raise TypeError("Use sync method for ThordataClient")
        return await self._client.list_proxy_users(  # type: ignore
            page=page, page_size=page_size, username=username
        )

    def create_user(
        self,
        username: str,
        password: str,
        *,
        traffic_limit: int | None = None,
    ) -> dict[str, Any]:
        """Create a proxy user."""
        if self._is_async:
            raise TypeError("Use async method for AsyncThordataClient")
        return self._client.create_proxy_user(  # type: ignore
            username=username, password=password, traffic_limit=traffic_limit
        )

    async def create_user_async(
        self,
        username: str,
        password: str,
        *,
        traffic_limit: int | None = None,
    ) -> dict[str, Any]:
        """Create a proxy user (async)."""
        if not self._is_async:
            raise TypeError("Use sync method for ThordataClient")
        return await self._client.create_proxy_user(  # type: ignore
            username=username, password=password, traffic_limit=traffic_limit
        )

    def add_whitelist_ip(self, ip: str) -> dict[str, Any]:
        """Add IP to whitelist."""
        if self._is_async:
            raise TypeError("Use async method for AsyncThordataClient")
        return self._client.add_whitelist_ip(ip)  # type: ignore

    async def add_whitelist_ip_async(self, ip: str) -> dict[str, Any]:
        """Add IP to whitelist (async)."""
        if not self._is_async:
            raise TypeError("Use sync method for ThordataClient")
        return await self._client.add_whitelist_ip(ip)  # type: ignore

    def list_whitelist_ips(self) -> list[str]:
        """List whitelisted IPs."""
        if self._is_async:
            raise TypeError("Use async method for AsyncThordataClient")
        return self._client.list_whitelist_ips()  # type: ignore

    async def list_whitelist_ips_async(self) -> list[str]:
        """List whitelisted IPs (async)."""
        if not self._is_async:
            raise TypeError("Use sync method for ThordataClient")
        return await self._client.list_whitelist_ips()  # type: ignore


__all__ = [
    "BaseNamespace",
    "UniversalNamespace",
    "WebScraperNamespace",
    "AccountNamespace",
    "ProxyNamespace",
]
