"""
Thordata Web Scraper API - Multi-Spider ID Acceptance Test
----------------------------------------------------------

Goal: Test multiple spider IDs to ensure comprehensive coverage of Web Scraper API:
1. Test different tool categories (E-commerce, Social Media, Search, etc.)
2. Verify task creation, status polling, and result retrieval for each
3. Collect statistics on success rates and performance
4. Provide detailed reporting

This script tests multiple spider IDs across different categories to ensure
the SDK works correctly with various Web Scraper tools.
"""

from __future__ import annotations

import os
import time
from dataclasses import dataclass
from typing import Any

from thordata import ThordataClient, ThordataError, load_env_file
from thordata.tools import Amazon, GoogleMaps, YouTube


@dataclass
class TestCase:
    """Test case configuration for a spider ID."""

    name: str
    tool_class: Any
    tool_instance: Any
    max_wait: float = 300.0
    poll_interval: float = 3.0


@dataclass
class TestResult:
    """Result of a single test case."""

    name: str
    spider_id: str
    spider_name: str
    success: bool
    task_id: str | None = None
    final_status: str | None = None
    result_url: str | None = None
    elapsed_time: float | None = None
    error: str | None = None


def create_test_cases() -> list[TestCase]:
    """Create test cases for different spider IDs."""
    return [
        # E-commerce
        TestCase(
            name="Amazon_ProductByAsin",
            tool_class=Amazon.ProductByAsin,
            tool_instance=Amazon.ProductByAsin(asin="B0BZYCJK89"),
            max_wait=300.0,
        ),
        TestCase(
            name="Amazon_Search",
            tool_class=Amazon.Search,
            tool_instance=Amazon.Search(keyword="laptop", domain="amazon.com"),
            max_wait=300.0,
        ),
        # Search
        TestCase(
            name="GoogleMaps_DetailsByPlaceId",
            tool_class=GoogleMaps.DetailsByPlaceId,
            tool_instance=GoogleMaps.DetailsByPlaceId(
                place_id="ChIJPTacEpBQwokRKwIlDXelxkA"
            ),
            max_wait=600.0,  # Maps can take longer
        ),
        TestCase(
            name="GoogleMaps_DetailsByCid",
            tool_class=GoogleMaps.DetailsByCid,
            tool_instance=GoogleMaps.DetailsByCid(CID="2476046430038551731"),
            max_wait=600.0,
        ),
        # Video (lightweight test - just create, don't wait for completion)
        TestCase(
            name="YouTube_VideoInfo",
            tool_class=YouTube.VideoInfo,
            tool_instance=YouTube.VideoInfo(video_id="jNQXAC9IVRw"),
            max_wait=180.0,
        ),
    ]


def run_single_test(client: ThordataClient, test_case: TestCase) -> TestResult:
    """Run a single test case and return the result."""
    print(f"\n{'='*80}")
    print(f"Testing: {test_case.name}")
    print(f"{'='*80}")

    spider_id = test_case.tool_instance.get_spider_id()
    spider_name = test_case.tool_instance.get_spider_name()

    print(f"Spider ID: {spider_id}")
    print(f"Spider Name: {spider_name}")

    start_time = time.time()

    # Step 1: Create task
    print("\n[Step 1/3] Creating task...")
    try:
        task_id = client.run_tool(test_case.tool_instance)
        print(f"[OK] Task created: {task_id}")
    except ThordataError as e:
        error_msg = f"Task creation failed: {e}"
        print(f"[FAIL] {error_msg}")
        if hasattr(e, "payload"):
            print(f"   Error details: {e.payload}")
        return TestResult(
            name=test_case.name,
            spider_id=spider_id,
            spider_name=spider_name,
            success=False,
            error=error_msg,
        )
    except Exception as e:
        error_msg = f"Unexpected error: {e}"
        print(f"❌ {error_msg}")
        import traceback

        traceback.print_exc()
        return TestResult(
            name=test_case.name,
            spider_id=spider_id,
            spider_name=spider_name,
            success=False,
            error=error_msg,
        )

    # Step 2: Wait for completion
    print(f"\n[Step 2/3] Waiting for task completion (max {test_case.max_wait}s)...")
    try:
        final_status = client.wait_for_task(
            task_id,
            poll_interval=test_case.poll_interval,
            max_wait=test_case.max_wait,
        )
        elapsed = time.time() - start_time
        print(f"[OK] Task completed in {elapsed:.1f}s")
        print(f"   Final status: {final_status}")
    except ThordataError as e:
        error_msg = f"Wait failed: {e}"
        print(f"[FAIL] {error_msg}")
        try:
            final_status = client.get_task_status(task_id)
            print(f"   Current status: {final_status}")
        except Exception:
            final_status = "unknown"
        elapsed = time.time() - start_time
        return TestResult(
            name=test_case.name,
            spider_id=spider_id,
            spider_name=spider_name,
            success=False,
            task_id=task_id,
            final_status=final_status,
            elapsed_time=elapsed,
            error=error_msg,
        )
    except TimeoutError:
        error_msg = f"Timeout after {test_case.max_wait}s"
        print(f"[TIMEOUT] {error_msg}")
        try:
            final_status = client.get_task_status(task_id)
            print(f"   Current status: {final_status}")
        except Exception:
            final_status = "unknown"
        elapsed = time.time() - start_time
        return TestResult(
            name=test_case.name,
            spider_id=spider_id,
            spider_name=spider_name,
            success=False,
            task_id=task_id,
            final_status=final_status,
            elapsed_time=elapsed,
            error=error_msg,
        )

    elapsed = time.time() - start_time

    # Step 3: Get results
    print("\n[Step 3/3] Getting task results...")
    success_statuses = {"ready", "success", "finished"}
    if final_status.lower() in success_statuses:
        try:
            result_url = client.get_task_result(task_id)
            print("[OK] Results retrieved successfully!")
            print(f"   Download URL: {result_url[:80]}...")
            return TestResult(
                name=test_case.name,
                spider_id=spider_id,
                spider_name=spider_name,
                success=True,
                task_id=task_id,
                final_status=final_status,
                result_url=result_url,
                elapsed_time=elapsed,
            )
        except ThordataError as e:
            error_msg = f"Failed to get results: {e}"
            print(f"[FAIL] {error_msg}")
            return TestResult(
                name=test_case.name,
                spider_id=spider_id,
                spider_name=spider_name,
                success=False,
                task_id=task_id,
                final_status=final_status,
                elapsed_time=elapsed,
                error=error_msg,
            )
    else:
        error_msg = f"Task ended with non-success status: {final_status}"
        print(f"[WARN] {error_msg}")
        return TestResult(
            name=test_case.name,
            spider_id=spider_id,
            spider_name=spider_name,
            success=False,
            task_id=task_id,
            final_status=final_status,
            elapsed_time=elapsed,
            error=error_msg,
        )


