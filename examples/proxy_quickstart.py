"""
Demo: Basic Proxy Usage (Synchronous).

Corresponds to the "Proxy -> Send your first request" section in the docs.

Demonstrates:
- Initializing ThordataClient with credentials.
- Sending a simple GET request via the residential proxy gateway.
"""

import os
import logging
from dotenv import load_dotenv
from thordata import ThordataClient

# Configure logging
logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")

load_dotenv()

SCRAPER_TOKEN = os.getenv("THORDATA_SCRAPER_TOKEN")
PUBLIC_TOKEN = os.getenv("THORDATA_PUBLIC_TOKEN", "")
PUBLIC_KEY = os.getenv("THORDATA_PUBLIC_KEY", "")

if not SCRAPER_TOKEN:
    raise ValueError(
        "Missing THORDATA_SCRAPER_TOKEN. "
        "Please copy .env.example to .env and fill in your credentials."
    )

TARGET_URL = "http://httpbin.org/ip"


def run_quick_test() -> None:
    print("--- 1. Initialize Thordata Client ---")
    try:
        # Public tokens are optional for pure proxy usage, but good to have.
        client = ThordataClient(
            scraper_token=SCRAPER_TOKEN,
            public_token=PUBLIC_TOKEN,
            public_key=PUBLIC_KEY,
        )

        print(f"--- 2. Requesting via Proxy: {TARGET_URL} ---")
        # This request is routed through Thordata Residential Proxies
        response = client.get(TARGET_URL, timeout=30)
        response.raise_for_status()

        data = response.json()
        print("✅ Success! Request routed via Thordata.")
        print(f"   Origin IP: {data.get('origin')}")
        print(f"   Status Code: {response.status_code}")

    except Exception as e:
        print(f"❌ Request failed: {e}")


if __name__ == "__main__":
    print("=== Thordata SDK Quick Start ===")
    run_quick_test()
    print("================================")