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

from dotenv import load_dotenv

from thordata import (
    ThordataClient,
    AsyncThordataClient,
    Engine,
    SerpRequest,
    ThordataAuthError,
    ThordataRateLimitError,
)

logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")

load_dotenv()

SCRAPER_TOKEN = os.getenv("THORDATA_SCRAPER_TOKEN")

if not SCRAPER_TOKEN:
    print("❌ Error: THORDATA_SCRAPER_TOKEN is missing in .env")
    sys.exit(1)


def demo_basic_search():
    """Basic Google search."""
    print("\n" + "=" * 50)
    print("1️⃣  Basic Google Search")
    print("=" * 50)

    client = ThordataClient(scraper_token=SCRAPER_TOKEN)

    try:
        results = client.serp_search(
            query="Python programming",
            engine=Engine.GOOGLE,
            num=5,
        )

        organic = results.get("organic", [])
        print(f"✅ Found {len(organic)} organic results:\n")

        for i, item in enumerate(organic[:3], 1):
            title = item.get("title", "No title")
            link = item.get("link", "")
            print(f"   {i}. {title}")
            print(f"      {link}\n")

    except ThordataRateLimitError as e:
        print(f"❌ Rate limited: {e}")
    except ThordataAuthError as e:
        print(f"❌ Auth error: {e}")
    except Exception as e:
        print(f"❌ Search failed: {e}")


def demo_bing_search():
    """Bing search example."""
    print("\n" + "=" * 50)
    print("2️⃣  Bing Search")
    print("=" * 50)

    client = ThordataClient(scraper_token=SCRAPER_TOKEN)

    try:
        results = client.serp_search(
            query="machine learning",
            engine=Engine.BING,
            num=5,
        )

        organic = results.get("organic", [])
        print(f"✅ Bing returned {len(organic)} results")

    except Exception as e:
        print(f"❌ Bing search failed: {e}")


def demo_google_shopping():
    """Google Shopping search."""
    print("\n" + "=" * 50)
    print("3️⃣  Google Shopping Search")
    print("=" * 50)

    client = ThordataClient(scraper_token=SCRAPER_TOKEN)

    try:
        results = client.serp_search(
            query="laptop",
            engine=Engine.GOOGLE,
            search_type="shopping",
            country="us",
            num=5,
        )

        shopping = results.get("shopping_results", [])
        print(f"✅ Found {len(shopping)} shopping results")

        for item in shopping[:3]:
            title = item.get("title", "Unknown")
            price = item.get("price", "N/A")
            print(f"   • {title} - {price}")

    except Exception as e:
        print(f"❌ Shopping search failed: {e}")


def demo_advanced_search():
    """Advanced search using SerpRequest."""
    print("\n" + "=" * 50)
    print("4️⃣  Advanced Search (SerpRequest)")
    print("=" * 50)

    client = ThordataClient(scraper_token=SCRAPER_TOKEN)

    # Create detailed search request
    request = SerpRequest(
        query="AI news 2024",
        engine="google",
        num=10,
        country="us",
        language="en",
        search_type="news",
        time_filter="week",
        safe_search=True,
    )

    print(f"   Query: {request.query}")
    print(f"   Engine: {request.engine}")
    print("   Type: News")
    print("   Time: Past week")

    try:
        results = client.serp_search_advanced(request)
        news = results.get("news_results", results.get("organic", []))
        print(f"\n✅ Found {len(news)} news results")

    except Exception as e:
        print(f"❌ Advanced search failed: {e}")


async def demo_async_search():
    """Async SERP search."""
    print("\n" + "=" * 50)
    print("5️⃣  Async Search (Yandex)")
    print("=" * 50)

    async with AsyncThordataClient(scraper_token=SCRAPER_TOKEN) as client:
        try:
            results = await client.serp_search(
                query="Python async programming",
                engine=Engine.YANDEX,
                num=5,
            )

            organic = results.get("organic", [])
            print(f"✅ Yandex returned {len(organic)} results")

        except Exception as e:
            print(f"❌ Async search failed: {e}")


if __name__ == "__main__":
    print("=" * 50)
    print("   Thordata SDK - SERP API Demo")
    print("=" * 50)

    demo_basic_search()
    demo_bing_search()
    demo_google_shopping()
    demo_advanced_search()
    asyncio.run(demo_async_search())

    print("\n" + "=" * 50)
    print("   Demo Complete!")
    print("=" * 50)
