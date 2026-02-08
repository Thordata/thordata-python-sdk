"""
Quick Start Acceptance Test
---------------------------

Runs a quick validation of all core SDK features in sequence.
This is the fastest way to verify your SDK setup is working correctly.
"""

from __future__ import annotations

import os
import time
from pathlib import Path

from thordata import ThordataClient, load_env_file


def print_section(title: str) -> None:
    """Print a section header."""
    print("\n" + "=" * 80)
    print(title)
    print("=" * 80)


def test_serp_api(client: ThordataClient) -> bool:
    """Test SERP API."""
    print_section("1. Testing SERP API")
    try:
        result = client.serp_search(query="Thordata", engine="google", num=3)
        if result.get("organic"):
            print(
                f"[OK] SERP API working - Got {len(result.get('organic', []))} results"
            )
            return True
        else:
            print("[WARN] SERP API returned no results")
            return False
    except Exception as e:
        print(f"[FAIL] SERP API failed: {e}")
        return False


def test_universal_api(client: ThordataClient) -> bool:
    """Test Universal Scrape API."""
    print_section("2. Testing Universal Scrape API")
    try:
        # Use new namespace API (recommended)
        html = client.universal.scrape(
            url="https://www.example.com",
            js_render=True,
            country="us",
        )
        html_str = html if isinstance(html, str) else str(html)
        if html_str and len(html_str) > 200:
            print(f"[OK] Web Unlocker working - Got {len(html_str)} bytes")
            return True
        else:
            print("[WARN] Web Unlocker returned minimal content")
            return False
    except Exception as e:
        print(f"[FAIL] Universal Scrape failed: {e}")
        return False


def test_account_api(client: ThordataClient) -> bool:
    """Test Account Management API."""
    print_section("3. Testing Account Management API")
    try:
        traffic = client.get_traffic_balance()
        wallet = client.get_wallet_balance()
        print(f"[OK] Account API working - Traffic: {traffic} KB, Wallet: ${wallet}")
        return True
    except Exception as e:
        print(f"[FAIL] Account API failed: {e}")
        return False


def test_web_scraper_api(client: ThordataClient) -> bool:
    """Test Web Scraper API (quick test - just create task)."""
    print_section("4. Testing Web Scraper API")
    try:
        from thordata.tools import Amazon

        # Use new namespace API (recommended)
        task_id = client.scraper.run_tool(Amazon.ProductByAsin(asin="B0BZYCJK89"))
        print(f"[OK] Web Scraper API working - Task created: {task_id}")
        print("     (Task is running in background, check status later)")
        return True
    except Exception as e:
        print(f"[FAIL] Web Scraper API failed: {e}")
        return False


def main() -> int:
    """Main function."""
    # Load .env
    repo_root = Path(__file__).parent.parent
    load_env_file(str(repo_root / ".env"))

    print("=" * 80)
    print("Thordata SDK - Quick Start Acceptance Test")
    print("=" * 80)
    print("\nThis script quickly validates all core SDK features.")
    print("For detailed testing, use individual demo scripts.\n")

    # Check credentials
    scraper_token = os.getenv("THORDATA_SCRAPER_TOKEN")
    public_token = os.getenv("THORDATA_PUBLIC_TOKEN")
    public_key = os.getenv("THORDATA_PUBLIC_KEY")

    if not scraper_token:
        print("[FAIL] THORDATA_SCRAPER_TOKEN is required")
        print("  Run: python examples/validate_env.py")
        return 1

    if not public_token or not public_key:
        print(
            "[WARN] THORDATA_PUBLIC_TOKEN/KEY not set - Account API tests will be skipped"
        )

    # Initialize client
    client = ThordataClient(
        scraper_token=scraper_token,
        public_token=public_token,
        public_key=public_key,
        api_timeout=60,
    )

    results: dict[str, bool] = {}

    # Run tests
    start_time = time.time()

    results["SERP"] = test_serp_api(client)
    time.sleep(1)  # Brief pause between tests

    results["Universal"] = test_universal_api(client)
    time.sleep(1)

    if public_token and public_key:
        results["Account"] = test_account_api(client)
        time.sleep(1)

        results["Web Scraper"] = test_web_scraper_api(client)

    elapsed = time.time() - start_time

    # Summary
    print_section("Test Summary")
    total = len(results)
    passed = sum(1 for v in results.values() if v)
    failed = total - passed

    for name, success in results.items():
        status = "[OK]" if success else "[FAIL]"
        print(f"  {status} {name}")

    print(f"\nResults: {passed}/{total} passed")
    print(f"Time: {elapsed:.1f}s")

    if failed == 0:
        print("\n[SUCCESS] All tests passed! Your SDK is configured correctly.")
        return 0
    else:
        print(f"\n[WARN] {failed} test(s) failed. Check your configuration.")
        print("  Run: python examples/validate_env.py")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