def main() -> int:
    # Load .env
    repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    load_env_file(os.path.join(repo_root, ".env"))

    s_token = os.getenv("THORDATA_SCRAPER_TOKEN")
    p_token = os.getenv("THORDATA_PUBLIC_TOKEN")
    p_key = os.getenv("THORDATA_PUBLIC_KEY")
    s_base = os.getenv("THORDATA_SCRAPERAPI_BASE_URL")
    w_base = os.getenv("THORDATA_WEB_SCRAPER_API_BASE_URL")

    if not all([s_token, p_token, p_key]):
        print("❌ Missing required environment variables:")
        print("   - THORDATA_SCRAPER_TOKEN")
        print("   - THORDATA_PUBLIC_TOKEN")
        print("   - THORDATA_PUBLIC_KEY")
        return 1

    client = ThordataClient(
        scraper_token=s_token,
        public_token=p_token,
        public_key=p_key,
        scraperapi_base_url=s_base,
        web_scraper_api_base_url=w_base,
        api_timeout=90,
    )

    print("=" * 80)
    print("Thordata Web Scraper API - Multi-Spider ID Acceptance Test")
    print("=" * 80)

    test_cases = create_test_cases()
    print(f"\n[INFO] Total test cases: {len(test_cases)}")
    for i, tc in enumerate(test_cases, 1):
        print(f"   {i}. {tc.name} ({tc.tool_instance.get_spider_id()})")

    results: list[TestResult] = []

    for i, test_case in enumerate(test_cases, 1):
        print(f"\n\n{'#'*80}")
        print(f"Test {i}/{len(test_cases)}: {test_case.name}")
        print(f"{'#'*80}")
        result = run_single_test(client, test_case)
        results.append(result)
        time.sleep(2)  # Brief pause between tests

    # Summary
    print("\n\n" + "=" * 80)
    print("Test Summary")
    print("=" * 80)

    total = len(results)
    successful = sum(1 for r in results if r.success)
    failed = total - successful

    print(f"\nTotal tests: {total}")
    print(f"[OK] Successful: {successful}")
    print(f"[FAIL] Failed: {failed}")
    print(f"Success rate: {successful/total*100:.1f}%")

    if successful > 0:
        avg_time = sum(r.elapsed_time or 0 for r in results if r.success) / successful
        print(f"\nAverage completion time (successful): {avg_time:.1f}s")

    print("\nDetailed Results:")
    print("-" * 80)
    for result in results:
        status_icon = "[OK]" if result.success else "[FAIL]"
        print(f"{status_icon} {result.name}")
        print(f"   Spider ID: {result.spider_id}")
        print(f"   Task ID: {result.task_id or 'N/A'}")
        print(f"   Status: {result.final_status or 'N/A'}")
        if result.elapsed_time:
            print(f"   Elapsed: {result.elapsed_time:.1f}s")
        if result.error:
            print(f"   Error: {result.error}")
        if result.result_url:
            print(f"   Result URL: {result.result_url[:60]}...")
        print()

    # Return non-zero if any test failed
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
