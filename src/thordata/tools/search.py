"""
Search Engine & Map Scraper Tools (Google, etc.)
"""

from __future__ import annotations

from dataclasses import dataclass

from .base import ToolRequest


class GoogleMaps:
    """Namespace for Google Maps tools."""

    @dataclass
    class DetailsByUrl(ToolRequest):
        """Google Maps Details Scraper by URL."""

        SPIDER_ID = "google_map-details_by-url"
        SPIDER_NAME = "google.com"

        url: str

    @dataclass
    class DetailsByCid(ToolRequest):
        """Google Maps Details Scraper by CID."""

        SPIDER_ID = "google_map-details_by-cid"
        SPIDER_NAME = "google.com"

        CID: str

    @dataclass
    class DetailsByLocation(ToolRequest):
        """Google Maps Details Scraper by Location keyword + country (+ optional lat/long/zoom)."""  # noqa: E501

        SPIDER_ID = "google_map-details_by-location"
        SPIDER_NAME = "google.com"

        country: str
        keyword: str
        lat: str | None = None
        long: str | None = None
        zoom_level: str | None = None

    @dataclass
    class DetailsByPlaceId(ToolRequest):
        """Google Maps Details Scraper by Place ID."""

        SPIDER_ID = "google_map-details_by-placeid"
        SPIDER_NAME = "google.com"

        place_id: str

    # Backward compatible alias: keep old name working
    Details = DetailsByUrl

    @dataclass
    class Reviews(ToolRequest):
        """Google Maps Review Information Scraper"""

        SPIDER_ID = "google_comment_by-url"
        SPIDER_NAME = "google.com"

        url: str
        days_limit: int | None = None  # Crawl reviews within X days


class GoogleShopping:
    """Namespace for Google Shopping tools."""

    @dataclass
    class Product(ToolRequest):
        """Google Shopping Information Scraper by URL"""

        SPIDER_ID = "google_shopping_by-url"
        SPIDER_NAME = "google.com"
        url: str
        country: str | None = None  # e.g. "US"

    @dataclass
    class ProductByKeywords(ToolRequest):
        """Google Shopping Information Scraper by Keywords"""

        SPIDER_ID = "google_shopping_by-keywords"
        SPIDER_NAME = "google.com"
        keyword: str
        country: str | None = None  # e.g. "US"


class GooglePlay:
    """Namespace for Google Play Store tools."""

    @dataclass
    class AppInfo(ToolRequest):
        """Google Play Store Information Scraper"""

        SPIDER_ID = "google-play-store_information_by-url"
        SPIDER_NAME = "google.com"

        app_url: str
        country: str | None = None

    @dataclass
    class Reviews(ToolRequest):
        """Google Play Store Reviews Scraper"""

        SPIDER_ID = "google-play-store_reviews_by-url"
        SPIDER_NAME = "google.com"

        app_url: str
        num_of_reviews: int | None = None
        start_date: str | None = None  # yyyy-mm-dd
        end_date: str | None = None
        country: str | None = None
