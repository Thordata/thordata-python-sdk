"""
Demo: SERP API usage (Google / Bing / Yandex / Google Shopping).

Corresponds to the "SERP API -> Send your first request" section in the docs.

Shows how to:
- Use Engine and GoogleSearchType enums.
- Pass engine-specific parameters (location, type, etc.) via kwargs.
- Handle specific Thordata exceptions (RateLimit / Auth).
"""

from __future__ import annotations

import asyncio
import logging
import os

from dotenv import load_dotenv

from thordata import (
    AsyncThordataClient,
    Engine,
    GoogleSearchType,
    ThordataAuthError,
    ThordataClient,
    ThordataRateLimitError,
)

# Configure logging to see SDK internal logs (optional)
logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")

# Load credentials from .env
load_dotenv()
SCRAPER_TOKEN = os.getenv("THORDATA_SCRAPER_TOKEN")
PUBLIC_TOKEN = os.getenv("THORDATA_PUBLIC_TOKEN", "")
PUBLIC_KEY = os.getenv("THORDATA_PUBLIC_KEY", "")

if not SCRAPER_TOKEN:
    raise ValueError(
        "Missing THORDATA_SCRAPER_TOKEN. "
        "Please copy .env.example to .env and fill in your credentials."
    )


def demo_sync_serp() -> None:
    """
    Demonstrates synchronous SERP usage:
    1) Bing search using Engine enum.
    2) Google Shopping search using GoogleSearchType enum.
    """
    print("\n=== SERP API (Synchronous Client) ===")
    client = ThordataClient(SCRAPER_TOKEN, PUBLIC_TOKEN, PUBLIC_KEY)

    # 1. Bing search
    print("\n[1] Bing search: 'Thordata SDK' ...")
    try:
        results = client.serp_search("Thordata SDK", engine=Engine.BING)
        organic = results.get("organic", [])
        print(f"✅ Bing search succeeded. Organic results: {len(organic)}")
    except (ThordataRateLimitError, ThordataAuthError) as e:
        print(f"❌ Bing search failed (Auth/Quota): {e}")
    except Exception as e:
        print(f"❌ Bing search failed (Generic): {e}")

    # 2. Google Shopping search
    print("\n[2] Google Shopping search: 'iPhone 15' (location=US) ...")
    try:
        results = client.serp_search(
            "iPhone 15",
            engine=Engine.GOOGLE,
            type=GoogleSearchType.SHOPPING,  # or simply "shopping"
            location="United States",
            num=5,
        )
        # Shopping results structure might vary
        shopping = results.get("shopping_results") or results.get("shopping") or []
        print(f"✅ Google Shopping search succeeded. Items found: {len(shopping)}")
    except Exception as e:
        print(f"❌ Google Shopping search failed: {e}")


async def demo_async_serp() -> None:
    """
    Demonstrates asynchronous SERP usage with Yandex.
    Shows how normalize_serp_params handles 'text' vs 'q' automatically.
    """
    print("\n=== SERP API (Asynchronous Client) ===")

    async with AsyncThordataClient(
        scraper_token=SCRAPER_TOKEN,
        public_token=PUBLIC_TOKEN,
        public_key=PUBLIC_KEY,
    ) as client:

        print("\n[3] Yandex search (async): 'Python async' ...")
        try:
            results = await client.serp_search("Python async", engine=Engine.YANDEX)
            status = results.get("search_metadata", {}).get("status", "Unknown")
            print(f"✅ Yandex async search succeeded. Status: {status}")
        except Exception as e:
            print(f"❌ Yandex async search failed: {e}")


if __name__ == "__main__":
    demo_sync_serp()
    asyncio.run(demo_async_serp())
