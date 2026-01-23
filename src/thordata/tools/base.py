"""
Base classes for Web Scraper Tools.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, ClassVar


@dataclass
class ToolRequest:
    """Base class for standard scraping tools."""

    # These must be defined in subclasses
    SPIDER_ID: ClassVar[str]
    SPIDER_NAME: ClassVar[str]

    def to_task_parameters(self) -> dict[str, Any]:
        """Convert dataclass fields to API parameters dict."""
        # Filter out internal fields and None values
        return {
            k: v
            for k, v in asdict(self).items()
            if v is not None and k != "common_settings"
        }

    def get_spider_id(self) -> str:
        return self.SPIDER_ID

    def get_spider_name(self) -> str:
        return self.SPIDER_NAME


@dataclass
class VideoToolRequest(ToolRequest):
    """
    Marker class for Video/Audio tools that use the /video_builder endpoint.
    Concrete classes must define a 'common_settings' field.
    """

    pass
