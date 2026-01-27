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
        """Github Repository Scraper by Repo URL"""

        SPIDER_ID = "github_repository_by-repo-url"
        SPIDER_NAME = "github.com"
        repo_url: str

    @dataclass
    class RepositoryBySearchUrl(ToolRequest):
        """Github Repository Scraper by Search URL"""

        SPIDER_ID = "github_repository_by-search-url"
        SPIDER_NAME = "github.com"
        search_url: str
        page_turning: int | None = None
        max_num: int | None = None

    @dataclass
    class RepositoryByUrl(ToolRequest):
        """Github Repository Scraper by URL"""

        SPIDER_ID = "github_repository_by-url"
        SPIDER_NAME = "github.com"
        url: str
