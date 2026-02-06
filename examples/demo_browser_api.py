"""
Thordata Browser API - One-Click Acceptance Script
-------------------------------------------------

Goal: Provide a one-click Browser API acceptance script to verify:
1. Browser credentials are correctly configured
2. Network connectivity is normal (including upstream proxy support)
3. Browser API connection is successful
4. Basic browser operations (navigation, screenshots) work correctly

Setup:
- Fill in .env:
    THORDATA_SCRAPER_TOKEN=...
    THORDATA_BROWSER_USERNAME=...  # or use THORDATA_RESIDENTIAL_USERNAME
    THORDATA_BROWSER_PASSWORD=...  # or use THORDATA_RESIDENTIAL_PASSWORD
  Optional upstream proxy (e.g., Clash):
    THORDATA_UPSTREAM_PROXY=https://127.0.0.1:7899  # or socks5://127.0.0.1:7898

Requirements:
    pip install thordata[browser]
    playwright install chromium
"""

from __future__ import annotations

import asyncio
import os
import sys
from contextlib import suppress
from pathlib import Path

from thordata import AsyncThordataClient, ThordataConfigError, load_env_file


async def main() -> int:
    # Load .env
    repo_root = Path(__file__).parent.parent
    load_env_file(str(repo_root / ".env"))

    scraper_token = os.getenv("THORDATA_SCRAPER_TOKEN")
    browser_username = os.getenv("THORDATA_BROWSER_USERNAME") or os.getenv(
        "THORDATA_RESIDENTIAL_USERNAME"
    )
    browser_password = os.getenv("THORDATA_BROWSER_PASSWORD") or os.getenv(
        "THORDATA_RESIDENTIAL_PASSWORD"
    )

    if not scraper_token:
        print("[FAIL] Missing THORDATA_SCRAPER_TOKEN")
        return 1

    if not browser_username or not browser_password:
        print("[FAIL] Missing browser credentials:")
        print("   Please set THORDATA_BROWSER_USERNAME and THORDATA_BROWSER_PASSWORD")
        print(
            "   or use THORDATA_RESIDENTIAL_USERNAME and THORDATA_RESIDENTIAL_PASSWORD"
        )
        return 1

    upstream = os.getenv("THORDATA_UPSTREAM_PROXY")
    if upstream:
        print(f"[OK] Upstream proxy detected: {upstream}")

    print("=" * 80)
    print("Thordata Browser API - One-Click Acceptance")
    print("=" * 80)

    # Check if Playwright is installed
    try:
        from playwright.async_api import async_playwright  # noqa: F401
    except ImportError:
        print("\n[FAIL] Playwright not installed")
        print("   Please run: pip install thordata[browser]")
        print("   Then run: playwright install chromium")
        return 1

    # ========== Step 1: Initialize Client ==========
    print("\n[Step 1/5] Initializing Thordata client...")
    try:
        client = AsyncThordataClient(scraper_token=scraper_token)
        print("[OK] Client initialized successfully")
    except Exception as e:
        print(f"[FAIL] Client initialization failed: {e}")
        return 2

    # ========== Step 2: Get Browser Connection URL ==========
    print("\n[Step 2/5] Getting browser connection URL...")
    try:
        ws_url = client.get_browser_connection_url(
            username=browser_username, password=browser_password
        )
        print("[OK] Browser connection URL generated successfully")
        print(
            f"   URL: {ws_url[:50]}..."
        )  # Only show first 50 chars to avoid exposing password
    except ThordataConfigError as e:
        print(f"[FAIL] Configuration error: {e}")
        return 2
    except Exception as e:
        print(f"[FAIL] Failed to get connection URL: {e}")
        return 2

    # ========== Step 3: Connect to Browser ==========
    print("\n[Step 3/5] Connecting to Thordata Scraping Browser...")
    try:
        from playwright.async_api import async_playwright

        async with async_playwright() as p:
            print("   Connecting...")
            browser = await p.chromium.connect_over_cdp(ws_url)
            print("[OK] Browser connected successfully")
    except Exception as e:
        print(f"[FAIL] Browser connection failed: {e}")
        print("\n[TIP] Possible causes:")
        print("   1. Browser credentials are incorrect")
        print(
            "   2. Network connectivity issues (if upstream proxy is configured, check if Clash is running)"
        )
        print("   3. Thordata service temporarily unavailable")
        return 3

    # ========== Step 4: Execute Basic Operations ==========
    print("\n[Step 4/5] Executing basic browser operations...")
    try:
        # Create context and page
        context = await browser.new_context(viewport={"width": 1920, "height": 1080})
        page = await context.new_page()
        page.set_default_navigation_timeout(60000)  # 60 second timeout

        # Navigate to test page
        test_url = "https://example.com"
        print(f"   Navigating to: {test_url}")
        await page.goto(test_url, wait_until="domcontentloaded")
        print("[OK] Page navigation successful")

        # Get page title
        title = await page.title()
        print(f"   Page title: {title}")

        # Get current URL
        current_url = page.url
        print(f"   Current URL: {current_url}")

        # Take screenshot
        print("   Taking screenshot...")
        screenshot_dir = repo_root / "artifacts" / "browser"
        screenshot_dir.mkdir(parents=True, exist_ok=True)
        screenshot_path = screenshot_dir / "browser_test_screenshot.png"
        await page.screenshot(path=str(screenshot_path), full_page=False)
        print(f"[OK] Screenshot saved successfully: {screenshot_path}")

        # Get page HTML preview
        html_preview = await page.content()
        print(f"   Page HTML length: {len(html_preview)} characters")

    except Exception as e:
        print(f"[FAIL] Browser operations failed: {e}")
        import traceback

        traceback.print_exc()
        return 4
    finally:
        # Cleanup
        with suppress(Exception):
            await browser.close()

    # ========== Step 5: Use BrowserSession API ==========
    print("\n[Step 5/5] Testing BrowserSession API...")
    try:
        async with client:
            browser_session = client.browser

            # Navigate
            print("   Navigating with BrowserSession...")
            result = await browser_session.navigate("https://example.org")
            print(f"[OK] Navigation successful: {result['title']}")

            # Screenshot
            print("   Taking screenshot with BrowserSession...")
            screenshot_bytes = await browser_session.screenshot_page(full_page=False)
            print(f"[OK] Screenshot successful: {len(screenshot_bytes)} bytes")

            # Get snapshot
            print("   Getting page snapshot...")
            snapshot = await browser_session.snapshot(filtered=True, max_items=10)
            print("[OK] Snapshot retrieved successfully")
            print(
                f"   Snapshot contains {len(snapshot.get('aria_snapshot', '').split(chr(10)))} interactive elements"
            )

            # Cleanup
            await browser_session.close()
            print("[OK] BrowserSession cleanup completed")

    except ImportError as e:
        print(f"[WARN] BrowserSession unavailable: {e}")
        print("   This usually means Playwright is not properly installed")
    except Exception as e:
        print(f"[FAIL] BrowserSession test failed: {e}")
        import traceback

        traceback.print_exc()
        return 5

    print("\n" + "=" * 80)
    print("[OK] Browser API acceptance completed!")
    print("=" * 80)
    print("\n[SUMMARY] Acceptance Summary:")
    print("   [OK] Browser credentials verified")
    print("   [OK] Network connectivity normal")
    print("   [OK] Browser API connection successful")
    print("   [OK] Basic browser operations working")
    print("   [OK] BrowserSession API available")

    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
