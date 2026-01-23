"""
Proxy related types and configurations.
"""

from __future__ import annotations

import re
import uuid
from dataclasses import dataclass
from enum import Enum, IntEnum
from typing import Any
from urllib.parse import quote

# Import geography from common to avoid circular issues
from .common import Continent


class ProxyProduct(str, Enum):
    RESIDENTIAL = "residential"
    MOBILE = "mobile"
    DATACENTER = "datacenter"
    ISP = "isp"

    @property
    def default_port(self) -> int:
        ports = {
            "residential": 9999,
            "mobile": 5555,
            "datacenter": 7777,
            "isp": 6666,
        }
        return ports.get(self.value, 9999)


class ProxyType(IntEnum):
    RESIDENTIAL = 1
    UNLIMITED = 2
    DATACENTER = 3
    ISP = 4
    MOBILE = 5


class SessionType(str, Enum):
    ROTATING = "rotating"
    STICKY = "sticky"


class ProxyHost(str, Enum):
    DEFAULT = "pr.thordata.net"
    NORTH_AMERICA = "t.na.thordata.net"
    EUROPE = "t.eu.thordata.net"


class ProxyPort(IntEnum):
    RESIDENTIAL = 9999
    MOBILE = 5555
    DATACENTER = 7777
    ISP = 6666


@dataclass
class ProxyConfig:
    username: str
    password: str
    product: ProxyProduct | str = ProxyProduct.RESIDENTIAL
    host: str | None = None
    port: int | None = None
    protocol: str = "https"

    # Geo-targeting
    continent: str | None = None
    country: str | None = None
    state: str | None = None
    city: str | None = None
    asn: str | None = None

    # Session control
    session_id: str | None = None
    session_duration: int | None = None  # minutes, 1-90

    # Use a set of values for validation logic
    _VALID_CONTINENTS = {v.value for v in Continent}

    def __post_init__(self) -> None:
        if isinstance(self.product, str):
            self.product = ProxyProduct(self.product.lower())

        if self.host is None:
            host_map = {
                ProxyProduct.RESIDENTIAL: "pr.thordata.net",
                ProxyProduct.DATACENTER: "dc.pr.thordata.net",
                ProxyProduct.MOBILE: "m.pr.thordata.net",
                ProxyProduct.ISP: "isp.pr.thordata.net",
            }
            self.host = host_map.get(self.product, "pr.thordata.net")

        if self.port is None:
            self.port = self.product.default_port

        self._validate()

    def _validate(self) -> None:
        if self.protocol not in ("http", "https", "socks5", "socks5h"):
            raise ValueError(f"Invalid protocol: {self.protocol}")

        if self.session_duration is not None:
            if not 1 <= self.session_duration <= 90:
                raise ValueError("session_duration must be between 1 and 90 minutes")
            if not self.session_id:
                raise ValueError("session_duration requires session_id")

        if self.asn and not self.country:
            raise ValueError("ASN targeting requires country")

        if self.continent and self.continent.lower() not in self._VALID_CONTINENTS:
            raise ValueError(f"Invalid continent code: {self.continent}")

        if self.country and not re.match(r"^[a-zA-Z]{2}$", self.country):
            raise ValueError("Invalid country code")

    def build_username(self) -> str:
        base = self.username
        if not base.startswith("td-customer-"):
            base = f"td-customer-{base}"

        parts = [base]

        if self.continent:
            parts.append(f"continent-{self.continent.lower()}")
        if self.country:
            parts.append(f"country-{self.country.lower()}")
        if self.state:
            parts.append(f"state-{self.state.lower()}")
        if self.city:
            parts.append(f"city-{self.city.lower()}")
        if self.asn:
            asn_val = (
                self.asn.upper()
                if self.asn.upper().startswith("AS")
                else f"AS{self.asn.upper()}"
            )
            parts.append(f"asn-{asn_val}")
        if self.session_id:
            parts.append(f"sessid-{self.session_id}")
        if self.session_duration:
            parts.append(f"sesstime-{self.session_duration}")

        return "-".join(parts)

    def build_proxy_url(self) -> str:
        user = self.build_username()
        proto = "socks5h" if self.protocol == "socks5" else self.protocol

        safe_user = quote(user, safe="")
        safe_pass = quote(self.password, safe="")

        return f"{proto}://{safe_user}:{safe_pass}@{self.host}:{self.port}"

    def build_proxy_endpoint(self) -> str:
        proto = "socks5h" if self.protocol == "socks5" else self.protocol
        return f"{proto}://{self.host}:{self.port}"

    def build_proxy_basic_auth(self) -> str:
        return f"{self.build_username()}:{self.password}"

    def to_proxies_dict(self) -> dict[str, str]:
        url = self.build_proxy_url()
        return {"http": url, "https": url}

    def to_aiohttp_config(self) -> tuple:
        try:
            import aiohttp

            return (
                f"{self.protocol}://{self.host}:{self.port}",
                aiohttp.BasicAuth(login=self.build_username(), password=self.password),
            )
        except ImportError as e:
            # Fix B904: chain the exception
            raise ImportError("aiohttp required") from e


