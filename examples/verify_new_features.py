"""
Verification script for newly added features.

This script allows you to selectively test new API endpoints
with your real credentials.

Usage:
    # Test specific feature
    python examples/verify_new_features.py --test usage_stats

    # Test all features
    python examples/verify_new_features.py --test all

Available tests:
    - video_task: Video/audio download task creation
    - usage_stats: Account usage statistics
    - proxy_users: Proxy user management
    - whitelist: IP whitelist management
    - proxy_servers: ISP/DC proxy list
    - api_new_balance: Public API NEW - residential balance
    - api_new_isp: Public API NEW - ISP proxies
"""

import argparse
import os
import sys
from datetime import date, timedelta
from pathlib import Path

try:
    from dotenv import load_dotenv

    load_dotenv(dotenv_path=Path(__file__).resolve().parents[1] / ".env")
except ImportError:
    pass

from thordata import (
    CommonSettings,
    ProxyType,
    ThordataClient,
)


def test_video_task(client: ThordataClient) -> bool:
    """Test video_builder endpoint."""
    print("\n" + "=" * 60)
    print("Testing: Video Task Creation")
    print("=" * 60)

    try:
        # Note: This will actually create a task!
        # Adjust URL to a test video or comment out if you don't want to create real tasks
        task_id = client.create_video_task(
            file_name="test_{{VideoID}}",
            spider_id="youtube_video_by-url",
            spider_name="youtube.com",
            parameters={
                "url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",  # Example
            },
            common_settings=CommonSettings(
                resolution="720p",
                is_subtitles="false",
            ),
        )
        print(f"✅ Video task created: {task_id}")
        return True
    except Exception as e:
        print(f"❌ Failed: {e}")
        return False


def test_usage_stats(client: ThordataClient) -> bool:
    """Test usage statistics API."""
    print("\n" + "=" * 60)
    print("Testing: Usage Statistics")
    print("=" * 60)

    try:
        today = date.today()
        week_ago = today - timedelta(days=7)

        stats = client.get_usage_statistics(week_ago, today)

        print("✅ Usage Statistics Retrieved:")
        print(f"   Total Usage: {stats.total_usage_gb():.2f} GB")
        print(f"   Balance: {stats.balance_gb():.2f} GB")
        print(f"   Range Usage: {stats.range_usage_gb():.2f} GB")
        print(f"   Query Days: {stats.query_days}")
        return True
    except Exception as e:
        print(f"❌ Failed: {e}")
        return False


def test_proxy_users(client: ThordataClient) -> bool:
    """Test proxy user management."""
    print("\n" + "=" * 60)
    print("Testing: Proxy Users Management")
    print("=" * 60)

    try:
        users = client.list_proxy_users(proxy_type=ProxyType.RESIDENTIAL)

        print("✅ Proxy Users Retrieved:")
        print(f"   Total Users: {users.user_count}")
        print(f"   Limit: {users.limit / (1024**2):.2f} MB")
        print(f"   Remaining: {users.remaining_limit / (1024**2):.2f} MB")

        for i, user in enumerate(users.users[:3], 1):
            print(f"   User {i}: {user.username}")
            print(f"      Status: {'Enabled' if user.status else 'Disabled'}")
            print(f"      Usage: {user.usage_gb():.2f} GB")

        return True
    except Exception as e:
        print(f"❌ Failed: {e}")
        return False


def test_whitelist(client: ThordataClient) -> bool:
    """Test whitelist IP management."""
    print("\n" + "=" * 60)
    print("Testing: Whitelist IP Management")
    print("=" * 60)

    # This is read-only test - we don't actually add IPs
    print("⚠️  Skipping actual IP addition (would modify account)")
    print("    To test, uncomment and provide a test IP:")
    print("    # result = client.add_whitelist_ip('1.2.3.4', status=False)")
    return True


def test_proxy_servers(client: ThordataClient) -> bool:
    """Test proxy server list."""
    print("\n" + "=" * 60)
    print("Testing: Proxy Servers List")
    print("=" * 60)

    try:
        # Try ISP proxies (type=1)
        servers = client.list_proxy_servers(proxy_type=1)

        print("✅ ISP Proxy Servers Retrieved:")
        print(f"   Total Servers: {len(servers)}")

        for i, server in enumerate(servers[:3], 1):
            print(f"   Server {i}: {server.ip}:{server.port}")
            print(f"      Username: {server.username}")
            print(f"      Expiration: {server.expiration_time}")

        return True
    except Exception as e:
        print(f"❌ Failed (may not have ISP proxies): {e}")
        return False


