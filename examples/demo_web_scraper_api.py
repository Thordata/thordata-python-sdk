"""
Thordata Web Scraper API (Tasks) Demo - Complete Workflow Acceptance
--------------------------------------------------------------------

Goal: Demonstrate the complete workflow from task creation to result retrieval:
1. Create Web Scraper task
2. Poll task status
3. Wait for task completion
4. Download task results

This demo uses a **real Web Scraper tool** via `run_tool`, which matches
the typical usage pattern in the Web Scraper Store UI.
"""

from __future__ import annotations

import os
import time

from thordata import ThordataClient, ThordataError, load_env_file
from thordata.tools import Amazon


def main() -> int:
    # Best-effort .env load from repo root
    repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    load_env_file(os.path.join(repo_root, ".env"))

    s_token = os.getenv("THORDATA_SCRAPER_TOKEN")
    p_token = os.getenv("THORDATA_PUBLIC_TOKEN")
    p_key = os.getenv("THORDATA_PUBLIC_KEY")
    s_base = os.getenv("THORDATA_SCRAPERAPI_BASE_URL")
    w_base = os.getenv("THORDATA_WEB_SCRAPER_API_BASE_URL")

    if not all([s_token, p_token, p_key]):
        print("[FAIL] Missing required environment variables:")
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

    # Allow overriding the demo ASIN from env; fall back to a sample value.
    asin = os.getenv("THORDATA_DEMO_AMAZON_ASIN", "B0BZYCJK89")

    print("=" * 80)
    print("Thordata Web Scraper API - Complete Workflow Acceptance")
    print("=" * 80)
    print("\n[TOOL] Using tool: Amazon.ProductByAsin")
    print(f"   ASIN: {asin}")

    # ========== Step 1: Create Task ==========
    print("\n[Step 1/4] Creating Web Scraper task...")
    try:
        task_id = client.run_tool(Amazon.ProductByAsin(asin=asin))
        print("[OK] Task created successfully!")
        print(f"   Task ID: {task_id}")
    except ThordataError as e:
        print(f"[FAIL] Task creation failed: {e}")
        if hasattr(e, "payload"):
            print(f"   Error details: {e.payload}")
        return 2
    except Exception as e:
        print(f"[FAIL] Unexpected error: {e}")
        import traceback

        traceback.print_exc()
        return 2

    # ========== Step 2: Check Initial Status ==========
    print("\n[Step 2/4] Checking task status...")
    try:
        initial_status = client.get_task_status(task_id)
        print(f"   Initial status: {initial_status}")
    except ThordataError as e:
        print(f"[WARN] Failed to get status: {e}")
        initial_status = "unknown"

    # ========== Step 3: Wait for Task Completion ==========
    print("\n[Step 3/4] Waiting for task completion (max 5 minutes)...")
    print("   Poll interval: 3 seconds")

    max_wait = 300  # 5 minutes
    poll_interval = 3.0
    start_time = time.time()

    try:
        final_status = client.wait_for_task(
            task_id,
            poll_interval=poll_interval,
            max_wait=max_wait,
        )
        elapsed = time.time() - start_time
        print("[OK] Task completed!")
        print(f"   Final status: {final_status}")
        print(f"   Elapsed time: {elapsed:.1f} seconds")
    except ThordataError as e:
        print(f"[FAIL] Failed to wait for task: {e}")
        # Try to get current status
        try:
            final_status = client.get_task_status(task_id)
            print(f"   Current status: {final_status}")
        except Exception:
            final_status = "unknown"
        return 3
    except TimeoutError:
        print(f"[TIMEOUT] Wait timeout ({max_wait} seconds)")
        try:
            final_status = client.get_task_status(task_id)
            print(f"   Current status: {final_status}")
        except Exception:
            final_status = "unknown"
        return 3

    # ========== Step 4: Get Results ==========
    print("\n[Step 4/4] Getting task results...")

    success_statuses = {"ready", "success", "finished"}
    if final_status.lower() in success_statuses:
        try:
            result_url = client.get_task_result(task_id)
            print("[OK] Results retrieved successfully!")
            print(f"   Download URL: {result_url}")
            print("\n[TIP] You can download results using:")
            print(f"   curl -O '{result_url}'")
            print(f"   Or open in browser: {result_url}")
        except ThordataError as e:
            print(f"[FAIL] Failed to get results: {e}")
            if hasattr(e, "payload"):
                print(f"   Error details: {e.payload}")
            return 4
    else:
        print(f"[WARN] Task status is '{final_status}', not a success status")
        print(f"   Success statuses should be: {', '.join(success_statuses)}")
        print("   Cannot retrieve result URL")
        return 4

    print("\n" + "=" * 80)
    print("[OK] Complete workflow acceptance finished!")
    print("=" * 80)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
