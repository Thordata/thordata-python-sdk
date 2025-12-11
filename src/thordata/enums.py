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
    """

    DEFAULT = "pr.thordata.net"
    NORTH_AMERICA = "t.na.thordata.net"
    EUROPE = "t.eu.thordata.net"
    GATE = "gate.thordata.com"


class ProxyPort(IntEnum):
    """
    Available proxy gateway ports.
    """

    DEFAULT = 9999
    MOBILE = 5555
    DATACENTER = 7777
    ISP = 6666
    ALTERNATIVE = 22225


# =============================================================================
# Search Engine Enums
# =============================================================================


class Engine(str, Enum):
    """
    Supported search engines for SERP API.
    """

    GOOGLE = "google"
    BING = "bing"
    YANDEX = "yandex"
    DUCKDUCKGO = "duckduckgo"
    BAIDU = "baidu"
    YAHOO = "yahoo"
    NAVER = "naver"


class GoogleSearchType(str, Enum):
    """
    Search types specific to Google.
    """

    SEARCH = "search"
    MAPS = "maps"
    SHOPPING = "shopping"
    NEWS = "news"
    IMAGES = "images"
    VIDEOS = "videos"
    SCHOLAR = "scholar"
    PATENTS = "patents"
    JOBS = "jobs"
    FLIGHTS = "flights"
    FINANCE = "finance"


class BingSearchType(str, Enum):
    """
    Search types specific to Bing.
    """

    SEARCH = "search"
    IMAGES = "images"
    VIDEOS = "videos"
    NEWS = "news"
    MAPS = "maps"


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
    """

    HTML = "html"
    PNG = "png"
    PDF = "pdf"
    MARKDOWN = "markdown"
    TEXT = "text"


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
# Country Enum (常用国家)
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
        # value is an enum member, get its .value
        return str(getattr(value, "value", value)).lower()
    if isinstance(value, str):
        return value.lower()
    raise TypeError(
        f"Expected {enum_class.__name__} or str, got {type(value).__name__}"
    )
