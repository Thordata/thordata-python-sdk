"""
Enumerations for the Thordata Python SDK.

This module provides type-safe enumerations for all Thordata API parameters,
making it easier to discover available options via IDE autocomplete.
"""

from enum import Enum, IntEnum

# =============================================================================
# Continent Enum
# =============================================================================


class Continent(str, Enum):
    """
    Continent codes for geo-targeting.
    """

    AFRICA = "af"
    ANTARCTICA = "an"
    ASIA = "as"
    EUROPE = "eu"
    NORTH_AMERICA = "na"
    OCEANIA = "oc"
    SOUTH_AMERICA = "sa"


# =============================================================================
# Proxy Host Enum
# =============================================================================


class ProxyHost(str, Enum):
    """
    Available proxy gateway hosts.

    Note: Dashboard provides user-specific hosts like {shard}.{region}.thordata.net
    """

    DEFAULT = "pr.thordata.net"
    NORTH_AMERICA = "t.na.thordata.net"
    EUROPE = "t.eu.thordata.net"


class ProxyPort(IntEnum):
    """
    Available proxy gateway ports.
    """

    RESIDENTIAL = 9999
    MOBILE = 5555
    DATACENTER = 7777
    ISP = 6666


# =============================================================================
# Search Engine Enums
# =============================================================================


class Engine(str, Enum):
    """
    Supported search engines for SERP API.

    Engine naming convention:
    - Base search: {engine} for basic web search (google, bing, yandex, duckduckgo)
    - Verticals: {engine}_{vertical} (e.g., google_news, bing_images)
    - Sub-verticals: {engine}_{vertical}_{sub} (e.g., google_scholar_cite)
    """

    # ===================
    # Google
    # ===================
    GOOGLE = "google"
    GOOGLE_SEARCH = "google_search"
    GOOGLE_AI_MODE = "google_ai_mode"
    GOOGLE_WEB = "google_web"
    GOOGLE_SHOPPING = "google_shopping"
    GOOGLE_LOCAL = "google_local"
    GOOGLE_VIDEOS = "google_videos"
    GOOGLE_NEWS = "google_news"
    GOOGLE_FLIGHTS = "google_flights"
    GOOGLE_IMAGES = "google_images"
    GOOGLE_LENS = "google_lens"
    GOOGLE_TRENDS = "google_trends"
    GOOGLE_HOTELS = "google_hotels"
    GOOGLE_PLAY = "google_play"
    GOOGLE_JOBS = "google_jobs"
    GOOGLE_SCHOLAR = "google_scholar"
    GOOGLE_SCHOLAR_CITE = "google_scholar_cite"
    GOOGLE_SCHOLAR_AUTHOR = "google_scholar_author"
    GOOGLE_MAPS = "google_maps"
    GOOGLE_FINANCE = "google_finance"
    GOOGLE_FINANCE_MARKETS = "google_finance_markets"
    GOOGLE_PATENTS = "google_patents"
    GOOGLE_PATENTS_DETAILS = "google_patents_details"

    # ===================
    # Bing
    # ===================
    BING = "bing"
    BING_SEARCH = "bing_search"
    BING_IMAGES = "bing_images"
    BING_VIDEOS = "bing_videos"
    BING_NEWS = "bing_news"
    BING_MAPS = "bing_maps"
    BING_SHOPPING = "bing_shopping"

    # ===================
    # Yandex
    # ===================
    YANDEX = "yandex"
    YANDEX_SEARCH = "yandex_search"

    # ===================
    # DuckDuckGo
    # ===================
    DUCKDUCKGO = "duckduckgo"
    DUCKDUCKGO_SEARCH = "duckduckgo_search"


class GoogleSearchType(str, Enum):
    """
    Search types specific to Google.

    These map to the second part of Google engine names.
    For example, GOOGLE + NEWS = google_news
    """

    SEARCH = "search"
    AI_MODE = "ai_mode"
    WEB = "web"
    SHOPPING = "shopping"
    LOCAL = "local"
    VIDEOS = "videos"
    NEWS = "news"
    FLIGHTS = "flights"
    IMAGES = "images"
    LENS = "lens"
    TRENDS = "trends"
    HOTELS = "hotels"
    PLAY = "play"
    JOBS = "jobs"
    SCHOLAR = "scholar"
    MAPS = "maps"
    FINANCE = "finance"
    PATENTS = "patents"


class BingSearchType(str, Enum):
    """
    Search types specific to Bing.
    """

    SEARCH = "search"
    IMAGES = "images"
    VIDEOS = "videos"
    NEWS = "news"
    MAPS = "maps"
    SHOPPING = "shopping"


