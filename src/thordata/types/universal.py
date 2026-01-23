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
    output_format: str = "html"  # 'html' or 'png'
    country: str | None = None
    block_resources: str | None = None  # 'script,image'
    clean_content: str | None = None  # 'js,css'
    wait: int | None = None  # ms
    wait_for: str | None = None  # selector

    # Headers/Cookies must be serialized to JSON in payload
    headers: list[dict[str, str]] | None = None
    cookies: list[dict[str, str]] | None = None

    extra_params: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        valid_formats = {"html", "png"}
        if self.output_format.lower() not in valid_formats:
            raise ValueError(
                f"Invalid output_format: {self.output_format}. Must be one of: {valid_formats}"
            )

        if self.wait is not None and (self.wait < 0 or self.wait > 100000):
            raise ValueError("wait must be between 0 and 100000 milliseconds")

    def to_payload(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "url": self.url,
            "js_render": "True" if self.js_render else "False",
            "type": self.output_format.lower(),
        }

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

        # Serialize complex objects as JSON strings
        if self.headers:
            payload["headers"] = json.dumps(self.headers)
        if self.cookies:
            payload["cookies"] = json.dumps(self.cookies)

        payload.update(self.extra_params)
        return payload
