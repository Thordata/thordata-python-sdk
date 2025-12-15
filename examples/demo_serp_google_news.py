"""
Demo: Google News via Thordata SERP API

Demonstrates:
- Basic Google News search
- Using topic_token / publication_token / section_token / story_token
- Sorting by relevance/date (so parameter)

Usage:
    1. Set THORDATA_SCRAPER_TOKEN in .env
    2. (Optional) Set country/language if需要本地化
    3. Run:
        python examples/demo_serp_google_news.py
"""

import logging
import os
import sys

from dotenv import load_dotenv

from thordata import ThordataClient, Engine

logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")

# Load credentials
load_dotenv()

SCRAPER_TOKEN = os.getenv("THORDATA_SCRAPER_TOKEN")
COUNTRY = os.getenv("THORDATA_SERP_COUNTRY", "us")
LANGUAGE = os.getenv("THORDATA_SERP_LANGUAGE", "en")

if not SCRAPER_TOKEN:
    print("❌ Error: THORDATA_SCRAPER_TOKEN is missing in .env")
    sys.exit(1)


def print_news_results(results: dict, max_items: int = 5) -> None:
    """Pretty-print Google News results."""
    news = results.get("news_results") or results.get("organic") or []
    print(f"Found {len(news)} news results.\n")

    for i, item in enumerate(news[:max_items], 1):
        title = item.get("title", "No title")
        link = item.get("link", "")
        source = item.get("source") or item.get("publisher", "")
        snippet = item.get("snippet", "")[:120]

        print(f"{i}. {title}")
        if source:
            print(f"   Source: {source}")
        if snippet:
            print(f"   Snippet: {snippet}...")
        if link:
            print(f"   Link   : {link}")
        print()


def demo_basic_news_search() -> None:
    """Basic Google News search."""
    print("\n" + "=" * 60)
    print("1) Basic Google News search")
    print("=" * 60)

    client = ThordataClient(scraper_token=SCRAPER_TOKEN)

    query = "AI regulation"

    print(f"Query   : {query}")
    print(f"Country : {COUNTRY}")
    print(f"Language: {LANGUAGE}")

    results = client.serp_search(
        query=query,
        engine=Engine.GOOGLE,
        search_type="news",  # tbm=nws
        country=COUNTRY,
        language=LANGUAGE,
        num=10,
    )

    print_news_results(results)


def demo_advanced_news_filters() -> None:
    """
    Advanced Google News filters:
    - topic_token / publication_token / section_token / story_token
    - so (sort by relevance/date)
    """
    print("\n" + "=" * 60)
    print("2) Advanced Google News filters")
    print("=" * 60)

    client = ThordataClient(scraper_token=SCRAPER_TOKEN)

    query = "Artificial Intelligence"

    # 这里用占位符，实际使用时请替换为 Dashboard/调试结果中看到的 token 值
    topic_token = os.getenv("THORDATA_NEWS_TOPIC_TOKEN", "")
    publication_token = os.getenv("THORDATA_NEWS_PUBLICATION_TOKEN", "")
    section_token = os.getenv("THORDATA_NEWS_SECTION_TOKEN", "")
    story_token = os.getenv("THORDATA_NEWS_STORY_TOKEN", "")

    print(f"Query : {query}")
    print(f"Topic token       : {topic_token or '(not set)'}")
    print(f"Publication token : {publication_token or '(not set)'}")
    print(f"Section token     : {section_token or '(not set)'}")
    print(f"Story token       : {story_token or '(not set)'}")
    print("Sort by           : Date (so=1)")
    print()

    results = client.serp_search(
        query=query,
        engine=Engine.GOOGLE,
        search_type="news",
        country=COUNTRY,
        language=LANGUAGE,
        num=10,
        # 以下参数全部通过 kwargs 透传
        topic_token=topic_token or None,
        publication_token=publication_token or None,
        section_token=section_token or None,
        story_token=story_token or None,
        so=1,  # 0=Relevance, 1=Date
    )

    print_news_results(results)


if __name__ == "__main__":
    print("=" * 60)
    print("Thordata SERP API - Google News Demo")
    print("=" * 60)

    demo_basic_news_search()
    demo_advanced_news_filters()

    print("\nDone.")
