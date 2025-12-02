# src/thordata/__init__.py

from .client import ThordataClient
from .async_client import AsyncThordataClient
from .enums import Engine, GoogleSearchType
from .exceptions import (
    ThordataError,
    ThordataAPIError,
    ThordataAuthError,
    ThordataRateLimitError,
)

# Package version
__version__ = "0.3.1"

# Explicitly export classes to simplify user imports
__all__ = [
    "ThordataClient",
    "AsyncThordataClient",
    "Engine",
    "ThordataError",
    "ThordataAPIError",
    "ThordataAuthError",
    "ThordataRateLimitError",
    "GoogleSearchType"
]