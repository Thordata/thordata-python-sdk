"""
Scraping Browser Demo - Remote Browser Automation

Demonstrates:
- Connecting to Thordata's Scraping Browser via WebSocket
- Using Puppeteer/Playwright for complex page interactions
- Handling dynamic content and JavaScript-heavy pages

Requirements:
    pip install playwright
    playwright install chromium

Note: This example uses Playwright. You can also use Puppeteer with Node.js.

Usage:
    python examples/demo_scraping_browser.py
"""

import asyncio
import logging
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")

load_dotenv(dotenv_path=Path(__file__).resolve().parents[1] / ".env")

# Scraping Browser WebSocket endpoint
# Format: wss://td-customer-{USERNAME}:{PASSWORD}@ws-browser.thordata.com
USERNAME = os.getenv("THORDATA_BROWSER_USERNAME")
PASSWORD = os.getenv("THORDATA_BROWSER_PASSWORD")

if not USERNAME or not PASSWORD:
    print("❌ Error: Scraping Browser credentials required")
    print("   Set THORDATA_BROWSER_USERNAME and THORDATA_BROWSER_PASSWORD in .env")
    print("")
    print("   Note: Scraping Browser uses separate credentials from the Proxy API.")
    print("   Get them from: Thordata Dashboard > Scraping > Scraping Browser")
    sys.exit(1)

WS_ENDPOINT = f"wss://td-customer-{USERNAME}:{PASSWORD}@ws-browser.thordata.com"


async def demo_basic_navigation():
    """Basic page navigation with Scraping Browser."""
    print("\n" + "=" * 50)
    print("1️⃣  Basic Navigation")
    print("=" * 50)

    try:
        from playwright.async_api import async_playwright
    except ImportError:
        print("⚠️  Playwright not installed. Run:")
        print("   pip install playwright")
        print("   playwright install chromium")
        return

    try:
        async with async_playwright() as p:
            print("   Connecting to Scraping Browser...")

            # Connect to remote browser
            browser = await p.chromium.connect_over_cdp(WS_ENDPOINT)

            print("   ✅ Connected!")

            # Create a new page
            context = await browser.new_context(viewport={"width": 1366, "height": 768})
            page = await context.new_page()

            # Navigate to a page
            url = "https://example.com"
            print(f"   Navigating to {url}...")

            await page.goto(url, wait_until="domcontentloaded")

            # Get page title
            title = await page.title()
            print(f"   Page title: {title}")

            # Get page content
            content = await page.content()
            print(f"   Content length: {len(content)} characters")

            # Take screenshot
            screenshot = await page.screenshot()
            with open("browser_screenshot.png", "wb") as f:
                f.write(screenshot)
            print("   Screenshot saved: browser_screenshot.png")

            await browser.close()
            print("   ✅ Browser closed")

    except Exception as e:
        print(f"❌ Error: {e}")


async def demo_search_interaction():
    """Interactive search with form filling."""
    print("\n" + "=" * 50)
    print("2️⃣  Search Interaction")
    print("=" * 50)

    try:
        from playwright.async_api import async_playwright
    except ImportError:
        print("⚠️  Playwright not installed")
        return

    try:
        async with async_playwright() as p:
            browser = await p.chromium.connect_over_cdp(WS_ENDPOINT)
            context = await browser.new_context()
            page = await context.new_page()

            # Go to Bing
            print("   Navigating to Bing...")
            await page.goto("https://www.bing.com", wait_until="networkidle")

            # Search for something
            search_query = "Python programming"
            print(f"   Searching for: {search_query}")

            # Type in search box
            await page.fill('input[name="q"]', search_query)
            await page.keyboard.press("Enter")

            # Wait for results
            await page.wait_for_load_state("networkidle")

            # Get search results
            results = await page.query_selector_all("li.b_algo h2 a")
            print(f"   Found {len(results)} search results")

            for i, result in enumerate(results[:5], 1):
                title = await result.inner_text()
                await result.get_attribute("href")
                print(f"   {i}. {title[:50]}...")

            await browser.close()
            print("   ✅ Complete")

    except Exception as e:
        print(f"❌ Error: {e}")


async def demo_dynamic_content():
    """Handling JavaScript-rendered dynamic content."""
    print("\n" + "=" * 50)
    print("3️⃣  Dynamic Content (JS Rendering)")
    print("=" * 50)

    try:
        from playwright.async_api import async_playwright
    except ImportError:
        print("⚠️  Playwright not installed")
        return

    try:
        async with async_playwright() as p:
            browser = await p.chromium.connect_over_cdp(WS_ENDPOINT)
            context = await browser.new_context()
            page = await context.new_page()

            # Navigate to a JS-heavy page
            url = "https://news.ycombinator.com"
            print(f"   Navigating to {url}...")

            await page.goto(url, wait_until="networkidle")

            # Wait for specific element
            await page.wait_for_selector(".itemlist", timeout=10000)

            # Extract news items
            items = await page.query_selector_all(".athing .titleline > a")
            print(f"   Found {len(items)} news items")

            for i, item in enumerate(items[:5], 1):
                title = await item.inner_text()
                print(f"   {i}. {title[:60]}...")

            await browser.close()
            print("   ✅ Complete")

    except Exception as e:
        print(f"❌ Error: {e}")


def show_puppeteer_example():
    """Show equivalent Puppeteer (Node.js) code."""
    print("\n" + "=" * 50)
    print("📝 Puppeteer (Node.js) Example")
    print("=" * 50)

    code = """
const puppeteer = require('puppeteer-core');

const WS_ENDPOINT = 'wss://td-customer-USERNAME:PASSWORD@ws-browser.thordata.com';

async function main() {
    const browser = await puppeteer.connect({
        browserWSEndpoint: WS_ENDPOINT,
        defaultViewport: { width: 1366, height: 768 }
    });

    const page = await browser.newPage();
    await page.goto('https://example.com');

    const title = await page.title();
    console.log('Page title:', title);

    await browser.close();
}

main();
"""
    print(code)


if __name__ == "__main__":
    print("=" * 50)
    print("   Thordata SDK - Scraping Browser Demo")
    print("=" * 50)

    # Check if playwright is available
    try:

        HAS_PLAYWRIGHT = True
    except ImportError:
        HAS_PLAYWRIGHT = False
        print("\n⚠️  Playwright not installed.")
        print("   To run the interactive demos, install it:")
        print("   pip install playwright")
        print("   playwright install chromium")

    if HAS_PLAYWRIGHT:
        asyncio.run(demo_basic_navigation())
        asyncio.run(demo_search_interaction())
        asyncio.run(demo_dynamic_content())

    # Always show the Node.js example
    show_puppeteer_example()

    print("\n" + "=" * 50)
    print("   Demo Complete!")
    print("=" * 50)
