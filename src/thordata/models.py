"""
Data models for the Thordata Python SDK.

This module provides type-safe dataclasses for configuring proxy requests,
SERP API calls, and Universal Scraping requests. Using these models enables
IDE autocomplete and reduces parameter errors.

Example:
    >>> from thordata.models import ProxyConfig, SerpRequest
    >>>
    >>> # Build a proxy URL with geo-targeting
    >>> proxy = ProxyConfig(
    ...     username="myuser",
    ...     password="mypass",
    ...     country="us",
    ...     city="seattle"
    ... )
    >>> print(proxy.build_proxy_url())

    >>> # Configure a SERP request
    >>> serp = SerpRequest(query="python tutorial", engine="google", num=20)
    >>> print(serp.to_payload())
"""

from __future__ import annotations

import json
import re
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Union

# =============================================================================
# Proxy Product Types
# =============================================================================


class ProxyProduct(str, Enum):
    """
    Thordata proxy product types with their default ports.

    Each product type has a specific port on the proxy gateway.
    """

    RESIDENTIAL = "residential"
    MOBILE = "mobile"
    DATACENTER = "datacenter"
    ISP = "isp"

    @property
    def default_port(self) -> int:
        """Get the default port for this proxy product."""
        ports = {
            "residential": 9999,
            "mobile": 5555,
            "datacenter": 7777,
            "isp": 6666,
        }
        return ports[self.value]


# =============================================================================
# Proxy Configuration Models
# =============================================================================


