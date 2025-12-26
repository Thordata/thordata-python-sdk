"""
Thordata Python SDK

Official Python client for Thordata's Proxy Network, SERP API,
Universal Scraping API (Web Unlocker), and Web Scraper API.

Basic Usage:
    >>> from thordata import ThordataClient
    >>>
    >>> client = ThordataClient(
    ...     scraper_token="your_token",
    ...     public_token="your_public_token",
    ...     public_key="your_public_key"
    ... )
    >>>
    >>> # Proxy request
    >>> response = client.get("https://httpbin.org/ip")
    >>>
    >>> # SERP search
    >>> results = client.serp_search("python tutorial", engine="google")
    >>>
    >>> # Universal scrape
    >>> html = client.universal_scrape("https://example.com", js_render=True)

Async Usage:
    >>> from thordata import AsyncThordataClient
    >>> import asyncio
    >>>
    >>> async def main():
    ...     async with AsyncThordataClient(
    ...         scraper_token="your_token"
    ...     ) as client:
    ...         response = await client.get("https://httpbin.org/ip")
    >>>
    >>> asyncio.run(main())
"""

__version__ = "0.8.0"
__author__ = "Thordata Developer Team"
__email__ = "support@thordata.com"

# Main clients
from .async_client import AsyncThordataClient
from .client import ThordataClient

# Enums
from .enums import (
    BingSearchType,
    Continent,
    Country,
    DataFormat,
    Device,
    Engine,
    GoogleSearchType,
    GoogleTbm,
    OutputFormat,
    ProxyHost,
    ProxyPort,
    ProxyType,
    SessionType,
    TaskStatus,
    TimeRange,
)

# Exceptions
from .exceptions import (
    ThordataAPIError,
    ThordataAuthError,
    ThordataConfigError,
    ThordataError,
    ThordataNetworkError,
    ThordataNotCollectedError,
    ThordataRateLimitError,
    ThordataServerError,
    ThordataTimeoutError,
    ThordataValidationError,
)

# Models
from .models import (
    CommonSettings,
    ProxyConfig,
    ProxyProduct,
    ProxyServer,
    ProxyUser,
    ProxyUserList,
    ScraperTaskConfig,
    SerpRequest,
    StaticISPProxy,
    StickySession,
    TaskStatusResponse,
    UniversalScrapeRequest,
    UsageStatistics,
    VideoTaskConfig,
)

# Retry utilities
from .retry import RetryConfig

# Public API
__all__ = [
    # Version
    "__version__",
    # Clients
    "ThordataClient",
    "AsyncThordataClient",
    # Enums
    "Engine",
    "GoogleSearchType",
    "BingSearchType",
    "ProxyType",
    "SessionType",
    "Continent",
    "Country",
    "OutputFormat",
    "DataFormat",
    "TaskStatus",
    "Device",
    "TimeRange",
    "ProxyHost",
    "ProxyPort",
    "GoogleTbm",
    # Models
    "ProxyConfig",
    "ProxyProduct",
    "ProxyServer",
    "ProxyUser",
    "ProxyUserList",
    "UsageStatistics",
    "StaticISPProxy",
    "StickySession",
    "SerpRequest",
    "UniversalScrapeRequest",
    "ScraperTaskConfig",
    "CommonSettings",
    "VideoTaskConfig",
    "TaskStatusResponse",
    # Exceptions
    "ThordataError",
    "ThordataConfigError",
    "ThordataNetworkError",
    "ThordataTimeoutError",
    "ThordataAPIError",
    "ThordataAuthError",
    "ThordataRateLimitError",
    "ThordataServerError",
    "ThordataValidationError",
    "ThordataNotCollectedError",
    # Retry
    "RetryConfig",
]