class GoogleTbm(str, Enum):
    """
    Google tbm (to be matched) parameter values.

    Only available when using specific Google engines that support tbm.
    """

    NEWS = "nws"
    SHOPPING = "shop"
    IMAGES = "isch"
    VIDEOS = "vid"


class Device(str, Enum):
    """
    Device types for SERP API.
    """

    DESKTOP = "desktop"
    MOBILE = "mobile"
    TABLET = "tablet"


class TimeRange(str, Enum):
    """
    Time range filters for search results.
    """

    HOUR = "hour"
    DAY = "day"
    WEEK = "week"
    MONTH = "month"
    YEAR = "year"


# =============================================================================
# Proxy Enums
# =============================================================================


class ProxyType(IntEnum):
    """
    Types of proxy networks available.
    """

    RESIDENTIAL = 1
    UNLIMITED = 2
    DATACENTER = 3
    ISP = 4
    MOBILE = 5


class SessionType(str, Enum):
    """
    Proxy session types for connection persistence.
    """

    ROTATING = "rotating"
    STICKY = "sticky"


# =============================================================================
# Output Format Enums
# =============================================================================


class OutputFormat(str, Enum):
    """
    Output formats for Universal Scraping API.

    Currently supported: html, png
    """

    HTML = "html"
    PNG = "png"


class DataFormat(str, Enum):
    """
    Data formats for task result download.
    """

    JSON = "json"
    CSV = "csv"
    XLSX = "xlsx"


# =============================================================================
# Task Status Enums
# =============================================================================


class TaskStatus(str, Enum):
    """
    Possible statuses for async scraping tasks.
    """

    PENDING = "pending"
    RUNNING = "running"
    READY = "ready"
    SUCCESS = "success"
    FINISHED = "finished"
    FAILED = "failed"
    ERROR = "error"
    CANCELLED = "cancelled"
    UNKNOWN = "unknown"

    @classmethod
    def is_terminal(cls, status: "TaskStatus") -> bool:
        """Check if a status is terminal (no more updates expected)."""
        return status in {
            cls.READY,
            cls.SUCCESS,
            cls.FINISHED,
            cls.FAILED,
            cls.ERROR,
            cls.CANCELLED,
        }

    @classmethod
    def is_success(cls, status: "TaskStatus") -> bool:
        """Check if a status indicates success."""
        return status in {cls.READY, cls.SUCCESS, cls.FINISHED}

    @classmethod
    def is_failure(cls, status: "TaskStatus") -> bool:
        """Check if a status indicates failure."""
        return status in {cls.FAILED, cls.ERROR}


# =============================================================================
# Country Enum (Common Countries)
# =============================================================================


class Country(str, Enum):
    """
    Common country codes for geo-targeting.
    """

    # North America
    US = "us"
    CA = "ca"
    MX = "mx"

    # Europe
    GB = "gb"
    DE = "de"
    FR = "fr"
    ES = "es"
    IT = "it"
    NL = "nl"
    PL = "pl"
    RU = "ru"
    UA = "ua"
    SE = "se"
    NO = "no"
    DK = "dk"
    FI = "fi"
    CH = "ch"
    AT = "at"
    BE = "be"
    PT = "pt"
    IE = "ie"
    CZ = "cz"
    GR = "gr"

    # Asia Pacific
    CN = "cn"
    JP = "jp"
    KR = "kr"
    IN = "in"
    AU = "au"
    NZ = "nz"
    SG = "sg"
    HK = "hk"
    TW = "tw"
    TH = "th"
    VN = "vn"
    ID = "id"
    MY = "my"
    PH = "ph"
    PK = "pk"
    BD = "bd"

    # South America
    BR = "br"
    AR = "ar"
    CL = "cl"
    CO = "co"
    PE = "pe"
    VE = "ve"

    # Middle East & Africa
    AE = "ae"
    SA = "sa"
    IL = "il"
    TR = "tr"
    ZA = "za"
    EG = "eg"
    NG = "ng"
    KE = "ke"
    MA = "ma"


# =============================================================================
# Helper Functions
# =============================================================================


def normalize_enum_value(value: object, enum_class: type) -> str:
    """
    Safely convert an enum or string to its string value.
    """
    if isinstance(value, enum_class):
        return str(getattr(value, "value", value)).lower()
    if isinstance(value, str):
        return value.lower()
    raise TypeError(
        f"Expected {enum_class.__name__} or str, got {type(value).__name__}"
    )