@dataclass
class ProxyConfig:
    """
    Configuration for building a Thordata proxy URL.

    This class handles the complex username format required by Thordata proxies,
    where geo-targeting and session parameters are embedded in the username.

    Args:
        username: Your Thordata account username (the part after 'td-customer-').
        password: Your Thordata account password.
        product: Proxy product type (residential, mobile, datacenter, isp).
        host: Proxy gateway host. If None, uses default based on product.
        port: Proxy gateway port. If None, uses default based on product.
        protocol: Proxy protocol - 'http' or 'https'.

        # Geo-targeting (all optional)
        continent: Target continent code (af/an/as/eu/na/oc/sa).
        country: Target country code in ISO 3166-1 alpha-2 format.
        state: Target state name in lowercase.
        city: Target city name in lowercase.
        asn: Target ASN code (e.g., 'AS12322'). Must be used with country.

        # Session control (optional)
        session_id: Session identifier for sticky sessions.
        session_duration: Session duration in minutes (1-90).

    Example:
        >>> config = ProxyConfig(
        ...     username="GnrqUwwu3obt",
        ...     password="PkCSzvt30iww",
        ...     product=ProxyProduct.RESIDENTIAL,
        ...     country="us",
        ...     state="california",
        ...     session_id="mysession123",
        ...     session_duration=10
        ... )
        >>> print(config.build_proxy_url())
        http://td-customer-GnrqUwwu3obt-country-us-state-california-sessid-mysession123-sesstime-10:PkCSzvt30iww@....pr.thordata.net:9999
    """

    username: str
    password: str
    product: Union[ProxyProduct, str] = ProxyProduct.RESIDENTIAL
    host: Optional[str] = None
    port: Optional[int] = None
    protocol: str = "http"

    # Geo-targeting
    continent: Optional[str] = None
    country: Optional[str] = None
    state: Optional[str] = None
    city: Optional[str] = None
    asn: Optional[str] = None

    # Session control
    session_id: Optional[str] = None
    session_duration: Optional[int] = None  # minutes, 1-90

    # Valid continent codes
    VALID_CONTINENTS = {"af", "an", "as", "eu", "na", "oc", "sa"}

    def __post_init__(self) -> None:
        """Validate configuration after initialization."""
        # Normalize product to enum
        if isinstance(self.product, str):
            self.product = ProxyProduct(self.product.lower())

        # Set default host and port based on product
        if self.host is None:
            # Set host based on product type
            host_map = {
                ProxyProduct.RESIDENTIAL: "t.pr.thordata.net",
                ProxyProduct.DATACENTER: "dc.pr.thordata.net",
                ProxyProduct.MOBILE: "m.pr.thordata.net",
                ProxyProduct.ISP: "isp.pr.thordata.net",
            }
            self.host = host_map.get(self.product, "pr.thordata.net")

        if self.port is None:
            self.port = self.product.default_port

        self._validate()

    def _validate(self) -> None:
        """Validate the proxy configuration."""
        # Validate protocol
        if self.protocol not in ("http", "https"):
            raise ValueError(
                f"Invalid protocol: {self.protocol}. Must be 'http' or 'https'."
            )

        # Validate session duration
        if self.session_duration is not None:
            if not 1 <= self.session_duration <= 90:
                raise ValueError(
                    f"session_duration must be between 1 and 90 minutes, "
                    f"got {self.session_duration}"
                )
            if not self.session_id:
                raise ValueError("session_duration requires session_id to be set")

        # Validate ASN requires country
        if self.asn and not self.country:
            raise ValueError("ASN targeting requires country to be specified")

        # Validate continent code
        if self.continent and self.continent.lower() not in self.VALID_CONTINENTS:
            raise ValueError(
                f"Invalid continent code: {self.continent}. "
                f"Must be one of: {', '.join(sorted(self.VALID_CONTINENTS))}"
            )

        # Validate country code format (2 letters)
        if self.country and not re.match(r"^[a-zA-Z]{2}$", self.country):
            raise ValueError(
                f"Invalid country code: {self.country}. "
                "Must be a 2-letter ISO 3166-1 alpha-2 code."
            )

    def build_username(self) -> str:
        """
        Build the complete username string with embedded parameters.

        Returns:
            The formatted username string for proxy authentication.
        """
        parts = [f"td-customer-{self.username}"]

        # Add geo-targeting parameters (order matters)
        if self.continent:
            parts.append(f"continent-{self.continent.lower()}")

        if self.country:
            parts.append(f"country-{self.country.lower()}")

        if self.state:
            parts.append(f"state-{self.state.lower()}")

        if self.city:
            parts.append(f"city-{self.city.lower()}")

        if self.asn:
            # Ensure ASN has correct format
            asn_value = self.asn.upper()
            if not asn_value.startswith("AS"):
                asn_value = f"AS{asn_value}"
            parts.append(f"asn-{asn_value}")

        # Add session parameters
        if self.session_id:
            parts.append(f"sessid-{self.session_id}")

        if self.session_duration:
            parts.append(f"sesstime-{self.session_duration}")

        return "-".join(parts)

    def build_proxy_url(self) -> str:
        """
        Build the complete proxy URL.

        Returns:
            The formatted proxy URL for use with requests/aiohttp.
        """
        username = self.build_username()
        return f"{self.protocol}://{username}:{self.password}@{self.host}:{self.port}"

    def to_proxies_dict(self) -> Dict[str, str]:
        """
        Build a proxies dict suitable for the requests library.

        Returns:
            Dict with 'http' and 'https' keys pointing to the proxy URL.
        """
        url = self.build_proxy_url()
        return {"http": url, "https": url}

    def to_aiohttp_config(self) -> tuple:
        """
        Get proxy configuration for aiohttp.

        Returns:
            Tuple of (proxy_url, proxy_auth) for aiohttp.
        """
        try:
            import aiohttp

            proxy_url = f"{self.protocol}://{self.host}:{self.port}"
            proxy_auth = aiohttp.BasicAuth(
                login=self.build_username(), password=self.password
            )
            return proxy_url, proxy_auth
        except ImportError as e:
            raise ImportError(
                "aiohttp is required for async proxy configuration"
            ) from e


