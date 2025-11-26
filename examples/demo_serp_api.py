"""
Demo: SERP API usage (Google / Bing / Yandex) with sync & async clients.

- Shows how to use the Engine and GoogleSearchType enums.
- Demonstrates parameter passthrough via **kwargs (e.g. Shopping search).
"""

import os
import asyncio
import logging

from dotenv import load_dotenv
from thordata import ThordataClient, AsyncThordataClient, Engine, GoogleSearchType

# Configure logging to see SDK internal logs (optional)
logging.basicConfig(level=logging.INFO)

# Load credentials from .env
load_dotenv()
SCRAPER_TOKEN = os.getenv("THORDATA_SCRAPER_TOKEN")
PUBLIC_TOKEN = os.getenv("THORDATA_PUBLIC_TOKEN")
PUBLIC_KEY = os.getenv("THORDATA_PUBLIC_KEY")

if not SCRAPER_TOKEN:
    raise ValueError(
        "Missing THORDATA_SCRAPER_TOKEN. "
        "Please copy .env.example to .env and fill in your credentials."
    )


def demo_sync_serp() -> None:
    """
    Demonstrates synchronous SERP usage:
    1) Bing search using Engine enum.
    2) Google Shopping search using GoogleSearchType enum and **kwargs passthrough.
    """
    print("\n=== SERP API (Synchronous Client) ===")
    client = ThordataClient(SCRAPER_TOKEN, PUBLIC_TOKEN, PUBLIC_KEY)

    # 1. Bing search using Engine enum
    print("\n[1] Bing search using Engine.BING ...")
    try:
        results = client.serp_search("Thordata SDK", engine=Engine.BING)
        organic_count = len(results.get("organic", []))
        print(f"✅ Bing search succeeded. Organic results: {organic_count}")
    except Exception as e:
        print(f"❌ Bing search failed: {e}")

    # 2. Google Shopping search with advanced parameters
    print("\n[2] Google Shopping search using GoogleSearchType.SHOPPING ...")
    try:
        results = client.serp_search(
            "iPhone 15",
            engine=Engine.GOOGLE,
            type=GoogleSearchType.SHOPPING,  # or simply "shopping"
            location="United States",        # extra parameter passed via **kwargs
            num=5,
        )
        print("✅ Google Shopping search succeeded.")
        # Optionally inspect the raw structure:
        # print(json.dumps(results, indent=2))
    except Exception as e:
        print(f"❌ Google Shopping search failed: {e}")


async def demo_async_serp() -> None:
    """
    Demonstrates asynchronous SERP usage with Yandex.
    This validates the normalize_serp_params() logic for engines using 'text'
    instead of 'q' as the query parameter.
    """
    print("\n=== SERP API (Asynchronous Client) ===")

    async with AsyncThordataClient(
        scraper_token=SCRAPER_TOKEN,
        public_token=PUBLIC_TOKEN,
        public_key=PUBLIC_KEY,
    ) as client:

        print("\n[3] Yandex search (async) ...")
        try:
            results = await client.serp_search("Python async", engine=Engine.YANDEX)
            if "organic" in results or "search_metadata" in results:
                status = results.get("search_metadata", {}).get("status")
                print(f"✅ Yandex async search succeeded. Status: {status}")
            else:
                print(f"⚠️ Yandex returned 200 but content seems empty: {results}")
        except Exception as e:
            print(f"❌ Yandex async search failed: {e}")


if __name__ == "__main__":
    demo_sync_serp()
    asyncio.run(demo_async_serp())