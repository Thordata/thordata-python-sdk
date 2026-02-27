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
        # Allow both string and Enum values for engine (for backwards compatibility).
        raw_engine = self.engine
        if isinstance(raw_engine, Enum):
            engine_str = str(raw_engine.value)
        else:
            engine_str = str(raw_engine)
        engine = engine_str.lower()

        payload: dict[str, Any] = {"engine": engine}

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
        # Pagination + localization differ per engine family
        if engine.startswith("bing"):
            # Bing uses 1-based 'first' and 'count'
            if self.start > 0:
                payload["first"] = str(self.start + 1)
            payload["count"] = str(self.num)
            if self.country:
                payload["cc"] = self.country.lower()
            if self.language:
                payload["mkt"] = self.language
        elif engine == "yandex":
            # Yandex supports 'lang' (UI language) but also has its own 'lr' region param.
            if self.language:
                payload["lang"] = self.language
            # Yandex pagination is 'p' (page index); keep 'start/num' out unless user passes via extra_params.
        elif engine == "duckduckgo":
            # DuckDuckGo supports 'start' but has no standard 'num' param in our docs.
            if self.start > 0:
                payload["start"] = str(self.start)
            if self.language:
                # Best-effort: DuckDuckGo uses 'kl' for region/lang (e.g. 'us-en').
                payload["kl"] = self.language
        else:
            # Google (+ other engines that behave similarly)
            payload["num"] = str(self.num)
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
        if self.search_type and engine.startswith("google"):
            val = self.search_type.lower()
            payload["tbm"] = self.SEARCH_TYPE_MAP.get(val, val)

        # Filters
        if self.safe_search is not None and engine.startswith("google"):
            payload["safe"] = "active" if self.safe_search else "off"

        if self.time_filter and engine.startswith("google"):
            val = self.time_filter.lower()
            payload["tbs"] = self.TIME_FILTER_MAP.get(val, val)

        if self.no_autocorrect and engine.startswith("google"):
            payload["nfpr"] = "1"
        if self.filter_duplicates is not None and engine.startswith("google"):
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


# =============================================================================
# Strongly-Typed SERP Requests (minimal & extensible)
# =============================================================================
#
# Design goals:
# - Keep the core SDK minimal (no heavy validation deps like pydantic).
# - Provide strong typing + upfront validation for REQUIRED parameters per engine/mode.
# - Keep full flexibility via `extra_params` pass-through for long-tail parameters.


@dataclass
class SerpTypedRequest(ThordataBaseConfig):
    """
    Base class for strongly-typed SERP requests.

    Subclasses should define:
    - engine (fixed string)
    - required fields for that engine/mode
    - optional fields as needed
    """

    # Common options
    num: int = 10
    start: int = 0
    country: str | None = None
    language: str | None = None
    google_domain: str | None = None
    countries_filter: str | None = None
    languages_filter: str | None = None
    location: str | None = None
    uule: str | None = None
    search_type: str | None = None
    safe_search: bool | None = None
    time_filter: str | None = None
    no_autocorrect: bool = False
    filter_duplicates: bool | None = None
    device: str | None = None
    render_js: bool | None = None
    no_cache: bool | None = None
    output_format: str = "json"
    ai_overview: bool = False
    ludocid: str | None = None
    kgmid: str | None = None

    # Any extra API params not explicitly modeled
    extra_params: dict[str, Any] = field(default_factory=dict)

    # Subclass must override
    engine: str = "google"

    def _validate_common(self) -> None:
        if self.num < 1:
            raise ValueError("num must be >= 1")
        if self.start < 0:
            raise ValueError("start must be >= 0")

    def _build_serp_request(self, *, query: str) -> SerpRequest:
        self._validate_common()
        return SerpRequest(
            query=query,
            engine=self.engine,
            num=self.num,
            start=self.start,
            country=self.country,
            language=self.language,
            google_domain=self.google_domain,
            countries_filter=self.countries_filter,
            languages_filter=self.languages_filter,
            location=self.location,
            uule=self.uule,
            search_type=self.search_type,
            safe_search=self.safe_search,
            time_filter=self.time_filter,
            no_autocorrect=self.no_autocorrect,
            filter_duplicates=self.filter_duplicates,
            device=self.device,
            render_js=self.render_js,
            no_cache=self.no_cache,
            output_format=self.output_format,
            ai_overview=self.ai_overview,
            ludocid=self.ludocid,
            kgmid=self.kgmid,
            extra_params=dict(self.extra_params),
        )

    def to_serp_request(self) -> SerpRequest:
        """
        Convert this typed request into a `SerpRequest`.

        Subclasses must implement this and should call `_build_serp_request()`.
        """
        raise NotImplementedError("Subclasses must implement to_serp_request()")


# --- Google ---


@dataclass
class GoogleSearchRequest(SerpTypedRequest):
    engine: str = "google"
    query: str = ""

    def __post_init__(self) -> None:
        self._validate_common()
        if not self.query.strip():
            raise ValueError("GoogleSearchRequest.query is required")

    def to_serp_request(self) -> SerpRequest:  # type: ignore[override]
        return super()._build_serp_request(query=self.query)


@dataclass
class GoogleNewsRequest(GoogleSearchRequest):
    engine: str = "google_news"


@dataclass
class GoogleShoppingRequest(GoogleSearchRequest):
    engine: str = "google_shopping"


@dataclass
class GoogleLocalRequest(GoogleSearchRequest):
    engine: str = "google_local"


@dataclass
class GoogleVideosRequest(GoogleSearchRequest):
    engine: str = "google_videos"


@dataclass
class GoogleImagesRequest(GoogleSearchRequest):
    engine: str = "google_images"


