#!/usr/bin/env python
"""
Generate a Web Scraper tool coverage matrix from the live SDK registry.

This script does NOT rely on sdk-spec; it introspects the actual
`thordata.tools` namespace and writes a Markdown table grouped by tool group.

Output:
    docs/TOOL_COVERAGE_MATRIX.generated.md

Usage:
    python -m scripts.generate_tool_coverage_matrix
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from thordata._tools_registry import list_tools_metadata


def _format_row(meta: dict[str, Any]) -> str:
    """Format a single tool metadata row as Markdown."""
    spider_id = meta.get("spider_id") or ""
    spider_name = meta.get("spider_name") or ""
    key = meta.get("key") or ""
    class_name = meta.get("class_name") or ""
    module = meta.get("module") or ""
    fields: list[dict[str, Any]] = meta.get("fields") or []
    video = bool(meta.get("video"))

    params = ", ".join(f"{f['name']}" for f in fields) if fields else ""

    video_flag = "video" if video else ""

    return f"| `{spider_id}` | `{spider_name}` | `{key}` | `{class_name}` | `{module}` | {params} | {video_flag} |"


def main() -> None:
    tools, group_counts = list_tools_metadata()

    # Sort by group then by spider_id
    tools_sorted = sorted(
        tools,
        key=lambda m: (
            (m.get("group") or "default"),
            (m.get("spider_id") or ""),
        ),
    )

    lines: list[str] = []
    lines.append("# Thordata Web Scraper Tool Coverage (Generated)\n")
    lines.append("> This file is generated from the live Python SDK registry.\n")
    lines.append(
        "> Do not edit manually. Re-generate via `python -m scripts.generate_tool_coverage_matrix`.\n"
    )
    lines.append("")
    lines.append("## Summary\n")
    total = len(tools_sorted)
    lines.append(f"- Total tools: **{total}**")
    for group, count in sorted(group_counts.items()):
        lines.append(f"- **{group}**: {count}")
    lines.append("")

    current_group = None
    for meta in tools_sorted:
        group = meta.get("group") or "default"
        if group != current_group:
            current_group = group
            lines.append("")
            lines.append(f"## Group: `{group}`\n")
            lines.append(
                "| spider_id | spider_name | key | class | module | params | type |"
            )
            lines.append(
                "|-----------|------------|-----|-------|--------|--------|------|"
            )

        lines.append(_format_row(meta))

    out_path = (
        Path(__file__).resolve().parent.parent
        / "docs"
        / "TOOL_COVERAGE_MATRIX.generated.md"
    )
    out_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote tool coverage matrix to {out_path}")


if __name__ == "__main__":
    main()
