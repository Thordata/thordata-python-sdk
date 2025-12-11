"""
Universal Scraping API (Web Unlocker) Demo

Demonstrates:
- HTML scraping
- Screenshot capture (PNG)
- JavaScript rendering
- Geo-targeted scraping
- Advanced options with UniversalScrapeRequest

Usage:
    python examples/demo_universal.py
"""

import logging
import os
import sys

from dotenv import load_dotenv

from thordata import (
    ThordataClient,
    UniversalScrapeRequest,
    ThordataAuthError,
    ThordataRateLimitError,
)

logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")

load_dotenv()

SCRAPER_TOKEN = os.getenv("THORDATA_SCRAPER_TOKEN")

if not SCRAPER_TOKEN:
    print("❌ Error: THORDATA_SCRAPER_TOKEN is missing in .env")
    sys.exit(1)

client = ThordataClient(scraper_token=SCRAPER_TOKEN)


def demo_basic_scrape():
    """Basic HTML scraping."""
    print("\n" + "=" * 50)
    print("1️⃣  Basic HTML Scrape")
    print("=" * 50)

    url = "https://httpbin.org/html"

    try:
        html = client.universal_scrape(url=url, js_render=False)

        print(f"✅ Scraped {len(html)} characters")
        print(f"   Preview: {html[:100]}...")

    except ThordataRateLimitError as e:
        print(f"❌ Rate limited: {e}")
    except ThordataAuthError as e:
        print(f"❌ Auth error: {e}")
    except Exception as e:
        print(f"❌ Scrape failed: {e}")


def demo_js_rendering():
    """Scrape with JavaScript rendering."""
    print("\n" + "=" * 50)
    print("2️⃣  JavaScript Rendering")
    print("=" * 50)

    url = "https://example.com"

    try:
        html = client.universal_scrape(
            url=url,
            js_render=True,
            wait=2000,  # Wait 2 seconds for JS to load
        )

        print(f"✅ Rendered and scraped {len(html)} characters")
        print(f"   Contains <body>: {'<body' in html.lower()}")

    except Exception as e:
        print(f"❌ JS rendering failed: {e}")


def demo_screenshot():
    """Take a screenshot (PNG)."""
    print("\n" + "=" * 50)
    print("3️⃣  Screenshot Capture")
    print("=" * 50)

    url = "https://example.com"
    filename = "screenshot_demo.png"

    try:
        image_bytes = client.universal_scrape(
            url=url,
            output_format="png",
            js_render=True,
        )

        if isinstance(image_bytes, bytes):
            with open(filename, "wb") as f:
                f.write(image_bytes)

            print("✅ Screenshot saved!")
            print(f"   File: {os.path.abspath(filename)}")
            print(f"   Size: {len(image_bytes):,} bytes")
        else:
            print(f"⚠️  Expected bytes, got: {type(image_bytes)}")

    except Exception as e:
        print(f"❌ Screenshot failed: {e}")


def demo_geo_targeted():
    """Geo-targeted scraping."""
    print("\n" + "=" * 50)
    print("4️⃣  Geo-Targeted Scrape (US)")
    print("=" * 50)

    url = "https://httpbin.org/ip"

    try:
        html = client.universal_scrape(
            url=url,
            js_render=False,
            country="us",
        )

        print("✅ Scraped from US proxy")
        print(f"   Response: {html[:200]}...")

    except Exception as e:
        print(f"❌ Geo scrape failed: {e}")


def demo_advanced_options():
    """Advanced scraping with UniversalScrapeRequest."""
    print("\n" + "=" * 50)
    print("5️⃣  Advanced Options (UniversalScrapeRequest)")
    print("=" * 50)

    # Create detailed scrape request
    request = UniversalScrapeRequest(
        url="https://example.com",
        js_render=True,
        output_format="html",
        country="gb",
        wait=3000,
        wait_for="body",
        block_resources="image,font",
        clean_content="js,css",
    )

    print(f"   URL: {request.url}")
    print(f"   JS Render: {request.js_render}")
    print(f"   Country: {request.country}")
    print(f"   Wait: {request.wait}ms")

    try:
        html = client.universal_scrape_advanced(request)

        print("\n✅ Advanced scrape succeeded!")
        print(f"   Result length: {len(html)} characters")

    except Exception as e:
        print(f"❌ Advanced scrape failed: {e}")


if __name__ == "__main__":
    print("=" * 50)
    print("   Thordata SDK - Universal API Demo")
    print("=" * 50)

    demo_basic_scrape()
    demo_js_rendering()
    demo_screenshot()
    demo_geo_targeted()
    demo_advanced_options()

    print("\n" + "=" * 50)
    print("   Demo Complete!")
    print("=" * 50)
