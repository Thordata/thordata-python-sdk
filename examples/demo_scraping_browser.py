"""
Scraping Browser Demo - Advanced Automation (Amazon)

Matches the capability of the Node.js Puppeteer examples.
Demonstrates:
1. Connecting to Thordata Scraping Browser
2. navigating to Amazon
3. Waiting for selectors
4. Parsing results

Requirements:
    pip install playwright
    playwright install chromium
"""

import asyncio
import logging
import os
import sys
from typing import Dict, List

try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    pass

from thordata import AsyncThordataClient, ThordataConfigError

# Configure Logging
logging.basicConfig(level=logging.INFO, format="[%(asctime)s] %(message)s")
logger = logging.getLogger("browser_demo")


async def scrape_amazon_products(keyword: str = "thinkpad") -> List[Dict]:
    """
    Scrape Amazon search results using Playwright over CDP.
    """
    # 1. Initialize Client to get the Secure WebSocket URL
    client = AsyncThordataClient()

    try:
        # Automatically loads THORDATA_BROWSER_USERNAME / THORDATA_RESIDENTIAL_USERNAME
        ws_endpoint = client.get_browser_connection_url()
        logger.info("✅ Generated WebSocket Endpoint")
    except ThordataConfigError as e:
        logger.error(f"❌ Config Error: {e}")
        return []

    try:
        from playwright.async_api import async_playwright  # type: ignore
    except ImportError:
        logger.error(
            "❌ Playwright not installed. Run: pip install playwright && playwright install chromium"
        )
        return []

    results = []

    async with async_playwright() as p:
        logger.info("🔌 Connecting to Scraping Browser...")

        # Connect to the remote browser
        browser = await p.chromium.connect_over_cdp(ws_endpoint)

        try:
            # Create context & page
            context = await browser.new_context(viewport={"width": 1366, "height": 768})
            page = await context.new_page()
            page.set_default_navigation_timeout(
                120000
            )  # 2 mins timeout for proxy latency

            # Navigate
            url = f"https://www.amazon.com/s?k={keyword}"
            logger.info(f"🧭 Navigating to: {url}")
            await page.goto(url, wait_until="domcontentloaded")

            # Handling Anti-bot / Captcha is done automatically by the browser,
            # but we wait for the content container to be sure.
            selector = '[data-component-type="s-search-result"]'
            logger.info("⏳ Waiting for product list...")
            try:
                await page.wait_for_selector(selector, timeout=30000)
            except Exception:
                logger.warning("⚠️ Selector timeout. Taking screenshot...")
                await page.screenshot(path="amazon_error.png")
                raise

            # Extract Data
            logger.info("📄 Parsing results...")
            results = await page.evaluate(f"""() => {{
                const items = Array.from(document.querySelectorAll('{selector}'));
                return items.map(item => {{
                    const titleEl = item.querySelector('h2 a span');
                    const priceEl = item.querySelector('.a-price .a-offscreen');
                    const linkEl = item.querySelector('h2 a');
                    
                    if (!titleEl) return null;
                    
                    return {{
                        title: titleEl.innerText,
                        price: priceEl ? priceEl.innerText : 'N/A',
                        url: linkEl ? linkEl.href : ''
                    }};
                }}).filter(i => i !== null);
            }}""")

            logger.info(f"🎉 Found {len(results)} products")
            for idx, item in enumerate(results[:5], 1):
                logger.info(f"   {idx}. {item['title'][:50]}... | {item['price']}")

        except Exception as e:
            logger.error(f"❌ Browser Automation Failed: {e}")
        finally:
            await browser.close()
            logger.info("🔒 Browser closed")

    return results


if __name__ == "__main__":
    if not os.getenv("THORDATA_BROWSER_USERNAME"):
        logger.error("Please set THORDATA_BROWSER_USERNAME and PASSWORD in .env")
        sys.exit(1)

    asyncio.run(scrape_amazon_products("gaming laptop"))
