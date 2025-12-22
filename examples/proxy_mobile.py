"""
Mobile Proxy Demo

Usage:
    python examples/proxy_mobile.py
"""

import os
import sys

from dotenv import load_dotenv

load_dotenv()

USERNAME = os.getenv("THORDATA_MOBILE_USERNAME")
PASSWORD = os.getenv("THORDATA_MOBILE_PASSWORD")

if not USERNAME or not PASSWORD:
    print("Mobile Proxy Demo - Skipped")
    print("Set THORDATA_MOBILE_USERNAME and THORDATA_MOBILE_PASSWORD in .env")
    sys.exit(0)

import requests

from thordata import ProxyConfig, ProxyProduct


def main():
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
