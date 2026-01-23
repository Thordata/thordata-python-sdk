"""
Core networking modules for Thordata SDK.
"""

from .async_http_client import AsyncThordataHttpSession
from .http_client import ThordataHttpSession
from .tunnel import (
    HAS_PYSOCKS,
    UpstreamProxySocketFactory,
    create_tls_in_tls,
    parse_upstream_proxy,
    socks5_handshake,
)

__all__ = [
    "ThordataHttpSession",
    "AsyncThordataHttpSession",
    "parse_upstream_proxy",
    "UpstreamProxySocketFactory",
    "create_tls_in_tls",
    "socks5_handshake",
    "HAS_PYSOCKS",
]
