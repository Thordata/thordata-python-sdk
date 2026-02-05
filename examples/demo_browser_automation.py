"""Example: Browser automation with Thordata Scraping Browser.

This example demonstrates how to use the browser automation features
of the Thordata Python SDK.

Requirements:
    pip install thordata[browser]

Environment variables:
    THORDATA_SCRAPER_TOKEN - Your scraper token
    THORDATA_BROWSER_USERNAME - Browser username
    THORDATA_BROWSER_PASSWORD - Browser password
"""

import asyncio
import os

from thordata import AsyncThordataClient


async def main():
    """Main example function."""
    # Initialize client
    client = AsyncThordataClient(scraper_token=os.getenv("THORDATA_SCRAPER_TOKEN"))

    async with client:
        # Get browser session
        browser = client.browser

        try:
            # Navigate to a page
            print("Navigating to example.com...")
            result = await browser.navigate("https://example.com")
            print(f"Page title: {result['title']}")
            print(f"Page URL: {result['url']}")

            # Capture snapshot
            print("\nCapturing page snapshot...")
            snapshot = await browser.snapshot(filtered=True, max_items=10)
            print(f"Snapshot URL: {snapshot['url']}")
            print(f"Snapshot title: {snapshot['title']}")
            print(f"\nInteractive elements:\n{snapshot['aria_snapshot']}")

            # Get HTML content
            print("\nGetting page HTML...")
            html = await browser.get_html(full_page=False)
            print(f"HTML length: {len(html)} characters")

            # Take screenshot
            print("\nTaking screenshot...")
            screenshot = await browser.screenshot_page(full_page=False)
            print(f"Screenshot size: {len(screenshot)} bytes")

            # Scroll page
            print("\nScrolling page...")
            await browser.scroll()

            # Navigate to another page
            print("\nNavigating to another page...")
            await browser.navigate("https://example.org")

            # Go back
            print("\nGoing back...")
            result = await browser.go_back()
            print(f"Current URL: {result['url']}")

        finally:
            # Clean up
            await browser.close()


if __name__ == "__main__":
    asyncio.run(main())