@dataclass
class GoogleTrendsRequest(GoogleSearchRequest):
    engine: str = "google_trends"


@dataclass
class GoogleHotelsRequest(GoogleSearchRequest):
    engine: str = "google_hotels"


@dataclass
class GooglePlayRequest(GoogleSearchRequest):
    engine: str = "google_play"


@dataclass
class GoogleJobsRequest(GoogleSearchRequest):
    engine: str = "google_jobs"


@dataclass
class GoogleScholarRequest(GoogleSearchRequest):
    engine: str = "google_scholar"


@dataclass
class GoogleFinanceRequest(GoogleSearchRequest):
    engine: str = "google_finance"


@dataclass
class GooglePatentsRequest(GoogleSearchRequest):
    engine: str = "google_patents"


@dataclass
class GoogleMapsRequest(GoogleSearchRequest):
    engine: str = "google_maps"
    ll: str | None = None  # GPS coordinates string like '@lat,lon,14z'

    def to_serp_request(self) -> SerpRequest:  # type: ignore[override]
        req = super().to_serp_request()
        if self.ll:
            req.extra_params["ll"] = self.ll
        return req


@dataclass
class GoogleProductRequest(SerpTypedRequest):
    engine: str = "google_product"
    product_id: str = ""

    def __post_init__(self) -> None:
        self._validate_common()
        if not str(self.product_id).strip():
            raise ValueError("GoogleProductRequest.product_id is required")

    def to_serp_request(self) -> SerpRequest:  # type: ignore[override]
        req = super()._build_serp_request(query="")
        req.extra_params["product_id"] = str(self.product_id).strip()
        return req


@dataclass
class GoogleFlightsRequest(SerpTypedRequest):
    engine: str = "google_flights"
    departure_id: str = ""
    arrival_id: str = ""
    outbound_date: str = ""  # YYYY-MM-DD
    return_date: str | None = None

    def __post_init__(self) -> None:
        self._validate_common()
        if not self.departure_id.strip():
            raise ValueError("GoogleFlightsRequest.departure_id is required")
        if not self.arrival_id.strip():
            raise ValueError("GoogleFlightsRequest.arrival_id is required")
        if not self.outbound_date.strip():
            raise ValueError("GoogleFlightsRequest.outbound_date is required")

    def to_serp_request(self) -> SerpRequest:  # type: ignore[override]
        req = super()._build_serp_request(query="")
        req.extra_params["departure_id"] = self.departure_id
        req.extra_params["arrival_id"] = self.arrival_id
        req.extra_params["outbound_date"] = self.outbound_date
        if self.return_date:
            req.extra_params["return_date"] = self.return_date
        return req


@dataclass
class GoogleLensRequest(SerpTypedRequest):
    engine: str = "google_lens"
    url: str = ""  # Image URL (required)
    query: str | None = None  # Optional q for lens
    type: str | None = None  # Optional lens type

    def __post_init__(self) -> None:
        self._validate_common()
        u = self.url.strip()
        if not u:
            raise ValueError("GoogleLensRequest.url is required")
        if not (u.startswith("http://") or u.startswith("https://")):
            raise ValueError(
                "GoogleLensRequest.url must start with http:// or https://"
            )

    def to_serp_request(self) -> SerpRequest:  # type: ignore[override]
        req = super()._build_serp_request(query="")
        req.extra_params["url"] = self.url.strip()
        if self.query:
            req.extra_params["q"] = self.query
        if self.type:
            req.extra_params["type"] = self.type
        return req


# --- Bing ---


@dataclass
class BingSearchRequest(SerpTypedRequest):
    engine: str = "bing"
    query: str = ""

    def __post_init__(self) -> None:
        self._validate_common()
        if not self.query.strip():
            raise ValueError("BingSearchRequest.query is required")

    def to_serp_request(self) -> SerpRequest:  # type: ignore[override]
        return super()._build_serp_request(query=self.query)


@dataclass
class BingNewsRequest(BingSearchRequest):
    engine: str = "bing_news"


@dataclass
class BingShoppingRequest(BingSearchRequest):
    engine: str = "bing_shopping"


@dataclass
class BingImagesRequest(BingSearchRequest):
    engine: str = "bing_images"


@dataclass
class BingVideosRequest(BingSearchRequest):
    engine: str = "bing_videos"


@dataclass
class BingMapsRequest(BingSearchRequest):
    engine: str = "bing_maps"
    cp: str | None = None  # Optional GPS coordinates string like 'lat~lon'

    def to_serp_request(self) -> SerpRequest:  # type: ignore[override]
        req = super().to_serp_request()
        if self.cp:
            req.extra_params["cp"] = self.cp
        return req


# --- Others ---


@dataclass
class DuckDuckGoSearchRequest(SerpTypedRequest):
    engine: str = "duckduckgo"
    query: str = ""
    kl: str | None = None  # region/lang

    def __post_init__(self) -> None:
        self._validate_common()
        if not self.query.strip():
            raise ValueError("DuckDuckGoSearchRequest.query is required")

    def to_serp_request(self) -> SerpRequest:  # type: ignore[override]
        req = super()._build_serp_request(query=self.query)
        if self.kl:
            req.extra_params["kl"] = self.kl
        return req


@dataclass
class YandexSearchRequest(SerpTypedRequest):
    engine: str = "yandex"
    query: str = ""

    def __post_init__(self) -> None:
        self._validate_common()
        if not self.query.strip():
            raise ValueError("YandexSearchRequest.query is required")

    def to_serp_request(self) -> SerpRequest:  # type: ignore[override]
        return super()._build_serp_request(query=self.query)
