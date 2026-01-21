"""
Scraping Browser Demo - Remote Browser Automation

Demonstrates:
- Using SDK helper to generate connection URL
- Connecting to Thordata's Scraping Browser via WebSocket
- Using Playwright for automation

Usage:
    python examples/demo_scraping_browser.py
"""

import asyncio
import logging
from pathlib import Path

from dotenv import load_dotenv

from thordata import AsyncThordataClient, ThordataConfigError

logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")

load_dotenv(dotenv_path=Path(__file__).resolve().parents[1] / ".env")


async def demo_basic_navigation():
    print("\n" + "=" * 50)
    print("1️⃣  Basic Navigation (using SDK helper)")
    print("=" * 50)

    # Initialize client to use the helper
    client = AsyncThordataClient()

    try:
        # Use the new helper method
        ws_endpoint = client.get_browser_connection_url()
        print(f"   Generated Endpoint: {ws_endpoint[:20]}... (hidden)")
    except ThordataConfigError as e:
        print(f"❌ Configuration Error: {e}")
        print("   Set THORDATA_BROWSER_USERNAME/PASSWORD in .env")
        return

    try:
        from playwright.async_api import async_playwright  # type: ignore[import]
    except ImportError:
        print(
            "⚠️  Playwright not installed. Run: pip install playwright && playwright install chromium"
        )
        return

    try:
        async with async_playwright() as p:
            print("   Connecting to Scraping Browser...")
            browser = await p.chromium.connect_over_cdp(ws_endpoint)
            print("   ✅ Connected!")

            context = await browser.new_context()
            page = await context.new_page()

            await page.goto("https://example.com")
            print(f"   Title: {await page.title()}")

            await browser.close()
            print("   ✅ Browser closed")

    except Exception as e:
        print(f"❌ Browser Error: {e}")


if __name__ == "__main__":
    print("=" * 50)
    print("   Thordata SDK - Scraping Browser Demo")
    print("=" * 50)

    asyncio.run(demo_basic_navigation())
