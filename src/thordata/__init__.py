# src/thordata/__init__.py

from .client import ThordataClient
from .async_client import AsyncThordataClient
from .enums import Engine, GoogleSearchType

# Package version
__version__ = "0.3.0"

# Explicitly export classes to simplify user imports
__all__ = [
    "ThordataClient", 
    "AsyncThordataClient", 
    "Engine", 
    "GoogleSearchType"
]