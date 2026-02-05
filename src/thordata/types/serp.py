"""
SERP (Search Engine Results Page) related types and configurations.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from .common import ThordataBaseConfig


class Engine(str, Enum):
    # Google
    GOOGLE = "google"
    GOOGLE_AI_MODE = "google_ai_mode"
    GOOGLE_NEWS = "google_news"
    GOOGLE_SHOPPING = "google_shopping"
    GOOGLE_VIDEOS = "google_videos"
    GOOGLE_IMAGES = "google_images"
    GOOGLE_MAPS = "google_maps"
    GOOGLE_JOBS = "google_jobs"
    GOOGLE_PLAY = "google_play"
    GOOGLE_PLAY_PRODUCT = "google_play_product"
    GOOGLE_PLAY_GAMES = "google_play_games"
    GOOGLE_PLAY_MOVIES = "google_play_movies"
    GOOGLE_PLAY_BOOKS = "google_play_books"
    GOOGLE_TRENDS = "google_trends"
    GOOGLE_SCHOLAR = "google_scholar"
    GOOGLE_SCHOLAR_CITE = "google_scholar_cite"
    GOOGLE_SCHOLAR_AUTHOR = "google_scholar_author"
    GOOGLE_PATENTS = "google_patents"
    GOOGLE_PATENTS_DETAILS = "google_patents_details"
    GOOGLE_FINANCE = "google_finance"
    GOOGLE_FINANCE_MARKETS = "google_finance_markets"
    GOOGLE_FLIGHTS = "google_flights"
    GOOGLE_LENS = "google_lens"
    GOOGLE_HOTELS = "google_hotels"

    # Bing
    BING = "bing"
    BING_NEWS = "bing_news"
    BING_SHOPPING = "bing_shopping"
    BING_IMAGES = "bing_images"
    BING_VIDEOS = "bing_videos"
    BING_MAPS = "bing_maps"

    # Others
    YANDEX = "yandex"
    DUCKDUCKGO = "duckduckgo"
    BAIDU = "baidu"  # Deprecated: Not supported by Dashboard

    # Legacy / Compatibility Aliases
    GOOGLE_SEARCH = "google_search"
    GOOGLE_WEB = "google_web"
    GOOGLE_LOCAL = "google_local"
    GOOGLE_PRODUCT = (
        "google_product"  # mapped to shopping with product_id internally usually
    )


class GoogleSearchType(str, Enum):
    SEARCH = "search"
    NEWS = "news"
    SHOPPING = "shopping"
    IMAGES = "images"
    VIDEOS = "videos"
    MAPS = "maps"
    # Add others as needed


class BingSearchType(str, Enum):
    SEARCH = "search"
    NEWS = "news"
    SHOPPING = "shopping"
    IMAGES = "images"
    VIDEOS = "videos"
    MAPS = "maps"


class GoogleTbm(str, Enum):
    NEWS = "nws"
    SHOPPING = "shop"
    IMAGES = "isch"
    VIDEOS = "vid"


class TimeRange(str, Enum):
    HOUR = "hour"
    DAY = "day"
    WEEK = "week"
    MONTH = "month"
    YEAR = "year"


@dataclass
class SerpRequest(ThordataBaseConfig):
    query: str
    engine: str = "google"
    num: int = 10
    start: int = 0

    # Localization
    country: str | None = None  # 'gl'
    language: str | None = None  # 'hl'
    google_domain: str | None = None
    countries_filter: str | None = None  # 'cr'
    languages_filter: str | None = None  # 'lr'

    # Geo-targeting
    location: str | None = None
    uule: str | None = None

    # Search type
    search_type: str | None = None  # 'tbm'

    # Filters
    safe_search: bool | None = None
    time_filter: str | None = None  # 'tbs'
    no_autocorrect: bool = False  # 'nfpr'
    filter_duplicates: bool | None = None  # 'filter'

    # Device & Rendering
    device: str | None = None
    render_js: bool | None = None
    no_cache: bool | None = None

    # Output format: "json" (json=1), "html" (json=3), "light_json" (json=4)
    # Note: "both" (json=2) format is not supported by Dashboard
    output_format: str = "json"

    # Advanced Google
    ludocid: str | None = None
    kgmid: str | None = None
    ai_overview: bool = False  # Only supported for engine=google

    # Pass-through for any other param
    extra_params: dict[str, Any] = field(default_factory=dict)

    # Mappings
    SEARCH_TYPE_MAP = {
        "images": "isch",
        "shopping": "shop",
        "news": "nws",
        "videos": "vid",
        "isch": "isch",
        "shop": "shop",
        "nws": "nws",
        "vid": "vid",
    }

    TIME_FILTER_MAP = {
        "hour": "qdr:h",
        "day": "qdr:d",
        "week": "qdr:w",
        "month": "qdr:m",
        "year": "qdr:y",
    }

    def to_payload(self) -> dict[str, Any]:
        engine = self.engine.lower()
        payload: dict[str, Any] = {
            "engine": engine,
            "num": str(self.num),
        }

        # JSON output handling
        # Dashboard mapping: json=1 (json), json=3 (html), json=4 (light json)
        # Note: json=2 (both) format is not supported by Dashboard
        fmt = self.output_format.lower()
        if fmt == "json":
            payload["json"] = "1"
        elif fmt == "html":
            payload["json"] = "3"
        elif fmt in ("light_json", "light-json", "lightjson"):
            payload["json"] = "4"
        elif fmt in ("2", "both", "json+html"):
            import warnings

            warnings.warn(
                "The 'both' output format (json=2) is not supported by Dashboard. "
                "Use 'json' or 'html' instead.",
                DeprecationWarning,
                stacklevel=2,
            )
            payload["json"] = "2"
        # If no json param is set, default to HTML (legacy behavior)

        # Query param handling
        if engine == "yandex":
            payload["text"] = self.query
        else:
            payload["q"] = self.query

        # Basic fields
        if self.google_domain:
            payload["google_domain"] = self.google_domain
        if self.start > 0:
            payload["start"] = str(self.start)
        if self.country:
            payload["gl"] = self.country.lower()
        if self.language:
            payload["hl"] = self.language.lower()
        if self.countries_filter:
            payload["cr"] = self.countries_filter
        if self.languages_filter:
            payload["lr"] = self.languages_filter
        if self.location:
            payload["location"] = self.location
        if self.uule:
            payload["uule"] = self.uule

        # Search Type (tbm)
        if self.search_type:
            val = self.search_type.lower()
            payload["tbm"] = self.SEARCH_TYPE_MAP.get(val, val)

        # Filters
        if self.safe_search is not None:
            payload["safe"] = "active" if self.safe_search else "off"

        if self.time_filter:
            val = self.time_filter.lower()
            payload["tbs"] = self.TIME_FILTER_MAP.get(val, val)

        if self.no_autocorrect:
            payload["nfpr"] = "1"
        if self.filter_duplicates is not None:
            payload["filter"] = "1" if self.filter_duplicates else "0"

        # Device & Rendering
        if self.device:
            payload["device"] = self.device.lower()
        if self.render_js is not None:
            payload["render_js"] = "True" if self.render_js else "False"
        if self.no_cache is not None:
            payload["no_cache"] = "True" if self.no_cache else "False"

        # Advanced
        if self.ludocid:
            payload["ludocid"] = self.ludocid
        if self.kgmid:
            payload["kgmid"] = self.kgmid

        # AI Overview (only for Google engine)
        if self.ai_overview:
            if engine != "google":
                raise ValueError(
                    "ai_overview parameter is only supported for engine=google"
                )
            payload["ai_overview"] = "true"

        # Merge extras
        payload.update(self.extra_params)
        return payload
