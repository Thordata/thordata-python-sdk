"""
Web Scraper Tool Registry.
High-level abstractions for specific scraping targets.
"""

from .base import ToolRequest, VideoToolRequest
from .code import GitHub
from .ecommerce import Amazon
from .search import GoogleMaps, GooglePlay, GoogleShopping
from .social import Facebook, Instagram, LinkedIn, Reddit, TikTok, Twitter
from .video import YouTube

__all__ = [
    "ToolRequest",
    "VideoToolRequest",
    "Amazon",
    "GoogleMaps",
    "GoogleShopping",
    "GooglePlay",
    "TikTok",
    "Facebook",
    "Instagram",
    "Twitter",
    "LinkedIn",
    "Reddit",
    "YouTube",
    "GitHub",
]