@dataclass
class StaticISPProxy:
    """
    Configuration for static ISP proxy with direct IP connection.

    Static ISP proxies connect directly to a purchased IP address,
    not through the gateway.

    Args:
        host: The static IP address you purchased.
        username: Your ISP proxy username.
        password: Your ISP proxy password.
        port: Port number (default: 6666).
        protocol: Proxy protocol - 'http' or 'https'.

    Example:
        >>> proxy = StaticISPProxy(
        ...     host="xx.xxx.xxx.xxx",
        ...     username="myuser",
        ...     password="mypass"
        ... )
        >>> print(proxy.build_proxy_url())
        http://myuser:mypass@xx.xxx.xxx.xxx:6666
    """

    host: str
    username: str
    password: str
    port: int = 6666
    protocol: str = "http"

    def __post_init__(self) -> None:
        """Validate configuration."""
        if self.protocol not in ("http", "https"):
            raise ValueError(
                f"Invalid protocol: {self.protocol}. Must be 'http' or 'https'."
            )

    def build_proxy_url(self) -> str:
        """
        Build the complete proxy URL for direct connection.

        Returns:
            The formatted proxy URL.
        """
        return (
            f"{self.protocol}://{self.username}:{self.password}@{self.host}:{self.port}"
        )

    def to_proxies_dict(self) -> Dict[str, str]:
        """
        Build a proxies dict suitable for the requests library.

        Returns:
            Dict with 'http' and 'https' keys pointing to the proxy URL.
        """
        url = self.build_proxy_url()
        return {"http": url, "https": url}

    def to_aiohttp_config(self) -> tuple:
        """
        Get proxy configuration for aiohttp.

        Returns:
            Tuple of (proxy_url, proxy_auth) for aiohttp.
        """
        try:
            import aiohttp

            proxy_url = f"{self.protocol}://{self.host}:{self.port}"
            proxy_auth = aiohttp.BasicAuth(login=self.username, password=self.password)
            return proxy_url, proxy_auth
        except ImportError as e:
            raise ImportError(
                "aiohttp is required for async proxy configuration"
            ) from e

    @classmethod
    def from_env(cls) -> "StaticISPProxy":
        """
        Create StaticISPProxy from environment variables.

        Required env vars:
            - THORDATA_ISP_HOST
            - THORDATA_ISP_USERNAME
            - THORDATA_ISP_PASSWORD

        Returns:
            Configured StaticISPProxy instance.

        Raises:
            ValueError: If required environment variables are missing.
        """
        import os

        host = os.getenv("THORDATA_ISP_HOST")
        username = os.getenv("THORDATA_ISP_USERNAME")
        password = os.getenv("THORDATA_ISP_PASSWORD")

        if not all([host, username, password]):
            raise ValueError(
                "THORDATA_ISP_HOST, THORDATA_ISP_USERNAME, and "
                "THORDATA_ISP_PASSWORD are required"
            )

        return cls(host=host, username=username, password=password)


@dataclass
class StickySession(ProxyConfig):
    """
    Convenience class for creating sticky session proxy configurations.

    A sticky session keeps the same IP address for a specified duration,
    useful for multi-step operations that require IP consistency.

    Args:
        duration_minutes: How long to keep the same IP (1-90 minutes).
        auto_session_id: If True, automatically generates a unique session ID.

    Example:
        >>> session = StickySession(
        ...     username="myuser",
        ...     password="mypass",
        ...     country="us",
        ...     duration_minutes=15
        ... )
        >>> # Each call to build_proxy_url() uses the same session
        >>> url = session.build_proxy_url()
    """

    duration_minutes: int = 10
    auto_session_id: bool = True

    def __post_init__(self) -> None:
        # Auto-generate session ID if requested and not provided
        if self.auto_session_id and not self.session_id:
            self.session_id = uuid.uuid4().hex[:12]

        # Set session_duration from duration_minutes
        self.session_duration = self.duration_minutes

        # Call parent post_init
        super().__post_init__()


# =============================================================================
# SERP API Models
# =============================================================================


