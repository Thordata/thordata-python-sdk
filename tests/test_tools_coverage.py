from __future__ import annotations

import dataclasses
import inspect
import os
from collections.abc import Iterable
from dataclasses import is_dataclass
from typing import Any

import pytest

from thordata.tools.base import ToolRequest


def _is_integration_enabled() -> bool:
    return os.getenv("THORDATA_INTEGRATION", "").lower() in {"1", "true", "yes"}


def _iter_tool_request_classes() -> Iterable[type[ToolRequest]]:
    # Import here to avoid expensive imports at collection time in some envs
    import thordata.tools as tools_module

    for _, obj in inspect.getmembers(tools_module):
        # Namespace containers like Amazon/GoogleMaps/TikTok/YouTube
        if inspect.isclass(obj):
            for _, inner in inspect.getmembers(obj):
                if inspect.isclass(inner) and issubclass(inner, ToolRequest):
                    if inner is ToolRequest:
                        continue
                    if not is_dataclass(inner):
                        continue
                    yield inner


def _build_min_instance(cls: type[ToolRequest]) -> ToolRequest:
    # Heuristic: fill required fields with safe placeholders.
    # This is contract/serialization testing, not live crawling.
    kwargs: dict[str, Any] = {}
    for f in getattr(cls, "__dataclass_fields__", {}).values():
        # Skip internal/class constants accidentally captured as dataclass fields
        if f.name in {"common_settings", "SPIDER_ID", "SPIDER_NAME"}:
            continue

        # required if no default (dataclasses uses MISSING sentinel)
        required = (
            f.default is dataclasses.MISSING
            and f.default_factory is dataclasses.MISSING
        )
        if not required:
            continue

        name = f.name.lower()
        if "job_listing_url" in name:
            kwargs[f.name] = "https://www.linkedin.com/jobs/view/0"
        elif name == "location":
            kwargs[f.name] = "United States"
        elif "profileurl" in name or "posturl" in name:
            kwargs[f.name] = "https://example.com"
        elif "app_url" in name:
            kwargs[f.name] = (
                "https://play.google.com/store/apps/details?id=com.spotify.music"
            )
        elif "url" in name:
            kwargs[f.name] = "https://example.com"
        elif "asin" in name:
            kwargs[f.name] = "B000000000"
        elif "keyword" in name or "query" in name:
            kwargs[f.name] = "test"
        elif "video_id" in name or name.endswith("id"):
            kwargs[f.name] = "dQw4w9WgXcQ"
        elif "username" in name or name == "user_name" or name.endswith("username"):
            kwargs[f.name] = "test"
        elif "country" in name:
            kwargs[f.name] = "US"
        elif "domain" in name:
            kwargs[f.name] = "amazon.com"
        else:
            kwargs[f.name] = "test"

    return cls(**kwargs)  # type: ignore[call-arg]


TOOL_CLASSES = list(_iter_tool_request_classes())


@pytest.mark.parametrize("tool_cls", TOOL_CLASSES)
def test_tool_contract_serialization(tool_cls: type[ToolRequest]) -> None:
    tool = _build_min_instance(tool_cls)

    assert tool.get_spider_id()
    assert tool.get_spider_name()

    params = tool.to_task_parameters()
    assert isinstance(params, dict)
    assert params

    # Ensure no None values leak
    assert all(v is not None for v in params.values())

    # Integration/live crawling is validated via acceptance scripts.
    if not _is_integration_enabled():
        return
