import os
import time

import pytest
from dotenv import load_dotenv

from thordata import ThordataClient
from thordata.models import ProxyConfig, ProxyProduct

TARGET = "https://ipinfo.thordata.com"

RUN = (os.getenv("THORDATA_INTEGRATION") or "").strip().lower() == "true"
STRICT = (os.getenv("THORDATA_INTEGRATION_STRICT") or "").strip().lower() == "true"

if not RUN:
    pytest.skip(
        "integration disabled (set THORDATA_INTEGRATION=true)", allow_module_level=True
    )

pytestmark = pytest.mark.integration


def _must(k: str) -> str:
    v = (os.getenv(k) or "").strip()
    if not v:
        pytest.skip(f"missing {k}")
    return v


def _looks_like_interference(e: Exception) -> bool:
    s = str(e).lower()
    return any(
        x in s
        for x in [
            "wrong version number",
            "packet length too long",
            "server gave http response to https client",
            "hpe_cr_expected",
            "parse error",
            "econnreset",
            "socket hang up",
            "unexpected_message",
        ]
    )


def test_proxy_https_socks5h_integration():
    load_dotenv(".env")

    upstream = os.getenv("THORDATA_UPSTREAM_PROXY", "").strip()
    if not upstream:
        # 没有前置代理，清除环境变量避免意外双重代理
        for k in [
            "HTTP_PROXY",
            "HTTPS_PROXY",
            "ALL_PROXY",
            "NO_PROXY",
            "http_proxy",
            "https_proxy",
            "all_proxy",
            "no_proxy",
        ]:
            os.environ.pop(k, None)

    host = _must("THORDATA_PROXY_HOST")
    port = int((os.getenv("THORDATA_PROXY_PORT") or "9999").strip())
    u = _must("THORDATA_RESIDENTIAL_USERNAME")
    p = _must("THORDATA_RESIDENTIAL_PASSWORD")

    client = ThordataClient(scraper_token=os.getenv("THORDATA_SCRAPER_TOKEN", "dummy"))

    # 当有 upstream proxy 时，HTTPS 代理协议可能不支持（TLS-in-TLS 问题）
    # 优先使用 http 或 socks5h
    if upstream:
        protos = ["https", "socks5h"]
    else:
        protos = ["https", "socks5h"]
        if (os.getenv("THORDATA_INTEGRATION_HTTP") or "").strip().lower() == "true":
            protos.insert(0, "http")

    for proto in protos:
        print(f"\n--- Testing protocol: {proto} ---")
        proxy = ProxyConfig(
            username=u,
            password=p,
            product=ProxyProduct.RESIDENTIAL,
            host=host,
            port=port,
            protocol=proto,
            country="us",
        )

        last = None
        for attempt in range(3):
            try:
                print(f"  Attempt {attempt + 1}/3...")
                r = client.get(TARGET, proxy_config=proxy, timeout=60)
                print(f"  Status: {r.status_code}")
                assert r.status_code == 200
                print(f"  ✓ {proto} passed!")
                last = None
                break
            except Exception as e:
                print(f"  ✗ Error: {e}")
                last = e
                time.sleep(2)

        if last is not None:
            if not STRICT and _looks_like_interference(last):
                pytest.skip(
                    f"skipping due to local proxy/TUN interference: proto={proto} err={last}"
                )
            raise last
