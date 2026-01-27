"""
E-Commerce Scraper Tools (Amazon, etc.)
"""

from __future__ import annotations

from dataclasses import dataclass

from .base import ToolRequest


class Amazon:
    """Namespace for Amazon tools."""

    # --- Product Details (5 methods) ---
    @dataclass
    class ProductByAsin(ToolRequest):
        """Amazon Product Details Scraper by ASIN."""

        SPIDER_ID = "amazon_product_by-asin"
        SPIDER_NAME = "amazon.com"

        asin: str
        domain: str = "amazon.com"

    # Backward compatible alias
    Product = ProductByAsin

    @dataclass
    class ProductByUrl(ToolRequest):
        """Amazon Product Details Scraper by URL."""

        SPIDER_ID = "amazon_product_by-url"
        SPIDER_NAME = "amazon.com"

        url: str
        zip_code: str | None = None

    @dataclass
    class ProductByKeywords(ToolRequest):
        """Amazon Product Details Scraper by Keywords."""

        SPIDER_ID = "amazon_product_by-keywords"
        SPIDER_NAME = "amazon.com"

        keyword: str
        page_turning: int | None = None
        lowest_price: float | None = None
        highest_price: float | None = None

    @dataclass
    class ProductByCategoryUrl(ToolRequest):
        """Amazon Product Details Scraper by Category URL."""

        SPIDER_ID = "amazon_product_by-category-url"
        SPIDER_NAME = "amazon.com"

        url: str
        sort_by: str | None = None
        page_turning: int | None = None

    @dataclass
    class ProductByBestSellers(ToolRequest):
        """Amazon Product Details Scraper by Best Sellers URL."""

        SPIDER_ID = "amazon_product_by-best-sellers"
        SPIDER_NAME = "amazon.com"

        url: str
        page_turning: int | None = None

    # --- Other Amazon Tools ---

    @dataclass
    class GlobalProductByUrl(ToolRequest):
        """Amazon Global Product Details Scraper by URL"""

        SPIDER_ID = "amazon_global-product_by-url"
        SPIDER_NAME = "amazon.com"

        url: str

    # Backward compatible alias
    GlobalProduct = GlobalProductByUrl

    @dataclass
    class GlobalProductByCategoryUrl(ToolRequest):
        """Amazon Global Product Details Scraper by Category URL"""

        SPIDER_ID = "amazon_global-product_by-category-url"
        SPIDER_NAME = "amazon.com"

        url: str
        sort_by: str | None = None
        get_sponsored: str | None = None
        maximum: int | None = None

    @dataclass
    class GlobalProductBySellerUrl(ToolRequest):
        """Amazon Global Product Details Scraper by Seller URL"""

        SPIDER_ID = "amazon_global-product_by-seller-url"
        SPIDER_NAME = "amazon.com"

        url: str
        maximum: int | None = None

    @dataclass
    class GlobalProductByKeywords(ToolRequest):
        """Amazon Global Product Details Scraper by Keywords"""

        SPIDER_ID = "amazon_global-product_by-keywords"
        SPIDER_NAME = "amazon.com"

        keyword: str
        domain: str = "https://www.amazon.com"
        lowest_price: str | None = None
        highest_price: str | None = None
        page_turning: int | None = None

    @dataclass
    class GlobalProductByKeywordsBrand(ToolRequest):
        """Amazon Global Product Details Scraper by Keywords and Brand"""

        SPIDER_ID = "amazon_global-product_by-keywords-brand"
        SPIDER_NAME = "amazon.com"

        keyword: str
        brands: str
        page_turning: int | None = None

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
        domain: str = "https://www.amazon.com/"
        page_turning: int = 1


class eBay:
    """Namespace for eBay tools."""

    @dataclass
    class ProductByUrl(ToolRequest):
        """eBay Information Scraper by URL"""

        SPIDER_ID = "ebay_ebay_by-url"
        SPIDER_NAME = "ebay.com"
        url: str

    @dataclass
    class ProductByCategoryUrl(ToolRequest):
        """eBay Information Scraper by Category URL"""

        SPIDER_ID = "ebay_ebay_by-category-url"
        SPIDER_NAME = "ebay.com"
        url: str
        count: str | None = None

    @dataclass
    class ProductByKeywords(ToolRequest):
        """eBay Information Scraper by Keywords"""

        SPIDER_ID = "ebay_ebay_by-keywords"
        SPIDER_NAME = "ebay.com"
        keywords: str
        count: str | None = None

    @dataclass
    class ProductByListUrl(ToolRequest):
        """eBay Information Scraper by List URL"""

        SPIDER_ID = "ebay_ebay_by-listurl"
        SPIDER_NAME = "ebay.com"
        url: str
        count: str | None = None


class Walmart:
    """Namespace for Walmart tools."""

    @dataclass
    class ProductByUrl(ToolRequest):
        """Walmart Product Information Scraper by URL"""

        SPIDER_ID = "walmart_product_by-url"
        SPIDER_NAME = "walmart.com"
        url: str
        all_variations: str | None = None

    @dataclass
    class ProductByCategoryUrl(ToolRequest):
        """Walmart Product Information Scraper by Category URL"""

        SPIDER_ID = "walmart_product_by-category-url"
        SPIDER_NAME = "walmart.com"
        category_url: str
        all_variations: str | None = None
        page_turning: int | None = None

    @dataclass
    class ProductBySku(ToolRequest):
        """Walmart Product Information Scraper by SKU"""

        SPIDER_ID = "walmart_product_by-sku"
        SPIDER_NAME = "walmart.com"
        sku: str
        all_variations: str | None = None

    @dataclass
    class ProductByKeywords(ToolRequest):
        """Walmart Product Information Scraper by Keywords"""

        SPIDER_ID = "walmart_product_by-keywords"
        SPIDER_NAME = "walmart.com"
        keyword: str
        domain: str = "https://www.walmart.com/"
        all_variations: str | None = None
        page_turning: int | None = None

    @dataclass
    class ProductByZipcodes(ToolRequest):
        """Walmart Product Information Scraper by Zipcodes"""

        SPIDER_ID = "walmart_product_by-zipcodes"
        SPIDER_NAME = "walmart.com"
        url: str
        zip_code: str | None = None
