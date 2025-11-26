# src/thordata/enums.py

from enum import Enum

class Engine(str, Enum):
    """
    Supported Search Engines for SERP API.
    """
    GOOGLE = "google"
    BING = "bing"
    YANDEX = "yandex"
    DUCKDUCKGO = "duckduckgo"
    BAIDU = "baidu"

class GoogleSearchType(str, Enum):
    """
    Specific search types for Google Engine.
    """
    SEARCH = "search"      # Default web search
    MAPS = "maps"          # Google Maps
    SHOPPING = "shopping"  # Google Shopping
    NEWS = "news"          # Google News
    IMAGES = "images"      # Google Images
    VIDEOS = "videos"      # Google Videos
    # Users can pass other strings manually if needed