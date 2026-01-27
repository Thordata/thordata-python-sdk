"""
Travel & Real Estate Scraper Tools (Booking, Zillow, Airbnb)
"""

from __future__ import annotations

from dataclasses import dataclass

from .base import ToolRequest


class Booking:
    """Namespace for Booking.com tools."""

    @dataclass
    class HotelByUrl(ToolRequest):
        """Booking Hotel Information Scraper by URL"""

        SPIDER_ID = "booking_hotellist_by-url"
        SPIDER_NAME = "booking.com"
        url: str


class Zillow:
    """Namespace for Zillow tools."""

    @dataclass
    class PriceByUrl(ToolRequest):
        """Zillow Property Price History Information Scraper by URL"""

        SPIDER_ID = "zillow_price_by-url"
        SPIDER_NAME = "zillow.com"
        url: str

    @dataclass
    class ProductByUrl(ToolRequest):
        """Zillow Property Details Information Scraper by URL"""

        SPIDER_ID = "zillow_product_by-url"
        SPIDER_NAME = "zillow.com"
        url: str

    @dataclass
    class ProductByFilter(ToolRequest):
        """Zillow Property Details Information Scraper by Filter"""

        SPIDER_ID = "zillow_product_by-filter"
        SPIDER_NAME = "zillow.com"
        keywords_location: str
        listingCategory: str | None = None  # For Rent, For Sale
        HomeType: str | None = None  # Houses
        days_on_zillow: str | None = None  # Any
        maximum: int | None = None

    @dataclass
    class ProductByListUrl(ToolRequest):
        """Zillow Property Details Information Scraper by List URL"""

        SPIDER_ID = "zillow_product_by-listurl"
        SPIDER_NAME = "zillow.com"
        url: str
        maximum: int | None = None


class Airbnb:
    """Namespace for Airbnb tools."""

    @dataclass
    class ProductBySearchUrl(ToolRequest):
        """Airbnb Properties Information Scraper by Search URL"""

        SPIDER_ID = "airbnb_product_by-searchurl"
        SPIDER_NAME = "airbnb.com"
        searchurl: str
        country: str | None = None

    @dataclass
    class ProductByLocation(ToolRequest):
        """Airbnb Properties Information Scraper by Location"""

        SPIDER_ID = "airbnb_product_by-location"
        SPIDER_NAME = "airbnb.com"
        location: str
        check_in: str | None = None
        check_out: str | None = None
        num_of_adults: str | None = None
        num_of_children: str | None = None
        num_of_infants: str | None = None
        num_of_pets: str | None = None
        country: str | None = None
        currency: str | None = None

    @dataclass
    class ProductByUrl(ToolRequest):
        """Airbnb Properties Information Scraper by URL"""

        SPIDER_ID = "airbnb_product_by-url"
        SPIDER_NAME = "airbnb.com"
        url: str
        country: str | None = None
