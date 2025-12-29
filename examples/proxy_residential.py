"""
Residential Proxy Demo

Demonstrates residential proxy with geo-targeting and sticky sessions.

Usage:
    python examples/proxy_residential.py
"""

import os
import sys
from pathlib import Path

import requests
from dotenv import load_dotenv

from thordata import ProxyConfig, ProxyProduct, StickySession

load_dotenv(dotenv_path=Path(__file__).resolve().parents[1] / ".env")

USERNAME = os.getenv("THORDATA_RESIDENTIAL_USERNAME")
PASSWORD = os.getenv("THORDATA_RESIDENTIAL_PASSWORD")


def main():
    if not USERNAME or not PASSWORD:
        print("Residential Proxy Demo - Skipped")
        print(
            "Set THORDATA_RESIDENTIAL_USERNAME and THORDATA_RESIDENTIAL_PASSWORD in .env"
        )
        return

    print("Residential Proxy Demo\n")

    # Basic geo-targeted request
    proxy = ProxyConfig(
        username=USERNAME,
        password=PASSWORD,
        product=ProxyProduct.RESIDENTIAL,
        country="us",
    )

    print("1. US Residential Request")
    try:
        response = requests.get(
            "http://httpbin.org/ip",
            proxies=proxy.to_proxies_dict(),
            timeout=30,
        )
        print(f"   IP: {response.json().get('origin')}")
    except Exception as e:
        print(f"   Failed: {e}")

    # Sticky session
    print("\n2. Sticky Session (Tokyo, 10 min)")
    session = StickySession(
        username=USERNAME,
        password=PASSWORD,
        product=ProxyProduct.RESIDENTIAL,
        country="jp",
        city="tokyo",
        duration_minutes=10,
    )

    for i in range(2):
        try:
            response = requests.get(
                "http://httpbin.org/ip",
                proxies=session.to_proxies_dict(),
                timeout=30,
            )
            print(f"   Request {i + 1}: {response.json().get('origin')}")
        except Exception as e:
            print(f"   Request {i + 1}: Failed - {e}")


if __name__ == "__main__":
    main()
