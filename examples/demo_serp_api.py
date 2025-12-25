"""
SERP API Demo - Search Engine Results

Demonstrates:
- Google, Bing, Yandex search using Engine enum
- Search types (Shopping, News, Images)
- Advanced search with SerpRequest
- Async SERP search

Usage:
    python examples/demo_serp_api.py
"""

import asyncio
import logging
import os
import sys
from datetime import date

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

try:
    from dotenv import load_dotenv
except ImportError:
    load_dotenv = None

from thordata import (
    AsyncThordataClient,
    Engine,
    SerpRequest,
    ThordataAuthError,
    ThordataClient,
    ThordataRateLimitError,
)

logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")


def _load_env() -> None:
    if load_dotenv is not None:
        load_dotenv()


def _print_results(results: dict, result_key: str, alt_keys: list = None) -> int:
    """Helper to find and print results from various possible keys."""
    alt_keys = alt_keys or []

    # Try primary key first, then alternatives
    data = results.get(result_key, [])
    if not data:
        for key in alt_keys:
            data = results.get(key, [])
            if data:
                break

    # If still no data, show available keys for debugging
    if not data:
        available_keys = [k for k in results.keys() if not k.startswith("search_")]
        print(f"   Available keys: {available_keys[:10]}")  # Show first 10

    return len(data) if isinstance(data, list) else 0


def demo_basic_search(scraper_token: str) -> None:
    """Basic Google search."""
    print("\n" + "=" * 50)
    print("1)  Basic Google Search")
    print("=" * 50)

    client = ThordataClient(scraper_token=scraper_token)

    try:
        results = client.serp_search(
            query="Python programming",
            engine=Engine.GOOGLE,
            num=10,  # Request more results
        )

        organic = results.get("organic", results.get("organic_results", []))
        print(f"[OK] Found {len(organic)} organic results:\n")

        for i, item in enumerate(organic[:5], 1):  # Show up to 5
            title = item.get("title", "No title")
            link = item.get("link", "")
            print(f"   {i}. {title}")
            print(f"      {link}\n")

    except ThordataRateLimitError as e:
        print(f"[ERROR] Rate limited: {e}")
    except ThordataAuthError as e:
        print(f"[ERROR] Auth error: {e}")
    except Exception as e:
        print(f"[ERROR] Search failed: {e}")


def demo_bing_search(scraper_token: str) -> None:
    """Bing search example."""
    print("\n" + "=" * 50)
    print("2)  Bing Search")
    print("=" * 50)

    client = ThordataClient(scraper_token=scraper_token)

    try:
        results = client.serp_search(
            query="machine learning",
            engine=Engine.BING,
            num=10,
        )

        organic = results.get("organic", results.get("organic_results", []))
        print(f"[OK] Bing returned {len(organic)} results")

    except Exception as e:
        print(f"[ERROR] Bing search failed: {e}")


def demo_google_shopping(scraper_token: str) -> None:
    """Google Shopping search."""
    print("\n" + "=" * 50)
    print("3)  Google Shopping Search")
    print("=" * 50)

    client = ThordataClient(scraper_token=scraper_token)

    try:
        results = client.serp_search(
            query="laptop",
            engine="google_shopping",
            country="us",
            num=10,
        )

        # Try multiple possible keys for shopping results
        shopping = (
            results.get("shopping")
            or results.get("shopping_results")
            or results.get("inline_shopping")
            or results.get("immersive_products")
            or results.get("products")
            or []
        )

        print(f"[OK] Found {len(shopping)} shopping results")

        if shopping:
            for item in shopping[:3]:
                title = item.get("title", "Unknown")
                price = item.get("price", item.get("extracted_price", "N/A"))
                print(f"   - {title} - {price}")
        else:
            # Debug: show what keys we got
            print(f"   (Debug) Response keys: {list(results.keys())[:10]}")

    except Exception as e:
        print(f"[ERROR] Shopping search failed: {e}")


def demo_google_news(scraper_token: str) -> None:
    """Google News search."""
    print("\n" + "=" * 50)
    print("4)  Google News Search")
    print("=" * 50)

    client = ThordataClient(scraper_token=scraper_token)

    try:
        results = client.serp_search(
            query="AI regulation 2024",
            engine="google_news",
            country="us",
            language="en",
            num=10,
        )

        # Try multiple possible keys for news results
        news = (
            results.get("news_results")
            or results.get("top_stories")
            or results.get("news")
            or results.get("organic")
            or []
        )

        print(f"[OK] Found {len(news)} news results")

        if news:
            for item in news[:3]:
                title = item.get("title", "Unknown")
                source = item.get("source", item.get("publisher", ""))
                print(f"   - {title}")
                if source:
                    print(f"     Source: {source}")
        else:
            print(f"   (Debug) Response keys: {list(results.keys())[:10]}")

    except Exception as e:
        print(f"[ERROR] News search failed: {e}")


async def demo_async_search(scraper_token: str) -> None:
    """Async SERP search with extended timeout."""
    print("\n" + "=" * 50)
    print("5)  Async Search (Yandex)")
    print("=" * 50)

    # Use longer timeout for Yandex
    async with AsyncThordataClient(
        scraper_token=scraper_token,
        timeout=60,  # Extended timeout
    ) as client:
        try:
            results = await client.serp_search(
                query="Python tutorial",
                engine=Engine.YANDEX,
                num=5,
            )

            organic = results.get("organic", results.get("organic_results", []))
            print(f"[OK] Yandex returned {len(organic)} results")

        except Exception as e:
            print(f"[WARN] Yandex search issue: {type(e).__name__}: {e}")
            print("       (Yandex may have slower response times)")


def main() -> int:
    _load_env()

    scraper_token = os.getenv("THORDATA_SCRAPER_TOKEN")
    if not scraper_token:
        print("Error: THORDATA_SCRAPER_TOKEN is missing.")
        return 1

    print("=" * 50)
    print("Thordata SDK - SERP API Demo")
    print(f"Date: {date.today().isoformat()}")
    print("=" * 50)

    demo_basic_search(scraper_token)
    demo_bing_search(scraper_token)
    demo_google_shopping(scraper_token)
    demo_google_news(scraper_token)
    asyncio.run(demo_async_search(scraper_token))

    print("\n" + "=" * 50)
    print("Demo complete.")
    print("=" * 50)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
