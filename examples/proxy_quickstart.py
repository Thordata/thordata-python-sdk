"""
Proxy Quick Start - Basic Usage

Demonstrates:
- Basic proxy request
- Geo-targeting with ProxyConfig
- Sticky sessions with StickySession

Usage:
    python examples/proxy_quickstart.py
"""

import logging
import os
import sys

from dotenv import load_dotenv

from thordata import (
    ProxyConfig,
    StickySession,
    ThordataClient,
    ThordataError,
)

logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")

load_dotenv()

SCRAPER_TOKEN = os.getenv("THORDATA_SCRAPER_TOKEN")
USERNAME = os.getenv("THORDATA_USERNAME")
PASSWORD = os.getenv("THORDATA_PASSWORD")

if not SCRAPER_TOKEN:
    print("❌ Error: THORDATA_SCRAPER_TOKEN is missing in .env")
    print("   Copy .env.example to .env and fill in your credentials.")
    sys.exit(1)


def demo_basic_request():
    """Basic proxy request without geo-targeting."""
    print("\n" + "=" * 50)
    print("1️⃣  Basic Proxy Request")
    print("=" * 50)

    client = ThordataClient(scraper_token=SCRAPER_TOKEN)

    try:
        response = client.get("https://httpbin.org/ip", timeout=30)
        response.raise_for_status()

        data = response.json()
        print("✅ Success!")
        print(f"   Proxy IP: {data.get('origin')}")

    except ThordataError as e:
        print(f"❌ Request failed: {e}")


def demo_geo_targeting():
    """Geo-targeted request using ProxyConfig."""
    print("\n" + "=" * 50)
    print("2️⃣  Geo-Targeted Request (US)")
    print("=" * 50)

    if not USERNAME or not PASSWORD:
        print("⚠️  Skipped: THORDATA_USERNAME and THORDATA_PASSWORD required")
        return

    client = ThordataClient(scraper_token=SCRAPER_TOKEN)

    # Build proxy config with geo-targeting
    proxy_config = ProxyConfig(
        username=USERNAME,
        password=PASSWORD,
        country="us",
        state="california",
    )

    print("   Target: US - California")
    print(f"   Username: {proxy_config.build_username()}")

    try:
        response = client.get(
            "https://ipinfo.io/json",
            proxy_config=proxy_config,
            timeout=30,
        )
        response.raise_for_status()

        data = response.json()
        print("✅ Success!")
        print(f"   IP: {data.get('ip')}")
        print(f"   Country: {data.get('country')}")
        print(f"   Region: {data.get('region')}")
        print(f"   City: {data.get('city')}")

    except ThordataError as e:
        print(f"❌ Request failed: {e}")


def demo_sticky_session():
    """Sticky session - same IP for multiple requests."""
    print("\n" + "=" * 50)
    print("3️⃣  Sticky Session (Same IP)")
    print("=" * 50)

    if not USERNAME or not PASSWORD:
        print("⚠️  Skipped: THORDATA_USERNAME and THORDATA_PASSWORD required")
        return

    client = ThordataClient(scraper_token=SCRAPER_TOKEN)

    # Create sticky session (auto-generates session ID)
    session = StickySession(
        username=USERNAME,
        password=PASSWORD,
        country="gb",
        duration_minutes=10,
    )

    print(f"   Session ID: {session.session_id}")
    print("   Duration: 10 minutes")
    print("   Making 3 requests...")

    ips = []
    for i in range(3):
        try:
            response = client.get(
                "https://httpbin.org/ip",
                proxy_config=session,
                timeout=30,
            )
            response.raise_for_status()
            ip = response.json().get("origin")
            ips.append(ip)
            print(f"   Request {i + 1}: {ip}")

        except ThordataError as e:
            print(f"   Request {i + 1}: ❌ {e}")

    # Check if all IPs are the same
    if ips and len(set(ips)) == 1:
        print("✅ All requests used the same IP!")
    elif ips:
        print(f"⚠️  Got {len(set(ips))} different IPs")


if __name__ == "__main__":
    print("=" * 50)
    print("   Thordata SDK - Proxy Quick Start")
    print("=" * 50)

    demo_basic_request()
    demo_geo_targeting()
    demo_sticky_session()

    print("\n" + "=" * 50)
    print("   Demo Complete!")
    print("=" * 50)