@dataclass
class SerpRequest:
    """
    Configuration for a SERP API request.

    Supports Google, Bing, Yandex, DuckDuckGo, and Baidu search engines.

    Args:
        query: The search query string (required).
        engine: Search engine to use (default: 'google').
        num: Number of results per page (default: 10).
        start: Result offset for pagination (default: 0).

        # Localization
        country: Country code for results (gl parameter for Google).
        language: Language code for interface (hl parameter for Google).
        google_domain: Google domain to use (e.g., 'google.co.uk').

        # Geo-targeting
        location: Location name for geo-targeting.
        uule: Encoded location parameter (use with location).

        # Search type
        search_type: Type of search (images, news, shopping, videos, etc.).

        # Filters
        safe_search: Enable safe search filtering.
        time_filter: Time range filter (hour, day, week, month, year).
        no_autocorrect: Disable automatic spelling correction (nfpr).
        filter_duplicates: Enable/disable duplicate filtering.

        # Device & Rendering
        device: Device type ('desktop', 'mobile', 'tablet').
        render_js: Enable JavaScript rendering in SERP (render_js=True/False).
        no_cache: Disable internal caching (no_cache=True/False).

        # Output
        output_format: 'json' (default) or 'html'.

        # Advanced
        ludocid: Google Place ID.
        kgmid: Google Knowledge Graph ID.

        # Extra
        extra_params: Additional parameters to pass through (ibp, lsig, si, uds, ...).
    """

    query: str
    engine: str = "google"
    num: int = 10
    start: int = 0

    # Localization
    country: Optional[str] = None  # 'gl' for Google
    language: Optional[str] = None  # 'hl' for Google
    google_domain: Optional[str] = None
    countries_filter: Optional[str] = None  # 'cr' parameter
    languages_filter: Optional[str] = None  # 'lr' parameter

    # Geo-targeting
    location: Optional[str] = None
    uule: Optional[str] = None  # Encoded location

    # Search type
    search_type: Optional[str] = None  # tbm parameter (isch, shop, nws, vid, ...)

    # Filters
    safe_search: Optional[bool] = None
    time_filter: Optional[str] = None  # tbs parameter (time part)
    no_autocorrect: bool = False  # nfpr parameter
    filter_duplicates: Optional[bool] = None  # filter parameter

    # Device & Rendering
    device: Optional[str] = None  # 'desktop', 'mobile', 'tablet'
    render_js: Optional[bool] = None  # render_js parameter
    no_cache: Optional[bool] = None  # no_cache parameter

    # Output format
    output_format: str = "json"  # 'json' or 'html'

    # Advanced Google parameters
    ludocid: Optional[str] = None  # Google Place ID
    kgmid: Optional[str] = None  # Knowledge Graph ID

    # Pass-through
    extra_params: Dict[str, Any] = field(default_factory=dict)

    # Search type mappings for tbm parameter
    SEARCH_TYPE_MAP = {
        "images": "isch",
        "shopping": "shop",
        "news": "nws",
        "videos": "vid",
        # Direct values also work
        "isch": "isch",
        "shop": "shop",
        "nws": "nws",
        "vid": "vid",
    }

    # Time filter mappings for tbs parameter
    TIME_FILTER_MAP = {
        "hour": "qdr:h",
        "day": "qdr:d",
        "week": "qdr:w",
        "month": "qdr:m",
        "year": "qdr:y",
    }

    # Engine URL defaults
    ENGINE_URLS = {
        "google": "google.com",
        "bing": "bing.com",
        "yandex": "yandex.com",
        "duckduckgo": "duckduckgo.com",
        "baidu": "baidu.com",
    }

    def to_payload(self) -> Dict[str, Any]:
        """
        Convert to API request payload.

        Returns:
            Dictionary ready to be sent to the SERP API.
        """
        engine = self.engine.lower()

        payload: Dict[str, Any] = {
            "engine": engine,
            "num": str(self.num),
            # output_format: json=1 for JSON, json=0 for raw HTML
            "json": "1" if self.output_format.lower() == "json" else "0",
        }

        # Handle query parameter (Yandex uses 'text', others use 'q')
        if engine == "yandex":
            payload["text"] = self.query
        else:
            payload["q"] = self.query

        # Set URL / domain based on google_domain or engine default
        if self.google_domain:
            # 显式设置 google_domain 参数，同时设置 url
            payload["google_domain"] = self.google_domain
            payload["url"] = self.google_domain
        elif engine in self.ENGINE_URLS:
            payload["url"] = self.ENGINE_URLS[engine]

        # Pagination
        if self.start > 0:
            payload["start"] = str(self.start)

        # Localization
        if self.country:
            payload["gl"] = self.country.lower()

        if self.language:
            payload["hl"] = self.language.lower()

        if self.countries_filter:
            payload["cr"] = self.countries_filter

        if self.languages_filter:
            payload["lr"] = self.languages_filter

        # Geo-targeting
        if self.location:
            payload["location"] = self.location

        if self.uule:
            payload["uule"] = self.uule

        # Search type (tbm)
        if self.search_type:
            search_type_lower = self.search_type.lower()
            tbm_value = self.SEARCH_TYPE_MAP.get(search_type_lower, search_type_lower)
            payload["tbm"] = tbm_value

        # Filters
        if self.safe_search is not None:
            payload["safe"] = "active" if self.safe_search else "off"

        if self.time_filter:
            time_lower = self.time_filter.lower()
            tbs_value = self.TIME_FILTER_MAP.get(time_lower, time_lower)
            payload["tbs"] = tbs_value

        if self.no_autocorrect:
            payload["nfpr"] = "1"

        if self.filter_duplicates is not None:
            payload["filter"] = "1" if self.filter_duplicates else "0"

        # Device
        if self.device:
            payload["device"] = self.device.lower()

        # Rendering & cache control
        if self.render_js is not None:
            payload["render_js"] = "True" if self.render_js else "False"

        if self.no_cache is not None:
            payload["no_cache"] = "True" if self.no_cache else "False"

        # Advanced Google parameters
        if self.ludocid:
            payload["ludocid"] = self.ludocid

        if self.kgmid:
            payload["kgmid"] = self.kgmid

        # Extra parameters (ibp, lsig, si, uds, etc.)
        payload.update(self.extra_params)

        return payload


