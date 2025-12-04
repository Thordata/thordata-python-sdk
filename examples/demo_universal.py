"""
Demo: Universal Scraping API (HTML & Screenshots).

Corresponds to the "Universal Scraping API -> Quick Start" section in the docs.

Shows how to:
- Fetch raw HTML (text).
- Fetch a Screenshot (PNG bytes) and save to disk.
- Handle SDK-specific exceptions.
"""

from __future__ import annotations

import os
import logging
from dotenv import load_dotenv
from thordata import (
    ThordataClient,
    ThordataRateLimitError,
    ThordataAuthError,
)

logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")

load_dotenv()
SCRAPER_TOKEN = os.getenv("THORDATA_SCRAPER_TOKEN")
PUBLIC_TOKEN = os.getenv("THORDATA_PUBLIC_TOKEN", "")
PUBLIC_KEY = os.getenv("THORDATA_PUBLIC_KEY", "")

if not SCRAPER_TOKEN:
    print("❌ Error: THORDATA_SCRAPER_TOKEN is missing in .env")
    exit(1)

client = ThordataClient(SCRAPER_TOKEN, PUBLIC_TOKEN, PUBLIC_KEY)


def scrape_html() -> None:
    target_url = "http://httpbin.org/ip"
    print(f"\n📄 [1] Scraping HTML from: {target_url}...")

    try:
        # js_render=False is faster for simple sites
        html = client.universal_scrape(url=target_url, js_render=False)
        # The SDK guarantees returning a str for HTML format
        print("✅ HTML Scrape Success!")
        print(f"   Preview: {str(html)[:100]!r}...")
    except ThordataRateLimitError as e:
        print(f"❌ Rate limit / Quota exceeded: {e}")
    except ThordataAuthError as e:
        print(f"❌ Authentication failed: {e}")
    except Exception as e:
        print(f"❌ HTML Scrape Failed: {e}")


def take_screenshot() -> None:
    target_url = "https://www.example.com"
    filename = "screenshot_result.png"
    print(f"\n📸 [2] Taking Screenshot of: {target_url}...")

    try:
        # The SDK automatically handles Base64 decoding -> bytes
        image_bytes = client.universal_scrape(
            url=target_url,
            output_format="PNG",
            js_render=True,
            block_resources=False,
        )

        if isinstance(image_bytes, str):
            print("⚠️ Expected bytes for PNG, got string (error json?):", image_bytes)
            return

        with open(filename, "wb") as f:
            f.write(image_bytes)

        print("✅ Screenshot Success!")
        print(f"📂 Saved to: {os.path.abspath(filename)}")
        print(f"📊 Size: {len(image_bytes)} bytes")

    except Exception as e:
        print(f"❌ Screenshot Failed: {e}")


if __name__ == "__main__":
    print("=== Thordata Universal API Demo ===")
    scrape_html()
    take_screenshot()