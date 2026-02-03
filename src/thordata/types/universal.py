"""
Universal Scraping (Web Unlocker) types.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any

from .common import ThordataBaseConfig


@dataclass
class UniversalScrapeRequest(ThordataBaseConfig):
    url: str
    js_render: bool = False
    output_format: str | list[str] = (
        "html"  # 'html', 'png', or ['png', 'html'] for both
    )
    country: str | None = None
    block_resources: str | None = None  # 'script,image,video'
    clean_content: str | None = None  # 'js,css'
    wait: int | None = None  # ms
    wait_for: str | None = None  # selector
    follow_redirect: bool | None = None  # Follow redirects

    # Headers/Cookies must be serialized to JSON in payload
    headers: list[dict[str, str]] | None = None
    cookies: list[dict[str, str]] | None = None

    extra_params: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        # Normalize output_format to list for easier handling
        if isinstance(self.output_format, str):
            formats = [f.strip().lower() for f in self.output_format.split(",")]
        else:
            formats = [
                f.lower() if isinstance(f, str) else str(f).lower()
                for f in self.output_format
            ]

        valid_formats = {"html", "png"}
        invalid = [f for f in formats if f not in valid_formats]
        if invalid:
            raise ValueError(
                f"Invalid output_format: {invalid}. Must be one or more of: {valid_formats}. "
                f"Use comma-separated string like 'png,html' or list ['png', 'html'] for multiple formats."
            )

        # Store as list for to_payload
        self._output_formats = formats

        if self.wait is not None and (self.wait < 0 or self.wait > 100000):
            raise ValueError("wait must be between 0 and 100000 milliseconds")

    def to_payload(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "url": self.url,
            "js_render": "True" if self.js_render else "False",
        }

        # Handle output format: support single or multiple formats (e.g., "png,html")
        if hasattr(self, "_output_formats") and self._output_formats:
            if len(self._output_formats) == 1:
                payload["type"] = self._output_formats[0]
            else:
                # Multiple formats: join with comma (e.g., "png,html")
                payload["type"] = ",".join(self._output_formats)
        else:
            # Fallback for backward compatibility
            if isinstance(self.output_format, str):
                payload["type"] = self.output_format.lower()
            else:
                payload["type"] = ",".join([str(f).lower() for f in self.output_format])

        if self.country:
            payload["country"] = self.country.lower()
        if self.block_resources:
            payload["block_resources"] = self.block_resources
        if self.clean_content:
            payload["clean_content"] = self.clean_content
        if self.wait is not None:
            payload["wait"] = str(self.wait)
        if self.wait_for:
            payload["wait_for"] = self.wait_for
        if self.follow_redirect is not None:
            payload["follow_redirect"] = "True" if self.follow_redirect else "False"

        # Serialize complex objects as JSON strings
        if self.headers:
            payload["headers"] = json.dumps(self.headers)
        if self.cookies:
            payload["cookies"] = json.dumps(self.cookies)

        payload.update(self.extra_params)
        return payload