# =============================================================================
# Universal Scraper (Web Unlocker) Models
# =============================================================================


@dataclass
class UniversalScrapeRequest:
    """
    Configuration for a Universal Scraping API (Web Unlocker) request.

    This API bypasses anti-bot protections like Cloudflare, CAPTCHAs, etc.

    Args:
        url: Target URL to scrape (required).
        js_render: Enable JavaScript rendering with headless browser.
        output_format: Output format - 'html' or 'png' (screenshot).
        country: Country code for geo-targeting the request.
        block_resources: Block specific resources (e.g., 'script', 'image').
        clean_content: Remove JS/CSS from returned content (e.g., 'js,css').
        wait: Wait time in milliseconds after page load (max 100000).
        wait_for: CSS selector to wait for before returning.
        headers: Custom request headers as list of {name, value} dicts.
        cookies: Custom cookies as list of {name, value} dicts.
        extra_params: Additional parameters to pass through.

    Example:
        >>> req = UniversalScrapeRequest(
        ...     url="https://example.com",
        ...     js_render=True,
        ...     output_format="html",
        ...     country="us",
        ...     wait=5000,
        ...     wait_for=".content"
        ... )
        >>> payload = req.to_payload()
    """

    url: str
    js_render: bool = False
    output_format: str = "html"  # 'html' or 'png'
    country: Optional[str] = None
    block_resources: Optional[str] = None  # e.g., 'script', 'image', 'script,image'
    clean_content: Optional[str] = None  # e.g., 'js', 'css', 'js,css'
    wait: Optional[int] = None  # Milliseconds, max 100000
    wait_for: Optional[str] = None  # CSS selector
    headers: Optional[List[Dict[str, str]]] = None  # [{"name": "...", "value": "..."}]
    cookies: Optional[List[Dict[str, str]]] = None  # [{"name": "...", "value": "..."}]
    extra_params: Dict[str, Any] = field(default_factory=dict)  # 这个必须用 field()

    def __post_init__(self) -> None:
        """Validate configuration."""
        valid_formats = {"html", "png"}
        if self.output_format.lower() not in valid_formats:
            raise ValueError(
                f"Invalid output_format: {self.output_format}. "
                f"Must be one of: {', '.join(valid_formats)}"
            )

        if self.wait is not None and (self.wait < 0 or self.wait > 100000):
            raise ValueError(
                f"wait must be between 0 and 100000 milliseconds, got {self.wait}"
            )

    def to_payload(self) -> Dict[str, Any]:
        """
        Convert to API request payload.

        Returns:
            Dictionary ready to be sent to the Universal API.
        """
        payload: Dict[str, Any] = {
            "url": self.url,
            "js_render": "True" if self.js_render else "False",
            "type": self.output_format.lower(),
        }

        if self.country:
            payload["country"] = self.country.lower()

        if self.block_resources:
            payload["block_resources"] = self.block_resources

        if self.clean_content:
            payload["clean_content"] = self.clean_content

        if self.wait is not None:
            payload["wait"] = str(self.wait)

        if self.wait_for:
            payload["wait_for"] = self.wait_for

        if self.headers:
            payload["headers"] = json.dumps(self.headers)

        if self.cookies:
            payload["cookies"] = json.dumps(self.cookies)

        payload.update(self.extra_params)

        return payload


