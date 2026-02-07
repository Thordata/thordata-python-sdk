"""
Internal helpers for discovering and working with Web Scraper tools.

These functions are intentionally kept **internal** (underscore-prefixed
module name) so that we can evolve the public API surface in `client`
and `async_client` without exposing the full reflection logic.

This module uses caching to avoid repeated reflection overhead.
"""

from __future__ import annotations

import dataclasses
import inspect
from collections.abc import Iterable
from dataclasses import is_dataclass
from typing import Any

from .tools import ToolRequest, VideoToolRequest

# Cache for tool classes and metadata
_tools_classes_cache: list[type[ToolRequest]] | None = None
_tools_metadata_cache: dict[str, list[dict[str, Any]]] = {}
_tools_key_map: dict[str, type[ToolRequest]] = {}
_tools_spider_map: dict[str, list[str]] = {}


def _clear_cache() -> None:
    """Clear the tools registry cache. Useful for testing."""
    global _tools_classes_cache, _tools_metadata_cache, _tools_key_map, _tools_spider_map
    _tools_classes_cache = None
    _tools_metadata_cache.clear()
    _tools_key_map.clear()
    _tools_spider_map.clear()


def _iter_tool_classes() -> Iterable[type[ToolRequest]]:
    """
    Iterate over all ToolRequest subclasses that are exported from
    the `thordata.tools` namespace.

    This relies on `thordata.tools.__all__` and skips the base classes.

    Uses caching to avoid repeated reflection overhead.
    """
    global _tools_classes_cache

    if _tools_classes_cache is not None:
        return iter(_tools_classes_cache)

    from . import tools  # local import to avoid cycles at module import time

    all_classes: list[type[ToolRequest]] = []

    for name in getattr(tools, "__all__", []):
        obj = getattr(tools, name, None)
        if obj is None:
            continue

        # Direct ToolRequest subclass exported in __all__
        if inspect.isclass(obj) and issubclass(obj, ToolRequest):
            if obj not in (ToolRequest, VideoToolRequest):
                all_classes.append(obj)
            continue

        # Namespace-style container (e.g. Amazon, GoogleMaps, etc.)
        if inspect.isclass(obj):
            for _attr_name, attr_val in inspect.getmembers(obj):
                if (
                    inspect.isclass(attr_val)
                    and issubclass(attr_val, ToolRequest)
                    and attr_val not in (ToolRequest, VideoToolRequest)
                ):
                    all_classes.append(attr_val)

    _tools_classes_cache = all_classes
    return iter(all_classes)


def _tool_group_from_class(cls: type[ToolRequest]) -> str:
    """
    Derive a simple group identifier from the tool class module path.

    Examples:
        thordata.tools.ecommerce.Amazon.ProductByUrl -> "ecommerce"
        thordata.tools.social.Twitter.Post          -> "social"
    """
    module = getattr(cls, "__module__", "") or ""
    parts = module.split(".")
    try:
        idx = parts.index("tools")
    except ValueError:
        return "default"
    if idx + 1 < len(parts):
        return parts[idx + 1]
    return "default"


def _tool_key_from_class(cls: type[ToolRequest]) -> str:
    """
    Build a stable key for a ToolRequest subclass.

    Pattern: "<group>.<spider_id>"
    Fallback: lower-cased class name when SPIDER_ID is missing.
    """
    group = _tool_group_from_class(cls)
    spider_id = getattr(cls, "SPIDER_ID", "") or ""
    if not spider_id:
        spider_id = cls.__name__.lower()
    return f"{group}.{spider_id}"


def _tool_schema(cls: type[ToolRequest]) -> dict[str, Any]:
    """
    Build a lightweight schema dict for a ToolRequest subclass.

    This is intentionally kept small and LLM / UX friendly.
    """
    fields: list[dict[str, Any]] = []
    if is_dataclass(cls):
        # __dataclass_fields__ is present on dataclass types; we keep this defensive
        # access to avoid mypy/runtime issues.
        for f in getattr(cls, "__dataclass_fields__", {}).values():  # type: ignore[attr-defined]
            # Skip private/internal fields and synthetic constants.
            if f.name.startswith("_") or f.name in {
                "SPIDER_ID",
                "SPIDER_NAME",
                "common_settings",
            }:
                continue

            # Map dataclass default semantics to a simple JSON-friendly value.
            default: Any = None
            if f.default is not dataclasses.MISSING:
                default = f.default
            elif getattr(f, "default_factory", dataclasses.MISSING) is not dataclasses.MISSING:  # type: ignore[attr-defined]
                # We intentionally do *not* call default_factory to avoid side effects;
                # callers only need to know that a default exists.
                default = None

            fields.append(
                {
                    "name": f.name,
                    "type": str(f.type),
                    "default": default,
                }
            )

    return {
        "key": _tool_key_from_class(cls),
        "group": _tool_group_from_class(cls),
        "spider_id": getattr(cls, "SPIDER_ID", None),
        "spider_name": getattr(cls, "SPIDER_NAME", None),
        "class_name": cls.__name__,
        "module": getattr(cls, "__module__", None),
        "fields": fields,
        "video": issubclass(cls, VideoToolRequest),
    }


