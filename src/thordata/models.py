"""
Data models for the Thordata Python SDK.
Moved to thordata.types in v1.6.0.
This file is kept for backward compatibility.
"""

from .types.common import CommonSettings
from .types.proxy import (
    ProxyConfig,
    ProxyProduct,
    ProxyServer,
    ProxyUser,
    ProxyUserList,
    StaticISPProxy,
    StickySession,
)
from .types.serp import SerpRequest
from .types.task import (
    ScraperTaskConfig,
    TaskStatusResponse,
    UsageStatistics,
    VideoTaskConfig,
)
from .types.universal import UniversalScrapeRequest

__all__ = [
    "ProxyProduct",
    "ProxyConfig",
    "StickySession",
    "StaticISPProxy",
    "ProxyUser",
    "ProxyUserList",
    "ProxyServer",
    "SerpRequest",
    "UniversalScrapeRequest",
    "ScraperTaskConfig",
    "CommonSettings",
    "VideoTaskConfig",
    "TaskStatusResponse",
    "UsageStatistics",
]
