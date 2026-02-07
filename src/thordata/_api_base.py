"""
Shared internal API base layer for sync and async clients.

This module contains common logic for:
- URL construction and configuration
- Header building
- Request validation
- Error handling

Both ThordataClient and AsyncThordataClient delegate to this layer
to minimize code duplication and ensure consistent behavior.
"""

from __future__ import annotations

import os
from typing import Any


class ApiEndpoints:
    """Centralized API endpoint configuration."""

    BASE_URL = "https://scraperapi.thordata.com"
    UNIVERSAL_URL = "https://webunlocker.thordata.com"
    API_URL = "https://openapi.thordata.com/api/web-scraper-api"
    LOCATIONS_URL = "https://openapi.thordata.com/api/locations"


class UrlBuilder:
    """Helper for building API URLs from base configuration."""

    @staticmethod
    def build_urls(
        scraperapi_base_url: str | None = None,
        universalapi_base_url: str | None = None,
        web_scraper_api_base_url: str | None = None,
        locations_base_url: str | None = None,
    ) -> dict[str, str]:
        """
        Build all API URLs from base configuration or defaults.

        Returns:
            Dict mapping URL keys to fully qualified URLs.
        """
        scraperapi_base = (
            scraperapi_base_url
            or os.getenv("THORDATA_SCRAPERAPI_BASE_URL")
            or ApiEndpoints.BASE_URL
        ).rstrip("/")

        universalapi_base = (
            universalapi_base_url
            or os.getenv("THORDATA_UNIVERSALAPI_BASE_URL")
            or ApiEndpoints.UNIVERSAL_URL
        ).rstrip("/")

        web_scraper_api_base = (
            web_scraper_api_base_url
            or os.getenv("THORDATA_WEB_SCRAPER_API_BASE_URL")
            or ApiEndpoints.API_URL
        ).rstrip("/")

        locations_base = (
            locations_base_url
            or os.getenv("THORDATA_LOCATIONS_BASE_URL")
            or ApiEndpoints.LOCATIONS_URL
        ).rstrip("/")

        # Determine shared API base from locations URL
        shared_api_base = locations_base.replace("/locations", "")

        whitelist_base = os.getenv(
            "THORDATA_WHITELIST_BASE_URL", "https://openapi.thordata.com/api"
        )

        proxy_api_base = os.getenv(
            "THORDATA_PROXY_API_BASE_URL", "https://openapi.thordata.com/api"
        )

        return {
            "serp": f"{scraperapi_base}/request",
            "builder": f"{scraperapi_base}/builder",
            "video_builder": f"{scraperapi_base}/video_builder",
            "universal": f"{universalapi_base}/request",
            "status": f"{web_scraper_api_base}/tasks-status",
            "download": f"{web_scraper_api_base}/tasks-download",
            "list": f"{web_scraper_api_base}/tasks-list",
            "locations": locations_base,
            "usage_stats": f"{shared_api_base}/account/usage-statistics",
            "proxy_users": f"{shared_api_base}/proxy-users",
            "whitelist": f"{whitelist_base}/whitelisted-ips",
            "proxy_list": f"{proxy_api_base}/proxy/proxy-list",
            "proxy_expiration": f"{proxy_api_base}/proxy/expiration-time",
            "gateway": os.getenv(
                "THORDATA_GATEWAY_BASE_URL", "https://openapi.thordata.com/api/gateway"
            ),
            "child": os.getenv(
                "THORDATA_CHILD_BASE_URL", "https://openapi.thordata.com/api/child"
            ),
        }


def validate_auth_mode(auth_mode: str) -> str:
    """
    Validate and normalize authentication mode.

    Args:
        auth_mode: Authentication mode string.

    Returns:
        Normalized lowercase mode.

    Raises:
        ValueError: If mode is invalid.
    """
    normalized = auth_mode.lower()
    if normalized not in ("bearer", "header_token"):
        raise ValueError(
            f"Invalid auth_mode: {auth_mode}. Must be 'bearer' or 'header_token'."
        )
    return normalized


def require_public_credentials(
    public_token: str | None,
    public_key: str | None,
) -> None:
    """
    Check that public API credentials are available.

    Raises:
        ValueError: If either token or key is missing.
    """
    if not public_token or not public_key:
        raise ValueError("public_token and public_key are required for this operation.")


def require_scraper_token(scraper_token: str | None, operation_name: str) -> None:
    """
    Check that scraper token is available.

    Args:
        scraper_token: The scraper token to check.
        operation_name: Name of the operation for error messages.

    Raises:
        ValueError: If scraper token is missing.
    """
    if not scraper_token:
        raise ValueError(f"scraper_token is required for {operation_name}")


def build_date_range_params(
    from_date: str | Any,
    to_date: str | Any,
) -> dict[str, str]:
    """
    Build date range parameters for API requests.

    Handles both string and date objects.

    Args:
        from_date: Start date (string or date object).
        to_date: End date (string or date object).

    Returns:
        Dict with from_date and to_date as strings.
    """
    if hasattr(from_date, "strftime"):
        from_date = from_date.strftime("%Y-%m-%d")
    if hasattr(to_date, "strftime"):
        to_date = to_date.strftime("%Y-%m-%d")

    return {"from_date": str(from_date), "to_date": str(to_date)}


def normalize_proxy_type(
    proxy_type: Any,
) -> int:
    """
    Normalize proxy type to integer.

    Args:
        proxy_type: ProxyType enum or int.

    Returns:
        Integer proxy type value.
    """
    if hasattr(proxy_type, "value"):
        return int(proxy_type.value)
    return int(proxy_type)


def build_auth_params(
    public_token: str,
    public_key: str,
    **extra_params: Any,
) -> dict[str, str]:
    """
    Build standard auth params for GET requests.

    Args:
        public_token: Public API token.
        public_key: Public API key.
        **extra_params: Additional parameters to include.

    Returns:
        Dict with token, key, and any extra params.
    """
    params = {
        "token": public_token,
        "key": public_key,
    }
    params.update({k: str(v) for k, v in extra_params.items()})
    return params


def format_ip_list_response(
    data: list[dict[str, Any]] | list[str] | dict[str, Any] | list,
) -> list[str]:
    """
    Normalize IP list from various API response formats.

    Args:
        data: Response data from IP list endpoints.

    Returns:
        List of IP address strings.
    """
    if isinstance(data, list):
        result = []
        for item in data:
            if isinstance(item, str):
                result.append(item)
            elif isinstance(item, dict) and "ip" in item:
                result.append(str(item["ip"]))
            else:
                result.append(str(item))
        return result

    if isinstance(data, dict) and "data" in data:
        return format_ip_list_response(data["data"])

    return []
