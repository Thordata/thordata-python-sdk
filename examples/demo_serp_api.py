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

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

try:
    from dotenv import load_dotenv
except ImportError:
    load_dotenv = None

from thordata import (AsyncThordataClient, Engine, SerpRequest,
                      ThordataAuthError, ThordataClient,
                      ThordataRateLimitError)

logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")


def _load_env() -> None:
    if load_dotenv is not None:
        load_dotenv()


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
            num=5,
        )

        organic = results.get("organic", [])
        print(f"[OK] Found {len(organic)} organic results:\n")

        for i, item in enumerate(organic[:3], 1):
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
            num=5,
        )

        organic = results.get("organic", [])
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
            num=5,
        )

        shopping = results.get("shopping_results", [])
        print(f"[OK] Found {len(shopping)} shopping results")

        for item in shopping[:3]:
            title = item.get("title", "Unknown")
            price = item.get("price", "N/A")
            print(f"   - {title} - {price}")

    except Exception as e:
        print(f"[ERROR] Shopping search failed: {e}")


def demo_advanced_search(scraper_token: str) -> None:
    """Advanced search using SerpRequest."""
    print("\n" + "=" * 50)
    print("4)  Advanced Search (SerpRequest)")
    print("=" * 50)

    client = ThordataClient(scraper_token=scraper_token)

    # Create detailed search request
    request = SerpRequest(
        query="AI news 2024",
        engine="google_news",
        num=10,
        country="us",
        language="en",
        extra_params={"so": "1"},  # sort by date per docs
    )

    print(f"   Query: {request.query}")
    print(f"   Engine: {request.engine}")
    print("   Type: News")
    print("   Time: Past week")

    try:
        results = client.serp_search_advanced(request)
        news = results.get("news_results", results.get("organic", []))
        print(f"\n[OK] Found {len(news)} news results")

    except Exception as e:
        print(f"[ERROR] Advanced search failed: {e}")


async def demo_async_search(scraper_token: str) -> None:
    """Async SERP search."""
    print("\n" + "=" * 50)
    print("5)  Async Search (Yandex)")
    print("=" * 50)

    async with AsyncThordataClient(scraper_token=scraper_token) as client:
        try:
            results = await client.serp_search(
                query="Python async programming",
                engine=Engine.YANDEX,
                num=5,
            )

            organic = results.get("organic", [])
            print(f"[OK] Yandex returned {len(organic)} results")

        except Exception as e:
            print(f"[ERROR] Async search failed: {e}")


def main() -> int:
    _load_env()

    scraper_token = os.getenv("THORDATA_SCRAPER_TOKEN")
    if not scraper_token:
        print("Error: THORDATA_SCRAPER_TOKEN is missing.")
        return 1

    print("=" * 50)
    print("Thordata SDK - SERP API Demo")
    print("=" * 50)

    demo_basic_search(scraper_token)
    demo_bing_search(scraper_token)
    demo_google_shopping(scraper_token)
    demo_advanced_search(scraper_token)
    asyncio.run(demo_async_search(scraper_token))

    print("=" * 50)
    print("Demo complete.")
    print("=" * 50)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