def test_api_new_balance(client: ThordataClient) -> bool:
    """Test Public API NEW - residential balance."""
    print("\n" + "=" * 60)
    print("Testing: Public API NEW - Residential Balance")
    print("=" * 60)

    try:
        result = client.get_residential_balance()

        balance_gb = result["balance"] / (1024**3)
        print("✅ Residential Balance Retrieved:")
        print(f"   Balance: {balance_gb:.2f} GB")
        print(f"   Expire Time: {result.get('expire_time')}")
        return True
    except Exception as e:
        print(f"❌ Failed (requires sign/apiKey): {e}")
        return False


def test_api_new_isp(client: ThordataClient) -> bool:
    """Test Public API NEW - ISP proxies."""
    print("\n" + "=" * 60)
    print("Testing: Public API NEW - ISP Proxies")
    print("=" * 60)

    try:
        regions = client.get_isp_regions()

        print("✅ ISP Regions Retrieved:")
        print(f"   Total Regions: {len(regions)}")

        for region in regions[:3]:
            print(
                f"   {region.get('country')}/{region.get('city')}: {region.get('num')} IPs"
            )

        # Try listing ISP proxies
        proxies = client.list_isp_proxies()
        print(f"\n   ISP Proxies: {len(proxies)} proxies")

        return True
    except Exception as e:
        print(f"❌ Failed (requires sign/apiKey): {e}")
        return False


def main():
    parser = argparse.ArgumentParser(description="Verify new Thordata SDK features")
    parser.add_argument(
        "--test",
        choices=[
            "video_task",
            "usage_stats",
            "proxy_users",
            "whitelist",
            "proxy_servers",
            "api_new_balance",
            "api_new_isp",
            "all",
        ],
        default="all",
        help="Which test to run",
    )

    args = parser.parse_args()

    # Check credentials
    scraper_token = os.getenv("THORDATA_SCRAPER_TOKEN")
    public_token = os.getenv("THORDATA_PUBLIC_TOKEN")
    public_key = os.getenv("THORDATA_PUBLIC_KEY")

    # Fallback Allowed: If SIGN/API_KEY is not set, use PUBLIC_TOKEN/KEY
    sign = os.getenv("THORDATA_SIGN") or public_token
    api_key = os.getenv("THORDATA_API_KEY") or public_key

    if not scraper_token:
        print("❌ Error: THORDATA_SCRAPER_TOKEN is required")
        return 1

    print("=" * 60)
    print("Thordata SDK - New Features Verification")
    print("=" * 60)
    print("Credentials loaded:")
    print(f"  SCRAPER_TOKEN: {'✓' if scraper_token else '✗'}")
    print(f"  PUBLIC_TOKEN:  {'✓' if public_token else '✗'}")
    print(f"  PUBLIC_KEY:    {'✓' if public_key else '✗'}")
    print(f"  SIGN:          {'✓' if sign else '✗'} (for API NEW)")
    print(f"  API_KEY:       {'✓' if api_key else '✗'} (for API NEW)")

    # Create client
    client = ThordataClient(
        scraper_token=scraper_token,
        public_token=public_token,
        public_key=public_key,
        sign=sign,
        api_key=api_key,
    )

    # Test map
    tests = {
        "video_task": test_video_task,
        "usage_stats": test_usage_stats,
        "proxy_users": test_proxy_users,
        "whitelist": test_whitelist,
        "proxy_servers": test_proxy_servers,
        "api_new_balance": test_api_new_balance,
        "api_new_isp": test_api_new_isp,
    }

    # Run tests
    results = {}

    if args.test == "all":
        for name, func in tests.items():
            results[name] = func(client)
    else:
        results[args.test] = tests[args.test](client)

    # Summary
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)

    for name, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status} - {name}")

    passed_count = sum(results.values())
    total_count = len(results)
    print(f"\nTotal: {passed_count}/{total_count} passed")

    return 0 if passed_count == total_count else 1


if __name__ == "__main__":
    sys.exit(main())
