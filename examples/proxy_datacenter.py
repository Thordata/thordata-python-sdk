"""
Datacenter Proxy Demo

Usage:
    python examples/proxy_datacenter.py
"""

import os
from pathlib import Path

import requests
from dotenv import load_dotenv

from thordata import ProxyConfig, ProxyProduct
from thordata._example_utils import load_env, skip_if_missing

load_dotenv(dotenv_path=Path(__file__).resolve().parents[1] / ".env")

USERNAME = os.getenv("THORDATA_DATACENTER_USERNAME")
PASSWORD = os.getenv("THORDATA_DATACENTER_PASSWORD")


def main():
    load_env()
    if skip_if_missing(
        ["THORDATA_SCRAPER_TOKEN"],
        tip="Proxy example requires THORDATA_SCRAPER_TOKEN (and proxy settings depending on product).",
    ):
        return 0
    if not USERNAME or not PASSWORD:
        print("Datacenter Proxy Demo - Skipped")
        print(
            "Set THORDATA_DATACENTER_USERNAME and THORDATA_DATACENTER_PASSWORD in .env"
        )
        return

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