@dataclass
class StaticISPProxy:
    host: str
    username: str
    password: str
    port: int = 6666
    protocol: str = "https"

    def __post_init__(self) -> None:
        if self.protocol not in ("http", "https", "socks5", "socks5h"):
            raise ValueError(f"Invalid protocol: {self.protocol}")

    def build_username(self) -> str:
        # Static ISP usually doesn't use the 'td-customer-' prefix logic
        # or special params, it uses raw username.
        return self.username

    def build_proxy_endpoint(self) -> str:
        # FIX: Added this method to satisfy client.py interface
        proto = "socks5h" if self.protocol == "socks5" else self.protocol
        return f"{proto}://{self.host}:{self.port}"

    def build_proxy_basic_auth(self) -> str:
        # FIX: Added this method to satisfy client.py interface
        return f"{self.username}:{self.password}"

    def build_proxy_url(self) -> str:
        proto = "socks5h" if self.protocol == "socks5" else self.protocol
        safe_user = quote(self.username, safe="")
        safe_pass = quote(self.password, safe="")
        return f"{proto}://{safe_user}:{safe_pass}@{self.host}:{self.port}"

    def to_proxies_dict(self) -> dict[str, str]:
        url = self.build_proxy_url()
        return {"http": url, "https": url}

    def to_aiohttp_config(self) -> tuple:
        try:
            import aiohttp

            return (
                f"{self.protocol}://{self.host}:{self.port}",
                aiohttp.BasicAuth(login=self.username, password=self.password),
            )
        except ImportError as e:
            # Fix B904: chain the exception
            raise ImportError("aiohttp required") from e

    @classmethod
    def from_env(cls) -> StaticISPProxy:
        import os

        host = os.getenv("THORDATA_ISP_HOST")
        username = os.getenv("THORDATA_ISP_USERNAME")
        password = os.getenv("THORDATA_ISP_PASSWORD")
        if not all([host, username, password]):
            raise ValueError(
                "THORDATA_ISP_HOST, THORDATA_ISP_USERNAME, and THORDATA_ISP_PASSWORD are required"
            )
        return cls(host=host, username=username, password=password)  # type: ignore


@dataclass
class StickySession(ProxyConfig):
    duration_minutes: int = 10
    auto_session_id: bool = True

    def __post_init__(self) -> None:
        if self.auto_session_id and not self.session_id:
            self.session_id = uuid.uuid4().hex[:12]
        self.session_duration = self.duration_minutes
        super().__post_init__()


@dataclass
class ProxyUser:
    username: str
    password: str
    status: bool
    traffic_limit: int
    usage_traffic: float

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ProxyUser:
        return cls(
            username=str(data.get("username", "")),
            password=str(data.get("password", "")),
            status=str(data.get("status")).lower() in ("true", "1"),
            traffic_limit=int(data.get("traffic_limit", 0)),
            usage_traffic=float(data.get("usage_traffic", 0)),
        )

    def usage_gb(self) -> float:
        return self.usage_traffic / (1024 * 1024)

    def limit_gb(self) -> float:
        if self.traffic_limit == 0:
            return 0.0
        return self.traffic_limit / 1024.0


@dataclass
class ProxyUserList:
    limit: float
    remaining_limit: float
    user_count: int
    users: list[ProxyUser]

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ProxyUserList:
        user_list_raw = data.get("list")
        if user_list_raw is None:
            possible_data = data.get("data")
            user_list_raw = possible_data if isinstance(possible_data, list) else []
        if not isinstance(user_list_raw, list):
            user_list_raw = []

        users = [ProxyUser.from_dict(u) for u in user_list_raw]

        return cls(
            limit=float(data.get("limit", 0)),
            remaining_limit=float(data.get("remaining_limit", 0)),
            user_count=int(data.get("user_count", len(users))),
            users=users,
        )


@dataclass
class ProxyServer:
    ip: str
    port: int
    username: str
    password: str
    expiration_time: int | str | None = None
    region: str | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ProxyServer:
        return cls(
            ip=str(data.get("ip", "")),
            port=int(data.get("port", 0)),
            username=str(data.get("username", data.get("user", ""))),
            password=str(data.get("password", data.get("pwd", ""))),
            expiration_time=data.get("expiration_time", data.get("expireTime")),
            region=str(data.get("region")) if data.get("region") else None,
        )

    def to_proxy_url(self, protocol: str = "https") -> str:
        return f"{protocol}://{self.username}:{self.password}@{self.ip}:{self.port}"

    def is_expired(self) -> bool:
        if self.expiration_time is None:
            return False
        import time

        if isinstance(self.expiration_time, int):
            return time.time() > self.expiration_time
        return False
