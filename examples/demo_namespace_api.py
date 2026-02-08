"""
Demo: New Namespace API Design
-------------------------------

This example demonstrates the improved namespace-based API design,
showing how the SDK is now more organized and easier to use.

Key improvements:
1. Organized namespaces (universal, scraper, account, proxy)
2. Constants for type safety
3. Enhanced error messages
4. Unified response handling
"""

from __future__ import annotations

import os
from pathlib import Path

from thordata import (
    APIBaseURL,
    APIEndpoint,
    APIResponse,
    EnvVar,
    ThordataClient,
    load_env_file,
)


def print_section(title: str) -> None:
    """Print a section header."""
    print("\n" + "=" * 80)
    print(title)
    print("=" * 80)


def demo_constants() -> None:
    """Demonstrate using constants for type safety."""
    print_section("1. Using Constants (Type Safety)")

    # Before: Hard-coded strings (error-prone)
    # url = "https://scraperapi.thordata.com/request"

    # After: Constants (type-safe, IDE autocomplete)
    base_url = APIBaseURL.SCRAPER_API
    endpoint = APIEndpoint.SERP_REQUEST
    full_url = f"{base_url}{endpoint}"

    print(f"Base URL: {base_url}")
    print(f"Endpoint: {endpoint}")
    print(f"Full URL: {full_url}")

    # Environment variable constants
    print("\nEnvironment Variables:")
    print(f"  Scraper Token: {EnvVar.SCRAPER_TOKEN}")
    print(f"  Public Token: {EnvVar.PUBLIC_TOKEN}")
    print(f"  Public Key: {EnvVar.PUBLIC_KEY}")


def demo_namespaces(client: ThordataClient) -> None:
    """Demonstrate the new namespace-based API."""
    print_section("2. Using Namespaces (Better Organization)")

    # Universal Scraping Namespace
    print("\n[Universal Scraping Namespace]")
    print("  client.universal.scrape(...)")
    try:
        html = client.universal.scrape(
            url="https://www.example.com",
            js_render=True,
            country="us",
        )
        html_str = html if isinstance(html, str) else str(html)
        print(f"  ✓ Scraped {len(html_str)} bytes")
    except Exception as e:
        print(f"  ✗ Error: {e}")

    # Web Scraper Namespace
    print("\n[Web Scraper Namespace]")
    print("  client.scraper.create_task(...)")
    print("  client.scraper.get_status(...)")
    print("  client.scraper.get_result(...)")
    try:
        task_id = client.scraper.create_task(
            file_name="demo_task",
            spider_id="amazon_product_by-url",
            spider_name="amazon.com",
            parameters={"url": "https://www.amazon.com/dp/B0BZYCJK89"},
        )
        print(f"  ✓ Task created: {task_id}")
    except Exception as e:
        print(f"  ✗ Error: {e}")

    # Account Namespace
    print("\n[Account Namespace]")
    print("  client.account.get_balance()")
    print("  client.account.get_usage_statistics(...)")
    try:
        balance = client.account.get_balance()
        print(f"  ✓ Balance retrieved: {balance}")
    except Exception as e:
        print(f"  ✗ Error: {e}")

    # Proxy Namespace
    print("\n[Proxy Namespace]")
    print("  client.proxy.list_users(...)")
    print("  client.proxy.create_user(...)")
    print("  client.proxy.add_whitelist_ip(...)")
    try:
        users = client.proxy.list_users()
        print(f"  ✓ Users listed: {len(users.get('users', []))} users")
    except Exception as e:
        print(f"  ✗ Error: {e}")

    # Existing namespaces still work
    print("\n[Existing Namespaces]")
    print("  client.serp.google.search(...)")
    print("  client.serp.bing.search(...)")
    print("  client.unlimited.list_servers()")


def demo_response_wrapper(client: ThordataClient) -> None:
    """Demonstrate the unified response wrapper."""
    print_section("3. Using Response Wrapper (Unified Interface)")

    # Note: This is a low-level example. In practice, client methods
    # handle this internally, but you can use it for custom requests.

    print("\nResponse wrapper provides:")
    print("  - Consistent interface across all APIs")
    print("  - Automatic field extraction (code, message, request_id)")
    print("  - Success/error checking")
    print("  - Type safety with generics")

    # Example: Using response wrapper with internal HTTP client
    # (In real usage, client methods handle this automatically)
    try:
        # This is just for demonstration
        # In practice, use: client.account.get_balance()
        response = client._http.request(
            "GET",
            client._usage_stats_url,
            params={
                "token": client.public_token,
                "key": client.public_key,
            },
        )
        api_response = APIResponse.from_requests_response(response)

        if api_response.is_success:
            print("\n  ✓ Request successful")
            print(f"    Status Code: {api_response.status_code}")
            print(f"    Request ID: {api_response.request_id}")
            if api_response.data:
                print(
                    f"    Data keys: {list(api_response.data.keys()) if isinstance(api_response.data, dict) else 'N/A'}"
                )
        else:
            print("\n  ✗ Request failed")
            print(f"    Error: {api_response.message}")
            print(f"    Code: {api_response.code}")
    except Exception as e:
        print(f"  ✗ Error: {e}")


