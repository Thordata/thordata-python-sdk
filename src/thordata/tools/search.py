"""
Search Engine & Map Scraper Tools (Google, etc.)
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from .base import ToolRequest


class GoogleMaps:
    """Namespace for Google Maps tools."""

    @dataclass
    class Details(ToolRequest):
        """Google Maps Details Information Scraper"""

        SPIDER_ID = "google_map-details_by-url"
        SPIDER_NAME = "google.com"

        url: str  # Google Maps URL

    @dataclass
    class Reviews(ToolRequest):
        """Google Maps Review Information Scraper"""

        SPIDER_ID = "google_comment_by-url"
        SPIDER_NAME = "google.com"

        url: str
        days_limit: Optional[int] = None  # Crawl reviews within X days


class GoogleShopping:
    """Namespace for Google Shopping tools."""

    @dataclass
    class Product(ToolRequest):
        """Google Shopping Information Scraper"""

        SPIDER_ID = "google_shopping_by-url"
        SPIDER_NAME = "google.com"

        url: str
        country: Optional[str] = None  # e.g. "US"


class GooglePlay:
    """Namespace for Google Play Store tools."""

    @dataclass
    class AppInfo(ToolRequest):
        """Google Play Store Information Scraper"""

        SPIDER_ID = "google-play-store_information_by-url"
        SPIDER_NAME = "google.com"

        app_url: str
        country: Optional[str] = None

    @dataclass
    class Reviews(ToolRequest):
        """Google Play Store Reviews Scraper"""

        SPIDER_ID = "google-play-store_reviews_by-url"
        SPIDER_NAME = "google.com"

        app_url: str
        num_of_reviews: Optional[int] = None
        start_date: Optional[str] = None  # yyyy-mm-dd
        end_date: Optional[str] = None
        country: Optional[str] = None
