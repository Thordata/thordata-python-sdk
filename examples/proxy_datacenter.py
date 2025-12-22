"""
Datacenter Proxy Demo

Usage:
    python examples/proxy_datacenter.py
"""

import os
import sys

from dotenv import load_dotenv

load_dotenv()

USERNAME = os.getenv("THORDATA_DATACENTER_USERNAME")
PASSWORD = os.getenv("THORDATA_DATACENTER_PASSWORD")

if not USERNAME or not PASSWORD:
    print("Datacenter Proxy Demo - Skipped")
    print("Set THORDATA_DATACENTER_USERNAME and THORDATA_DATACENTER_PASSWORD in .env")
    sys.exit(0)

import requests

from thordata import ProxyConfig, ProxyProduct


def main():
    print("Datacenter Proxy Demo\n")

    proxy = ProxyConfig(
        username=USERNAME,
        password=PASSWORD,
        product=ProxyProduct.DATACENTER,
    )

    try:
        response = requests.get(
            "http://httpbin.org/ip",
            proxies=proxy.to_proxies_dict(),
            timeout=30,
        )
        print(f"Datacenter IP: {response.json().get('origin')}")
    except Exception as e:
        print(f"Failed: {e}")


if __name__ == "__main__":
    main()