def demo_enhanced_errors(client: ThordataClient) -> None:
    """Demonstrate enhanced error messages."""
    print_section("4. Enhanced Error Messages (Better Debugging)")

    print("\nEnhanced errors now include:")
    print("  - HTTP status code")
    print("  - API error code")
    print("  - Request ID (if available)")
    print("  - URL that was requested")
    print("  - HTTP method used")

    # Try an operation that might fail to show error details
    try:
        # This might fail if credentials are invalid
        client.account.get_usage_statistics()
    except Exception as e:
        print("\n  Error example:")
        print(f"    Type: {type(e).__name__}")
        print(f"    Message: {e}")
        if hasattr(e, "status_code"):
            print(f"    Status Code: {e.status_code}")
        if hasattr(e, "request_id"):
            print(f"    Request ID: {e.request_id}")
        if hasattr(e, "url"):
            print(f"    URL: {e.url}")


def demo_comparison() -> None:
    """Show before/after comparison."""
    print_section("5. Before vs After Comparison")

    print("\n[BEFORE]")
    print("  # Hard-coded strings")
    print('  url = "https://scraperapi.thordata.com/request"')
    print("  # Scattered methods")
    print("  html = client.universal_scrape(url)")
    print("  task_id = client.create_scraper_task(...)")
    print("  balance = client.get_traffic_balance()")

    print("\n[AFTER]")
    print("  # Type-safe constants")
    print("  from thordata import APIBaseURL, APIEndpoint")
    print('  url = f"{APIBaseURL.SCRAPER_API}{APIEndpoint.SERP_REQUEST}"')
    print("  # Organized namespaces")
    print("  html = client.universal.scrape(url)")
    print("  task_id = client.scraper.create_task(...)")
    print("  balance = client.account.get_balance()")

    print("\n[Benefits]")
    print("  ✓ IDE autocomplete prevents typos")
    print("  ✓ Better code organization")
    print("  ✓ Easier to discover functionality")
    print("  ✓ Consistent API design")


def main() -> int:
    """Main function."""
    # Load .env
    repo_root = Path(__file__).parent.parent
    load_env_file(str(repo_root / ".env"))

    print("=" * 80)
    print("Thordata SDK - Namespace API Demo")
    print("=" * 80)
    print("\nThis demo showcases the improved SDK design:")
    print("  - Constants for type safety")
    print("  - Namespace-based organization")
    print("  - Unified response handling")
    print("  - Enhanced error messages")

    # Check credentials
    scraper_token = os.getenv(EnvVar.SCRAPER_TOKEN)
    public_token = os.getenv(EnvVar.PUBLIC_TOKEN)
    public_key = os.getenv(EnvVar.PUBLIC_KEY)

    if not scraper_token:
        print("\n[ERROR] THORDATA_SCRAPER_TOKEN is required")
        print("  Run: python examples/validate_env.py")
        return 1

    # Initialize client
    client = ThordataClient(
        scraper_token=scraper_token,
        public_token=public_token,
        public_key=public_key,
        api_timeout=60,
    )

    try:
        # Run demos
        demo_constants()
        demo_namespaces(client)
        demo_response_wrapper(client)
        demo_enhanced_errors(client)
        demo_comparison()

        print_section("Demo Complete")
        print("\nFor more examples, see:")
        print("  - examples/quick_start.py")
        print("  - examples/demo_serp_api.py")
        print("  - examples/demo_universal.py")
        print("  - examples/demo_web_scraper_api.py")

        return 0
    except KeyboardInterrupt:
        print("\n\n[Demo interrupted by user]")
        return 1
    except Exception as e:
        print(f"\n[ERROR] Demo failed: {e}")
        import traceback

        traceback.print_exc()
        return 1
    finally:
        client.close()


if __name__ == "__main__":
    raise SystemExit(main())