# =============================================================================
# Web Scraper Task Models
# =============================================================================


@dataclass
class ScraperTaskConfig:
    """
    Configuration for creating a Web Scraper API task.

    Note: You must get spider_id and spider_name from the Thordata Dashboard.

    Args:
        file_name: Name for the output file.
        spider_id: Spider identifier from Dashboard.
        spider_name: Spider name (usually the target domain).
        parameters: Spider-specific parameters.
        universal_params: Global spider settings.
        include_errors: Include error details in output.

    Example:
        >>> config = ScraperTaskConfig(
        ...     file_name="youtube_data",
        ...     spider_id="youtube_video-post_by-url",
        ...     spider_name="youtube.com",
        ...     parameters={
        ...         "url": "https://youtube.com/@channel/videos",
        ...         "num_of_posts": "50"
        ...     }
        ... )
        >>> payload = config.to_payload()
    """

    file_name: str
    spider_id: str
    spider_name: str
    parameters: Dict[str, Any]
    universal_params: Optional[Dict[str, Any]] = None
    include_errors: bool = True

    def to_payload(self) -> Dict[str, Any]:
        """
        Convert to API request payload.

        Returns:
            Dictionary ready to be sent to the Web Scraper API.
        """
        payload: Dict[str, Any] = {
            "file_name": self.file_name,
            "spider_id": self.spider_id,
            "spider_name": self.spider_name,
            "spider_parameters": json.dumps([self.parameters]),
            "spider_errors": "true" if self.include_errors else "false",
        }

        if self.universal_params:
            payload["spider_universal"] = json.dumps(self.universal_params)

        return payload


