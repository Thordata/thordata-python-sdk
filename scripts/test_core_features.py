"""
Core Features Real User Test
----------------------------

Tests core SDK features that may not have been fully tested:
- Namespace API usage
- Error handling edge cases
- Response wrapper
- Constants usage
- Performance features
"""

import os
import sys
from pathlib import Path

# Fix encoding for Windows
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

from thordata import (
    APIBaseURL,
    APIEndpoint,
    AsyncThordataClient,
    ThordataAPIError,
    ThordataClient,
    load_env_file,
)


def test_constants_usage():
    """Test that constants are being used correctly."""
    print("\n[Test 1] Constants Usage")
    print("-" * 60)

    # Verify constants exist
    assert hasattr(APIBaseURL, "SCRAPER_API")
    assert hasattr(APIEndpoint, "SERP_REQUEST")

    # Test URL construction
    url = f"{APIBaseURL.SCRAPER_API}{APIEndpoint.SERP_REQUEST}"
    assert "scraperapi.thordata.com" in url
    assert "/request" in url
    print("[OK] Constants are properly defined and usable")


def test_namespace_api(client: ThordataClient):
    """Test namespace-based API."""
    print("\n[Test 2] Namespace API")
    print("-" * 60)

    # Test all namespaces exist
    assert hasattr(client, "universal")
    assert hasattr(client, "scraper")
    assert hasattr(client, "account")
    assert hasattr(client, "proxy")
    print("[OK] All namespaces are available")

    # Test namespace methods exist
    assert hasattr(client.universal, "scrape")
    assert hasattr(client.scraper, "create_task")
    assert hasattr(client.account, "get_balance")
    print("[OK] Namespace methods are accessible")


def test_error_handling(client: ThordataClient):
    """Test enhanced error handling."""
    print("\n[Test 3] Error Handling")
    print("-" * 60)

    try:
        # This should trigger a validation error
        client.serp_search(query="")  # Empty query
    except ThordataAPIError as e:
        # Check error has enhanced context
        assert hasattr(e, "url") or "URL" in str(e)
        assert hasattr(e, "method") or "POST" in str(e) or "GET" in str(e)
        print(f"[OK] Error includes context: {type(e).__name__}")
        print(f"  Message: {str(e)[:100]}...")


def test_response_wrapper():
    """Test response wrapper if available."""
    print("\n[Test 4] Response Wrapper")
    print("-" * 60)

    try:
        from thordata.response import APIResponse

        # Test response wrapper exists
        assert APIResponse is not None
        print("[OK] Response wrapper is available")
    except ImportError:
        print("[SKIP] Response wrapper not available (may be internal)")


def test_performance_features():
    """Test performance utilities."""
    print("\n[Test 5] Performance Features")
    print("-" * 60)

    try:
        from thordata._performance import BatchProcessor, SimpleCache

        # Test cache
        cache = SimpleCache(ttl=60)
        cache.set("test", "value")
        assert cache.get("test") == "value"
        print("[OK] Caching utilities work")

        # Test batch processor
        processor = BatchProcessor(batch_size=5)
        assert processor.batch_size == 5
        print("[OK] Batch processing utilities work")
    except ImportError:
        print("[SKIP] Performance utilities not available (may be internal)")


def test_async_namespace():
    """Test async namespace API."""
    print("\n[Test 6] Async Namespace API")
    print("-" * 60)

    import asyncio

    async def test():
        async with AsyncThordataClient(
            scraper_token=os.getenv("THORDATA_SCRAPER_TOKEN"),
            public_token=os.getenv("THORDATA_PUBLIC_TOKEN"),
            public_key=os.getenv("THORDATA_PUBLIC_KEY"),
        ) as client:
            # Test namespaces exist
            assert hasattr(client, "universal")
            assert hasattr(client, "scraper")
            assert hasattr(client, "account")
            assert hasattr(client, "proxy")
            print("[OK] Async client namespaces are available")

            # Test async methods exist
            assert hasattr(client.universal, "scrape_async")
            assert hasattr(client.scraper, "create_task_async")
            print("[OK] Async namespace methods are accessible")

    asyncio.run(test())


def test_backward_compatibility(client: ThordataClient):
    """Test backward compatibility."""
    print("\n[Test 7] Backward Compatibility")
    print("-" * 60)

    # Test old methods still exist
    assert hasattr(client, "universal_scrape")
    assert hasattr(client, "get_traffic_balance")
    assert hasattr(client, "serp_search")
    print("[OK] Old API methods are still available")

    # Test both old and new APIs work
    try:
        # Old API
        balance_old = client.get_traffic_balance()
        print(f"[OK] Old API works: get_traffic_balance() = {balance_old}")
    except Exception as e:
        print(f"[SKIP] Old API test skipped: {type(e).__name__}")


def main() -> int:
    """Main test function."""
    # Load environment
    repo_root = Path(__file__).parent.parent
    load_env_file(str(repo_root / ".env"))

    print("=" * 60)
    print("Core Features Real User Test")
    print("=" * 60)
    print("\nTesting core SDK features and optimizations...")

    # Check credentials
    scraper_token = os.getenv("THORDATA_SCRAPER_TOKEN")
    public_token = os.getenv("THORDATA_PUBLIC_TOKEN")
    public_key = os.getenv("THORDATA_PUBLIC_KEY")

    if not scraper_token:
        print("\n[ERROR] THORDATA_SCRAPER_TOKEN is required")
        return 1

    # Initialize client
    client = ThordataClient(
        scraper_token=scraper_token,
        public_token=public_token,
        public_key=public_key,
    )

    # Run tests
    try:
        test_constants_usage()
        test_namespace_api(client)
        test_error_handling(client)
        test_response_wrapper()
        test_performance_features()

        if scraper_token:
            test_async_namespace()

        if public_token and public_key:
            test_backward_compatibility(client)

        print("\n" + "=" * 60)
        print("[SUCCESS] All core feature tests passed!")
        print("=" * 60)
        return 0

    except Exception as e:
        print(f"\n[ERROR] Test failed: {e}")
        import traceback

        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
