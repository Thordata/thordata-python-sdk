"""
Code Repository Scraper Tools (GitHub, etc.)
"""

from __future__ import annotations

from dataclasses import dataclass

from .base import ToolRequest


class GitHub:
    """Namespace for GitHub tools."""

    @dataclass
    class Repository(ToolRequest):
        """Github Repository Scraper"""

        SPIDER_ID = "github_repository_by-repo-url"
        SPIDER_NAME = "github.com"

        repo_url: str
        search_url: str | None = None
        url: str | None = None  # The generic URL param
        page_turning: int | None = None
        max_num: int | None = None