@dataclass
class CommonSettings:
    """
    Common settings for YouTube video/audio downloads.

    Used by /video_builder endpoint as `common_settings` parameter.
    Also known as `spider_universal` in some documentation.

    Args:
        resolution: Video resolution (360p/480p/720p/1080p/1440p/2160p).
        audio_format: Audio format (opus/mp3).
        bitrate: Audio bitrate (48/64/128/160/256/320 or with Kbps suffix).
        is_subtitles: Whether to download subtitles ("true"/"false").
        subtitles_language: Subtitle language code (e.g., "en", "zh-Hans").

    Example for video:
        >>> settings = CommonSettings(
        ...     resolution="1080p",
        ...     is_subtitles="true",
        ...     subtitles_language="en"
        ... )

    Example for audio:
        >>> settings = CommonSettings(
        ...     audio_format="mp3",
        ...     bitrate="320",
        ...     is_subtitles="true",
        ...     subtitles_language="en"
        ... )
    """

    # Video settings
    resolution: Optional[str] = None

    # Audio settings
    audio_format: Optional[str] = None
    bitrate: Optional[str] = None

    # Subtitle settings (used by both video and audio)
    is_subtitles: Optional[str] = None
    subtitles_language: Optional[str] = None

    # Valid values for validation
    VALID_RESOLUTIONS = {"360p", "480p", "720p", "1080p", "1440p", "2160p"}
    VALID_AUDIO_FORMATS = {"opus", "mp3"}

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary, excluding None values."""
        result = {}
        if self.resolution is not None:
            result["resolution"] = self.resolution
        if self.audio_format is not None:
            result["audio_format"] = self.audio_format
        if self.bitrate is not None:
            result["bitrate"] = self.bitrate
        if self.is_subtitles is not None:
            result["is_subtitles"] = self.is_subtitles
        if self.subtitles_language is not None:
            result["subtitles_language"] = self.subtitles_language
        return result

    def to_json(self) -> str:
        """Convert to JSON string for form submission."""
        return json.dumps(self.to_dict())


@dataclass
class VideoTaskConfig:
    """
    Configuration for creating a YouTube video/audio download task.

    Uses the /video_builder endpoint.

    Args:
        file_name: Name for the output file. Supports {{TasksID}}, {{VideoID}}.
        spider_id: Spider identifier (e.g., "youtube_video_by-url", "youtube_audio_by-url").
        spider_name: Spider name (typically "youtube.com").
        parameters: Spider-specific parameters (e.g., video URL).
        common_settings: Video/audio settings (resolution, format, subtitles).
        include_errors: Include error details in output.

    Example:
        >>> config = VideoTaskConfig(
        ...     file_name="{{VideoID}}",
        ...     spider_id="youtube_video_by-url",
        ...     spider_name="youtube.com",
        ...     parameters={"url": "https://www.youtube.com/watch?v=xxx"},
        ...     common_settings=CommonSettings(
        ...         resolution="1080p",
        ...         is_subtitles="true",
        ...         subtitles_language="en"
        ...     )
        ... )
    """

    file_name: str
    spider_id: str
    spider_name: str
    parameters: Dict[str, Any]
    common_settings: CommonSettings
    include_errors: bool = True

    def to_payload(self) -> Dict[str, Any]:
        """
        Convert to API request payload.

        Returns:
            Dictionary ready to be sent to the video_builder API.
        """
        payload: Dict[str, Any] = {
            "file_name": self.file_name,
            "spider_id": self.spider_id,
            "spider_name": self.spider_name,
            "spider_parameters": json.dumps([self.parameters]),
            "spider_errors": "true" if self.include_errors else "false",
            "common_settings": self.common_settings.to_json(),
        }
        return payload


# =============================================================================
# Response Models
# =============================================================================


@dataclass
class TaskStatusResponse:
    """
    Response from task status check.

    Attributes:
        task_id: The task identifier.
        status: Current task status.
        progress: Optional progress percentage.
        message: Optional status message.
    """

    task_id: str
    status: str
    progress: Optional[int] = None
    message: Optional[str] = None

    def is_complete(self) -> bool:
        """Check if the task has completed (success or failure)."""
        terminal_statuses = {
            "ready",
            "success",
            "finished",
            "failed",
            "error",
            "cancelled",
        }
        return self.status.lower() in terminal_statuses

    def is_success(self) -> bool:
        """Check if the task completed successfully."""
        success_statuses = {"ready", "success", "finished"}
        return self.status.lower() in success_statuses

    def is_failed(self) -> bool:
        """Check if the task failed."""
        failure_statuses = {"failed", "error"}
        return self.status.lower() in failure_statuses


@dataclass
class UsageStatistics:
    """
    Response model for account usage statistics.

    Attributes:
        total_usage_traffic: Total traffic used (KB).
        traffic_balance: Remaining traffic balance (KB).
        query_days: Number of days in the query range.
        range_usage_traffic: Traffic used in the specified date range (KB).
        data: Daily usage breakdown.
    """

    total_usage_traffic: float
    traffic_balance: float
    query_days: int
    range_usage_traffic: float
    data: List[Dict[str, Any]]

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "UsageStatistics":
        """Create from API response dict."""
        return cls(
            total_usage_traffic=float(data.get("total_usage_traffic", 0)),
            traffic_balance=float(data.get("traffic_balance", 0)),
            query_days=int(data.get("query_days", 0)),
            range_usage_traffic=float(data.get("range_usage_traffic", 0)),
            data=data.get("data", []),
        )

    def total_usage_gb(self) -> float:
        """Get total usage in GB."""
        return self.total_usage_traffic / (1024 * 1024)

    def balance_gb(self) -> float:
        """Get balance in GB."""
        return self.traffic_balance / (1024 * 1024)

    def range_usage_gb(self) -> float:
        """Get range usage in GB."""
        return self.range_usage_traffic / (1024 * 1024)


@dataclass
class ProxyUser:
    """
    Proxy user (sub-account) information.

    Attributes:
        username: User's username.
        password: User's password.
        status: User status (True=enabled, False=disabled).
        traffic_limit: Traffic limit in MB (0 = unlimited).
        usage_traffic: Traffic used in KB.
    """

    username: str
    password: str
    status: bool
    traffic_limit: int
    usage_traffic: float

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ProxyUser":
        """Create from API response dict."""
        return cls(
            username=data.get("username", ""),
            password=data.get("password", ""),
            status=data.get("status") in (True, "true", 1),
            traffic_limit=int(data.get("traffic_limit", 0)),
            usage_traffic=float(data.get("usage_traffic", 0)),
        )

    def usage_gb(self) -> float:
        """Get usage in GB."""
        return self.usage_traffic / (1024 * 1024)

    def limit_gb(self) -> float:
        """Get limit in GB (0 means unlimited)."""
        if self.traffic_limit == 0:
            return 0
        return self.traffic_limit / 1024


@dataclass
class ProxyUserList:
    """
    Response model for proxy user list.

    Attributes:
        limit: Total traffic limit (KB).
        remaining_limit: Remaining traffic limit (KB).
        user_count: Number of users.
        users: List of proxy users.
    """

    limit: float
    remaining_limit: float
    user_count: int
    users: List[ProxyUser]

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ProxyUserList":
        """Create from API response dict."""
        user_list = data.get("list", [])
        users = [ProxyUser.from_dict(u) for u in user_list]

        return cls(
            limit=float(data.get("limit", 0)),
            remaining_limit=float(data.get("remaining_limit", 0)),
            user_count=int(data.get("user_count", len(users))),
            users=users,
        )


@dataclass
class ProxyServer:
    """
    ISP or Datacenter proxy server information.

    Attributes:
        ip: Proxy server IP address.
        port: Proxy server port.
        username: Authentication username.
        password: Authentication password.
        expiration_time: Expiration timestamp (Unix timestamp or datetime string).
        region: Server region (optional).
    """

    ip: str
    port: int
    username: str
    password: str
    expiration_time: Optional[Union[int, str]] = None
    region: Optional[str] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ProxyServer":
        """Create from API response dict."""
        return cls(
            ip=data.get("ip", ""),
            port=int(data.get("port", 0)),
            username=data.get("username", data.get("user", "")),
            password=data.get("password", data.get("pwd", "")),
            expiration_time=data.get("expiration_time", data.get("expireTime")),
            region=data.get("region"),
        )

    def to_proxy_url(self, protocol: str = "http") -> str:
        """
        Build proxy URL for this server.

        Args:
            protocol: Proxy protocol (http/https/socks5).

        Returns:
            Complete proxy URL.
        """
        return f"{protocol}://{self.username}:{self.password}@{self.ip}:{self.port}"

    def is_expired(self) -> bool:
        """Check if proxy has expired (if expiration_time is available)."""
        if self.expiration_time is None:
            return False

        import time

        if isinstance(self.expiration_time, int):
            return time.time() > self.expiration_time

        # String timestamp handling would need datetime parsing
        return False
