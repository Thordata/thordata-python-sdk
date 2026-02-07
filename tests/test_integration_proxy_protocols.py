import os

import pytest

# Load .env file first
try:
    from dotenv import load_dotenv

    load_dotenv(".env")
except ImportError:
    from thordata.env import load_env_file

    load_env_file(".env")

from thordata import ThordataClient
from thordata.models import ProxyConfig, ProxyProduct, StaticISPProxy

TARGET = "https://ipinfo.thordata.com"

RUN_INTEGRATION = (os.getenv("THORDATA_INTEGRATION") or "").strip().lower() == "true"
IS_CI = (os.getenv("GITHUB_ACTIONS") or "").strip().lower() == "true"
FORCE = (os.getenv("THORDATA_INTEGRATION_FORCE") or "").strip().lower() == "true"

pytestmark = pytest.mark.integration


def _should_run_integration() -> tuple[bool, str]:
    if not RUN_INTEGRATION:
        return False, "THORDATA_INTEGRATION is not true"
    # Local dev (e.g. mainland China) often cannot run proxy integration reliably.
    # Only run locally if explicitly forced.
    if not IS_CI and not FORCE:
        return (
            False,
            "skipping local proxy integration (set THORDATA_INTEGRATION_FORCE=true to run locally)",
        )
    return True, ""


def _get_client():
    return ThordataClient(scraper_token=os.getenv("THORDATA_SCRAPER_TOKEN", "dummy"))


def _check_connectivity(name, proxy_config, protocols):
    """Helper to test a product across multiple protocols."""
    run, reason = _should_run_integration()
    if not run:
        pytest.skip(reason)

    client = _get_client()
    success_any = False
    errors = []

    print(f"\n[INTEGRATION] Product: {name}")
    for proto in protocols:
        proxy_config.protocol = proto
        print(f"  Testing {proto}...", end=" ", flush=True)
        try:
            # 20s is plenty for an overseas runner
            r = client.get(TARGET, proxy_config=proxy_config, timeout=20)
            if r.status_code == 200:
                print(f"PASSED (IP: {r.json().get('origin')})")
                success_any = True
            else:
                msg = f"HTTP {r.status_code}"
                print(f"FAILED ({msg})")
                errors.append(f"{proto}: {msg}")
        except Exception as e:
            msg = str(e)
            print(f"FAILED ({msg[:50]}...)")
            errors.append(f"{proto}: {msg}")

    return success_any, errors


def test_residential_connectivity():
    u = os.getenv("THORDATA_RESIDENTIAL_USERNAME")
    p = os.getenv("THORDATA_RESIDENTIAL_PASSWORD")
    host = os.getenv("THORDATA_PROXY_HOST", "vpn9wq0d.pr.thordata.net")
    if not (u and p):
        pytest.skip("Missing residential credentials")

    proxy = ProxyConfig(
        username=u, password=p, host=host, port=9999, product=ProxyProduct.RESIDENTIAL
    )
    # Test common protocols for residential
    success, errs = _check_connectivity("Residential", proxy, ["http", "socks5h"])
    assert success, f"Residential failed all protocols: {errs}"


def test_mobile_connectivity():
    u = os.getenv("THORDATA_MOBILE_USERNAME")
    p = os.getenv("THORDATA_MOBILE_PASSWORD")
    host = os.getenv("THORDATA_PROXY_HOST", "vpn9wq0d.pr.thordata.net")
    if not (u and p):
        pytest.skip("Missing mobile credentials")

    proxy = ProxyConfig(
        username=u, password=p, host=host, port=5555, product=ProxyProduct.MOBILE
    )
    success, errs = _check_connectivity("Mobile", proxy, ["http", "socks5h"])
    assert success, f"Mobile failed all protocols: {errs}"


def test_datacenter_connectivity():
    u = os.getenv("THORDATA_DATACENTER_USERNAME")
    p = os.getenv("THORDATA_DATACENTER_PASSWORD")
    host = os.getenv("THORDATA_PROXY_HOST", "vpn9wq0d.pr.thordata.net")
    if not (u and p):
        pytest.skip("Missing datacenter credentials")

    proxy = ProxyConfig(
        username=u, password=p, host=host, port=7777, product=ProxyProduct.DATACENTER
    )
    success, errs = _check_connectivity("Datacenter", proxy, ["http", "socks5h"])
    assert success, f"Datacenter failed all protocols: {errs}"


def test_isp_connectivity():
    host = os.getenv("THORDATA_ISP_HOST")
    u = os.getenv("THORDATA_ISP_USERNAME")
    p = os.getenv("THORDATA_ISP_PASSWORD")
    if not (host and u and p):
        pytest.skip("Missing ISP credentials")

    proxy = StaticISPProxy(
        host=host, username=u, password=p, port=6666, protocol="http"
    )
    success, errs = _check_connectivity("ISP", proxy, ["http"])
    assert success, f"ISP failed all protocols: {errs}"
