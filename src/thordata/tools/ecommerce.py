"""
E-Commerce Scraper Tools (Amazon, etc.)
"""

from __future__ import annotations

from dataclasses import dataclass

from .base import ToolRequest


class Amazon:
    """Namespace for Amazon tools."""

    @dataclass
    class Product(ToolRequest):
        """Amazon Product Details Scraper"""

        SPIDER_ID = "amazon_product_by-asin"
        SPIDER_NAME = "amazon.com"

        asin: str
        domain: str = "amazon.com"

    @dataclass
    class GlobalProduct(ToolRequest):
        """Amazon Global Product Details Scraper"""

        SPIDER_ID = "amazon_global-product_by-url"
        SPIDER_NAME = "amazon.com"

        url: str
        zip_code: str | None = None

    @dataclass
    class Review(ToolRequest):
        """Amazon Product Review Scraper"""

        SPIDER_ID = "amazon_comment_by-url"
        SPIDER_NAME = "amazon.com"

        url: str
        page_turning: int = 1

    @dataclass
    class Seller(ToolRequest):
        """Amazon Seller Information Scraper"""

        SPIDER_ID = "amazon_seller_by-url"
        SPIDER_NAME = "amazon.com"

        url: str

    @dataclass
    class Search(ToolRequest):
        """Amazon Product Listing Scraper"""

        SPIDER_ID = "amazon_product-list_by-keywords-domain"
        SPIDER_NAME = "amazon.com"

        keyword: str
        domain: str = "amazon.com"
        page_turning: int = 1
        sort_by: str | None = None  # Best Sellers, Newest Arrivals, etc.
        min_price: float | None = None
        max_price: float | None = None
        get_sponsored: bool | None = None
