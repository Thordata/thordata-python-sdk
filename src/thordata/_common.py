"""
Common utilities shared between sync and async clients.

This module reduces code duplication by extracting shared logic.
"""

from __future__ import annotations

from typing import Any

from .constants import APIBaseURL, APIEndpoint, EnvVar


def build_api_urls(
    scraperapi_base_url: str | None = None,
    universalapi_base_url: str | None = None,
    web_scraper_api_base_url: str | None = None,
    locations_base_url: str | None = None,
) -> dict[str, str]:
    """
    Build all API URLs from base URLs.

    This function centralizes URL construction logic to reduce duplication
    between sync and async clients.

    Args:
        scraperapi_base_url: Optional scraper API base URL.
        universalapi_base_url: Optional universal API base URL.
        web_scraper_api_base_url: Optional web scraper API base URL.
        locations_base_url: Optional locations API base URL.

    Returns:
        Dictionary of all API URLs.
    """
    import os

    # Resolve base URLs
    scraperapi_base = (
        scraperapi_base_url
        or os.getenv(EnvVar.SCRAPERAPI_BASE_URL)
        or APIBaseURL.SCRAPER_API
    ).rstrip("/")

    universalapi_base = (
        universalapi_base_url
        or os.getenv(EnvVar.UNIVERSALAPI_BASE_URL)
        or APIBaseURL.UNIVERSAL_API
    ).rstrip("/")

    web_scraper_api_base = (
        web_scraper_api_base_url
        or os.getenv(EnvVar.WEB_SCRAPER_API_BASE_URL)
        or APIBaseURL.WEB_SCRAPER_API
    ).rstrip("/")

    locations_base = (
        locations_base_url
        or os.getenv(EnvVar.LOCATIONS_BASE_URL)
        or APIBaseURL.LOCATIONS_API
    ).rstrip("/")

    gateway_base = os.getenv(EnvVar.GATEWAY_BASE_URL, APIBaseURL.GATEWAY_API)
    child_base = os.getenv(EnvVar.CHILD_BASE_URL, APIBaseURL.CHILD_API)
    whitelist_base = os.getenv(EnvVar.WHITELIST_BASE_URL, APIBaseURL.WHITELIST_API)
    proxy_api_base = os.getenv(EnvVar.PROXY_API_BASE_URL, APIBaseURL.PROXY_API)

    shared_api_base = locations_base.replace("/locations", "")

    return {
        "serp_url": f"{scraperapi_base}{APIEndpoint.SERP_REQUEST}",
        "builder_url": f"{scraperapi_base}{APIEndpoint.SERP_BUILDER}",
        "video_builder_url": f"{scraperapi_base}{APIEndpoint.SERP_VIDEO_BUILDER}",
        "universal_url": f"{universalapi_base}{APIEndpoint.UNIVERSAL_REQUEST}",
        "status_url": f"{web_scraper_api_base}{APIEndpoint.TASKS_STATUS}",
        "download_url": f"{web_scraper_api_base}{APIEndpoint.TASKS_DOWNLOAD}",
        "list_url": f"{web_scraper_api_base}{APIEndpoint.TASKS_LIST}",
        "locations_base_url": locations_base,
        "usage_stats_url": f"{shared_api_base}{APIEndpoint.USAGE_STATISTICS}",
        "proxy_users_url": f"{shared_api_base}{APIEndpoint.PROXY_USERS}",
        "whitelist_url": f"{whitelist_base}{APIEndpoint.WHITELIST_IPS}",
        "proxy_list_url": f"{proxy_api_base}{APIEndpoint.PROXY_LIST}",
        "proxy_expiration_url": f"{proxy_api_base}{APIEndpoint.PROXY_EXPIRATION_TIME}",
        "gateway_base_url": gateway_base,
        "child_base_url": child_base,
    }


def extract_error_from_response(
    response_data: dict[str, Any],
    default_message: str = "API request failed",
) -> tuple[str, int | None, int | None]:
    """
    Extract error information from API response.

    Args:
        response_data: The API response dictionary.
        default_message: Default error message if not found.

    Returns:
        Tuple of (message, status_code, code).
    """
    from ._utils import extract_error_message

    message = extract_error_message(response_data)
    if not message or message == str(response_data):
        message = default_message

    status_code = response_data.get("status_code")
    code = response_data.get("code")

    return message, status_code, code


def validate_credentials(
    scraper_token: str | None = None,
    public_token: str | None = None,
    public_key: str | None = None,
    *,
    require_scraper: bool = False,
    require_public: bool = False,
) -> None:
    """
    Validate credentials and raise appropriate errors.

    Args:
        scraper_token: Scraper API token.
        public_token: Public API token.
        public_key: Public API key.
        require_scraper: Whether scraper token is required.
        require_public: Whether public credentials are required.

    Raises:
        ThordataConfigError: If required credentials are missing.
    """
    from .constants import ErrorMessage
    from .exceptions import ThordataConfigError

    if require_scraper and not scraper_token:
        raise ThordataConfigError(ErrorMessage.SCRAPER_TOKEN_REQUIRED)

    if require_public and (not public_token or not public_key):
        raise ThordataConfigError(ErrorMessage.PUBLIC_CREDENTIALS_REQUIRED)


__all__ = ["build_api_urls", "extract_error_from_response", "validate_credentials"]
