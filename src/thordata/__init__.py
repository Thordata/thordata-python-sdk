"""
Thordata Python SDK

Official Python client for Thordata's Proxy Network, SERP API,
Universal Scraping API (Web Unlocker), and Web Scraper API.
"""

__version__ = "1.8.4"
__author__ = "Thordata Developer Team/Kael Odin"
__email__ = "support@thordata.com"

# Main clients
from .async_client import AsyncThordataClient
from .client import ThordataClient

# Constants (for advanced usage)
from .constants import (
    APIBaseURL,
    APIEndpoint,
    APIErrorCode,
    AuthMode,
    ContentType,
    EnvVar,
    ErrorMessage,
    HTTPMethod,
    HTTPStatus,
    RequestKey,
    ResponseKey,
)
from .constants import (
    TaskStatus as TaskStatusConstant,
)

# Enums (Legacy Import Path)
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

# Env helpers (optional, no side effects unless called)
from .env import load_env_file

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

# Models (Legacy Import Path)
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

# Response wrapper
from .response import APIResponse

# Retry utilities
from .retry import RetryConfig

# Public API
__all__ = [
    "__version__",
    "ThordataClient",
    "AsyncThordataClient",
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
    "RetryConfig",
    "load_env_file",
    # Constants
    "APIBaseURL",
    "APIEndpoint",
    "APIErrorCode",
    "AuthMode",
    "ContentType",
    "EnvVar",
    "ErrorMessage",
    "HTTPMethod",
    "HTTPStatus",
    "RequestKey",
    "ResponseKey",
    "TaskStatusConstant",
    # Response wrapper
    "APIResponse",
]
