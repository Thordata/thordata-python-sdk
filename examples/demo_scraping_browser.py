"""
Demo: Thordata Scraping Browser with Playwright (Python).

Connects to Thordata's remote browser (CDP) via WebSocket to scrape dynamic content.
Equivalent to the official Node.js Puppeteer example.

Usage:
    python examples/demo_scraping_browser.py
"""

import asyncio
import os
import urllib.parse

from dotenv import load_dotenv
from playwright.async_api import async_playwright

load_dotenv()

# 1. Credentials from Dashboard (Scraping Browser)
USERNAME = os.getenv("THORDATA_BROWSER_USERNAME", "td-customer-rltwM3prqji9")
PASSWORD = os.getenv("THORDATA_BROWSER_PASSWORD", "VlFQac3mx5md")
HOST = os.getenv("THORDATA_BROWSER_HOST", "ws-browser.thordata.com")

# 2. Construct Authenticated WebSocket URL
# Note: password must be URL-encoded if it contains special chars
encoded_user = urllib.parse.quote(USERNAME)
encoded_pass = urllib.parse.quote(PASSWORD)
CDP_URL = f"wss://{encoded_user}:{encoded_pass}@{HOST}"


async def run():
    print(f"Connecting to Scraping Browser at {HOST}...")

    async with async_playwright() as pw:
        try:
            # Connect to the remote browser instance
            browser = await pw.chromium.connect_over_cdp(CDP_URL)
            print("✅ Connected to remote browser.")

            # Create a new page/tab
            page = await browser.new_page()

            # Example
            target_url = "https://example.com"
            print(f"Navigating to: {target_url}")

            # Increased timeout for remote browsing
            await page.goto(target_url, timeout=60000, wait_until="domcontentloaded")

            print("Waiting for product list...")
            await page.wait_for_selector("h1")

            # Extract titles
            title = await page.title()

            print(f"Page Title: {title}")

            await browser.close()
            print("\nBrowser closed.")

        except Exception as e:
            print(f"❌ Scraping failed: {e}")


if __name__ == "__main__":
    asyncio.run(run())
