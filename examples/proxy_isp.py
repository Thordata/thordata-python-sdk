"""
Static ISP Proxy Demo

Static ISP proxies use direct IP connection (not gateway).

Usage:
    python examples/proxy_isp.py
"""

import os
from pathlib import Path

import requests
from dotenv import load_dotenv

from thordata import StaticISPProxy

load_dotenv(dotenv_path=Path(__file__).resolve().parents[1] / ".env")

HOST = os.getenv("THORDATA_ISP_HOST")
USERNAME = os.getenv("THORDATA_ISP_USERNAME")
PASSWORD = os.getenv("THORDATA_ISP_PASSWORD")


def main():
    if not HOST or not USERNAME or not PASSWORD:
        print("Static ISP Proxy Demo - Skipped")
        print(
            "Set THORDATA_ISP_HOST, THORDATA_ISP_USERNAME, and THORDATA_ISP_PASSWORD in .env"
        )
        return

    print("Static ISP Proxy Demo\n")

    proxy = StaticISPProxy(
        host=HOST,
        username=USERNAME,
        password=PASSWORD,
    )

    print(f"Expected IP: {HOST}")

    try:
        response = requests.get(
            "http://httpbin.org/ip",
            proxies=proxy.to_proxies_dict(),
            timeout=30,
        )
        actual_ip = response.json().get("origin")
        print(f"Actual IP  : {actual_ip}")

        if actual_ip == HOST:
            print("Success! IP matches.")
        else:
            print("Warning: IP does not match expected.")
    except Exception as e:
        print(f"Failed: {e}")


if __name__ == "__main__":
    main()
