"""
Mobile Proxy Demo

Usage:
    python examples/proxy_mobile.py
"""

import os
from pathlib import Path

import requests
from dotenv import load_dotenv

from thordata import ProxyConfig, ProxyProduct

load_dotenv(dotenv_path=Path(__file__).resolve().parents[1] / ".env")

USERNAME = os.getenv("THORDATA_MOBILE_USERNAME")
PASSWORD = os.getenv("THORDATA_MOBILE_PASSWORD")


def main():
    if not USERNAME or not PASSWORD:
        print("Mobile Proxy Demo - Skipped")
        print("Set THORDATA_MOBILE_USERNAME and THORDATA_MOBILE_PASSWORD in .env")
        return

    print("Mobile Proxy Demo\n")

    proxy = ProxyConfig(
        username=USERNAME,
        password=PASSWORD,
        product=ProxyProduct.MOBILE,
        country="gb",
    )

    try:
        response = requests.get(
            "http://httpbin.org/ip",
            proxies=proxy.to_proxies_dict(),
            timeout=30,
        )
        print(f"UK Mobile IP: {response.json().get('origin')}")
    except Exception as e:
        print(f"Failed: {e}")


if __name__ == "__main__":
    main()
