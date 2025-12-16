"""
Thordata Universal API (Web Unlocker) Demo

Demonstrates:
- Basic HTML scraping (no JS)
- JS rendering for SPA/dynamic pages
- Cleaning JS/CSS from returned content
- Using custom headers and cookies
- Taking PNG screenshots

Usage:
    1. Copy examples/.env.example to .env
    2. Fill in THORDATA_SCRAPER_TOKEN in .env
    3. Run:
        python examples/demo_universal.py
"""

import logging
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

from thordata import (
    ThordataClient,
    UniversalScrapeRequest,
    ThordataError,
    ThordataAuthError,
    ThordataRateLimitError,
)

logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")

# Load .env from project root
ROOT_DIR = Path(__file__).parent.parent
load_dotenv(ROOT_DIR / ".env")

SCRAPER_TOKEN = os.getenv("THORDATA_SCRAPER_TOKEN")

if not SCRAPER_TOKEN:
    print("❌ Error: THORDATA_SCRAPER_TOKEN is missing in .env")
    sys.exit(1)

client = ThordataClient(scraper_token=SCRAPER_TOKEN)


def demo_basic_html() -> None:
    """1) Basic HTML scrape without JS rendering."""
    url = "https://httpbin.org/html"
    print("\n" + "=" * 70)
    print(f"1️⃣  Basic HTML Scrape (no JS) - {url}")
    print("=" * 70)

    try:
        html = client.universal_scrape(
            url=url,
            js_render=False,
            output_format="html",
        )

        print("✅ Success! Received HTML content.")
        print("   Preview:")
        print("-" * 70)
        print(str(html)[:300])
        print("-" * 70)

    except ThordataRateLimitError as e:
        print(f"❌ Rate limit / quota issue: {e}")
    except ThordataAuthError as e:
        print(f"❌ Authentication error: {e}")
    except ThordataError as e:
        print(f"❌ Thordata SDK error: {e}")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")


def demo_js_render_wait() -> None:
    """2) JS rendering with wait_for selector."""
    url = "https://example.com"
    print("\n" + "=" * 70)
    print(f"2️⃣  JS Render + Wait for Selector - {url}")
    print("=" * 70)

    try:
        html = client.universal_scrape(
            url=url,
            js_render=True,
            output_format="html",
            # 等待 .content 或主内容元素出现，示例中用 body 替代
            wait_for="body",
        )

        print("✅ Success! JS-rendered HTML acquired.")
        print("   Preview:")
        print("-" * 70)
        print(str(html)[:300])
        print("-" * 70)

    except ThordataError as e:
        print(f"❌ Thordata SDK error: {e}")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")


def demo_clean_content() -> None:
    """3) Clean JS/CSS from returned HTML."""
    url = "https://www.google.com"
    print("\n" + "=" * 70)
    print(f"3️⃣  Clean Content (remove JS/CSS) - {url}")
    print("=" * 70)

    try:
        html = client.universal_scrape(
            url=url,
            js_render=True,
            output_format="html",
            clean_content="js,css",
            wait=5000,
        )

        print("✅ Success! JS/CSS cleaned from HTML.")
        print("   Preview:")
        print("-" * 70)
        print(str(html)[:300])
        print("-" * 70)

    except ThordataError as e:
        print(f"❌ Thordata SDK error: {e}")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")


def demo_custom_headers_and_cookies() -> None:
    """4) Use custom headers and cookies via UniversalScrapeRequest."""
    url = "https://httpbin.org/headers"
    print("\n" + "=" * 70)
    print(f"4️⃣  Custom Headers & Cookies - {url}")
    print("=" * 70)

    request = UniversalScrapeRequest(
        url=url,
        js_render=False,
        output_format="html",
        headers=[
            {
                "name": "User-Agent",
                "value": "Mozilla/5.0 (ThordataDemo/1.0)",
            },
            {
                "name": "X-Demo-Header",
                "value": "DemoValue",
            },
        ],
        cookies=[
            {"name": "session", "value": "demo_session_123"},
        ],
    )

    try:
        html = client.universal_scrape_advanced(request)

        print("✅ Success! Response with custom headers/cookies.")
        print("   Preview:")
        print("-" * 70)
        print(str(html)[:500])
        print("-" * 70)

    except ThordataError as e:
        print(f"❌ Thordata SDK error: {e}")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")


def demo_screenshot() -> None:
    """5) Take a PNG screenshot and save to disk."""
    url = "https://www.example.com"
    filename = ROOT_DIR / "universal_screenshot.png"

    print("\n" + "=" * 70)
    print(f"5️⃣  Screenshot (PNG) - {url}")
    print("=" * 70)

    try:
        png_bytes = client.universal_scrape(
            url=url,
            js_render=True,
            output_format="png",
        )

        if isinstance(png_bytes, bytes):
            with open(filename, "wb") as f:
                f.write(png_bytes)

            print("✅ Screenshot saved!")
            print(f"   File: {filename}")
            print(f"   Size: {len(png_bytes):,} bytes")
        else:
            print("⚠️  Expected PNG bytes, got:", type(png_bytes))

    except ThordataError as e:
        print(f"❌ Thordata SDK error: {e}")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")


if __name__ == "__main__":
    print("=" * 70)
    print(" Thordata SDK - Universal API (Web Unlocker) Demo")
    print("=" * 70)

    demo_basic_html()
    demo_js_render_wait()
    demo_clean_content()
    demo_custom_headers_and_cookies()
    demo_screenshot()

    print("\nAll demos completed.")