def list_tools_metadata(
    *,
    group: str | None = None,
    keyword: str | None = None,
) -> tuple[list[dict[str, Any]], dict[str, int]]:
    """
    Return a list of tool metadata dicts and a simple group count mapping.

    Args:
        group: Optional group filter (e.g. "ecommerce", "social")
        keyword: Optional keyword to match in key/spider_id/spider_name

    Returns:
        Tuple of (tools list, group counts dict)
    """
    all_tools: list[type[ToolRequest]] = list(_iter_tool_classes())
    out: list[dict[str, Any]] = []
    group_counts: dict[str, int] = {}

    group_norm = group.lower().strip() if group else None
    kw_norm = keyword.lower().strip() if keyword else None

    for cls in all_tools:
        meta = _tool_schema(cls)
        g = meta["group"] or "default"
        k = meta["key"] or ""
        spider_id = (meta.get("spider_id") or "") or ""
        spider_name = (meta.get("spider_name") or "") or ""

        if group_norm and g != group_norm:
            continue
        if kw_norm:
            haystack = f"{k} {spider_id} {spider_name}".lower()
            if kw_norm not in haystack:
                continue

        out.append(meta)
        group_counts[g] = group_counts.get(g, 0) + 1

    return out, group_counts


def get_tool_class_by_key(tool_key: str) -> type[ToolRequest]:
    """
    Resolve a ToolRequest subclass by its key.

    Pattern:
        "<group>.<spider_id>"

    Uses caching to avoid repeated class lookups.
    """
    global _tools_key_map

    # Build cache if empty
    if not _tools_key_map:
        for cls in _iter_tool_classes():
            key = _tool_key_from_class(cls).lower()
            _tools_key_map[key] = cls

    canonical = resolve_tool_key(tool_key).lower()
    cls = _tools_key_map.get(canonical)

    if cls is None:
        raise KeyError(f"Unknown tool key: {tool_key!r}")
    return cls


def resolve_tool_key(tool_key: str) -> str:
    """
    Resolve a tool key into its canonical form "<group>.<spider_id>".

    Accepts:
      - canonical key: "ecommerce.amazon_product_by-url"
      - raw spider_id: "amazon_product_by-url" (must be unique across all tools)

    Uses caching to avoid repeated lookups.

    Raises:
      - KeyError if unknown
      - KeyError with candidates if ambiguous
    """
    global _tools_spider_map

    raw = (tool_key or "").strip()
    if not raw:
        raise KeyError("Tool key is empty")

    raw_norm = raw.lower()

    # Build cache if empty
    if not _tools_spider_map:
        for cls in _iter_tool_classes():
            canonical = _tool_key_from_class(cls)
            spider_id = (getattr(cls, "SPIDER_ID", "") or "").lower()
            if spider_id:
                _tools_spider_map.setdefault(spider_id, []).append(canonical)

    # 1) canonical form
    if "." in raw_norm:
        # Direct lookup in key map
        canonical = get_tool_class_by_key(tool_key)
        return _tool_key_from_class(canonical)

    # 2) raw spider_id
    cands = _tools_spider_map.get(raw_norm) or []
    if len(cands) == 1:
        return cands[0]
    if len(cands) > 1:
        # ambiguous spider_id (rare, but possible)
        cands_s = ", ".join(sorted(cands)[:10])
        raise KeyError(f"Ambiguous tool key {tool_key!r}. Candidates: {cands_s}")

    raise KeyError(f"Unknown tool key: {tool_key!r}")


def get_tool_info(tool_key: str) -> dict[str, Any]:
    """
    Return tool metadata (schema) by tool key or raw spider_id.
    """
    cls = get_tool_class_by_key(tool_key)
    return _tool_schema(cls)
