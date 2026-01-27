#!/usr/bin/env python
"""Quick validation test - tests a subset of critical tools.

This script runs a minimal set of representative tools to quickly validate
the SDK is working correctly. Use this for fast feedback during development.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from scripts.acceptance.common import (
    AcceptanceConfig,
    ensure_output_dir,
    exit_with_result,
    is_integration_enabled,
    now_ts,
    print_header,
    require_env,
    safe_call,
    safe_call_with_timeout,
    write_json,
)
from thordata import CommonSettings, ThordataClient
from thordata.tools import Amazon, GoogleMaps, YouTube
from thordata.types import ScraperTaskConfig

_SUCCESS_STATUSES = {"ready", "success", "finished"}


def _run_quick_test(
    client: ThordataClient, name: str, tool, cfg: AcceptanceConfig
) -> dict:
    """Run a quick test with timeout protection."""
    spider_id = tool.get_spider_id()
    spider_name = tool.get_spider_name()
    file_name = f"quick_{name}_{now_ts()}"

    # Check if it's a video tool
    if hasattr(tool, "common_settings"):
        from thordata.types import VideoTaskConfig

        config = VideoTaskConfig(
            file_name=file_name,
            spider_id=spider_id,
            spider_name=spider_name,
            parameters=tool.to_task_parameters(),
            common_settings=tool.common_settings,
        )
        ok, task_or_err = safe_call(client.create_video_task_advanced, config)
    else:
        config = ScraperTaskConfig(
            file_name=file_name,
            spider_id=spider_id,
            spider_name=spider_name,
            parameters=tool.to_task_parameters(),
            include_errors=True,
        )
        ok, task_or_err = safe_call(client.create_scraper_task_advanced, config)

    if not ok:
        return {"name": name, "ok": False, "stage": "create", "error": str(task_or_err)}

    task_id = str(task_or_err)
    print(f"  Created task: {task_id}")

    # Wait with hard timeout
    ok, status_or_err = safe_call_with_timeout(
        client.wait_for_task,
        task_id,
        poll_interval=2.0,
        max_wait=120.0,
        hard_timeout=150.0,
    )

    if not ok:
        return {
            "name": name,
            "ok": False,
            "task_id": task_id,
            "stage": "wait",
            "error": str(status_or_err),
        }

    status = str(status_or_err).strip().lower()
    ok_dl, dl_or_err = safe_call(client.get_task_result, task_id)
    download_url = dl_or_err if ok_dl else None

    ok_final = status in _SUCCESS_STATUSES
    return {
        "name": name,
        "ok": ok_final,
        "task_id": task_id,
        "status": status,
        "download_url": download_url,
        "error": None if ok_final else f"Status: {status}",
    }


def main() -> bool:
    print_header("QUICK VALIDATION TEST")

    if not is_integration_enabled():
        print("THORDATA_INTEGRATION not set, skipping.")
        return True

    out = ensure_output_dir("quick_validation")

    scraper_token = require_env("THORDATA_SCRAPER_TOKEN")
    public_token = require_env("THORDATA_PUBLIC_TOKEN")
    public_key = require_env("THORDATA_PUBLIC_KEY")

    client = ThordataClient(
        scraper_token=scraper_token,
        public_token=public_token,
        public_key=public_key,
        api_timeout=60,
    )

    cfg = AcceptanceConfig(timeout=60, poll_interval=2.0, max_wait=120.0)

    # Minimal critical test cases
    test_cases = [
        ("amazon_product", Amazon.ProductByAsin(asin="B0BZYCJK89"), "text"),
        (
            "google_maps_placeid",
            GoogleMaps.DetailsByPlaceId(place_id="ChIJPTacEpBQwokRKwIlDXelxkA"),
            "text",
        ),
    ]

    # Add one video test if we have time
    video_id = "jNQXAC9IVRw"
    settings = CommonSettings(
        resolution="<=360p",
        video_codec="vp9",
        audio_format="opus",
        bitrate="<=320",
        selected_only=False,
    )
    test_cases.append(
        (
            "youtube_video_info",
            YouTube.VideoInfo(video_id=video_id, common_settings=settings),
            "video",
        )
    )

    results = []
    all_ok = True

    print(f"\nRunning {len(test_cases)} quick validation tests...\n")

    for name, tool, _tool_type in test_cases:
        print(f"Testing: {name} ({tool.get_spider_id()})")
        r = _run_quick_test(client, name, tool, cfg)
        results.append(r)
        if r.get("ok"):
            print(f"  [OK] task_id={r.get('task_id')} status={r.get('status')}")
        else:
            all_ok = False
            print(f"  [FAIL] {r.get('stage')}: {r.get('error')}")

    write_json(out / "quick_validation_results.json", results)
    client.close()

    print("\n--- Quick Validation Summary ---")
    if all_ok:
        print("[SUCCESS] All quick tests passed!")
    else:
        print("[FAILURE] Some tests failed. See artifacts for details.")

    return all_ok


if __name__ == "__main__":
    exit_with_result(main())
