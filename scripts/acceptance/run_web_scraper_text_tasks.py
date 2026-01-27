#!/usr/bin/env python
"""Web Scraper API acceptance - TEXT tasks (read-only).

Runs representative *text* tasks through the full lifecycle:
- create_scraper_task_advanced (builder)
- wait_for_task
- get_task_result (download url)

Strict pass criteria:
- Each task must end in a success-like status (Ready/Success/Finished)
- Any Failed/Error/Cancelled status is treated as a failure.

Google Maps (must-pass) strategy:
- Cover 4 scraping methods that exist in Dashboard:
  - by-url / by-cid / by-location / by-placeid
- Prefer more stable methods first (place_id/cid), then fall back to url/location.
- Higher max_wait for Maps
- Retry and never hang: hard timeout around wait_for_task
- Always capture diagnostics: task_id/status/download_url

IMPORTANT:
- We set include_errors=True when creating tasks.
"""

from __future__ import annotations

import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from thordata import ThordataClient
from thordata.tools import Amazon, GoogleMaps
from thordata.types import ScraperTaskConfig

from .common import (
    AcceptanceConfig,
    ensure_output_dir,
    exit_with_result,
    is_integration_enabled,
    now_ts,
    require_env,
    safe_call,
    safe_call_with_timeout,
    write_json,
)

_SUCCESS_STATUSES = {"ready", "success", "finished"}
_FAILURE_STATUSES = {"failed", "error", "cancelled"}


def _create_task_with_include_errors(
    client: ThordataClient,
    *,
    name: str,
    tool,
) -> tuple[bool, str | Exception]:
    file_name = f"accept_text_{name}_{now_ts()}"

    config = ScraperTaskConfig(
        file_name=file_name,
        spider_id=tool.get_spider_id(),
        spider_name=tool.get_spider_name(),
        parameters=tool.to_task_parameters(),
        include_errors=True,
    )
    return safe_call(client.create_scraper_task_advanced, config)


def _wait_and_collect(
    client: ThordataClient,
    *,
    name: str,
    task_id: str,
    spider_id: str,
    spider_name: str,
    cfg: AcceptanceConfig,
) -> dict:
    ok_wait, status_or_err = safe_call_with_timeout(
        client.wait_for_task,
        task_id,
        poll_interval=cfg.poll_interval,
        max_wait=cfg.max_wait,
        hard_timeout=float(cfg.max_wait) + 30.0,
    )

    ok_status, status_now = safe_call(client.safe_get_task_status, task_id)
    status_now_val = status_now if ok_status else "unknown"

    ok_dl, dl_or_err = safe_call(client.get_task_result, task_id)
    download_url = dl_or_err if ok_dl else None

    if not ok_wait:
        return {
            "name": name,
            "ok": False,
            "task_id": task_id,
            "status": status_now_val,
            "stage": "wait",
            "error": f"wait_for_task_timeout_or_error: {status_or_err}",
            "download_url": download_url,
            "spider_id": spider_id,
            "spider_name": spider_name,
        }

    status = str(status_or_err)
    status_lower = status.strip().lower()

    if status_lower in _FAILURE_STATUSES:
        return {
            "name": name,
            "ok": False,
            "task_id": task_id,
            "status": status,
            "stage": "status",
            "error": f"Task ended with failure status: {status}",
            "download_url": download_url,
            "spider_id": spider_id,
            "spider_name": spider_name,
        }

    ok_final = status_lower in _SUCCESS_STATUSES
    return {
        "name": name,
        "ok": ok_final,
        "task_id": task_id,
        "status": status,
        "download_url": download_url,
        "spider_id": spider_id,
        "spider_name": spider_name,
        "error": None if ok_final else f"Unexpected non-success status: {status}",
    }


def _run_tool_case(
    client: ThordataClient, *, name: str, tool, cfg: AcceptanceConfig
) -> dict:
    spider_id = tool.get_spider_id()
    spider_name = tool.get_spider_name()

    ok, task_or_err = _create_task_with_include_errors(client, name=name, tool=tool)
    if not ok:
        return {
            "name": name,
            "ok": False,
            "stage": "create",
            "error": str(task_or_err),
            "spider_id": spider_id,
            "spider_name": spider_name,
        }

    task_id = str(task_or_err)
    return _wait_and_collect(
        client,
        name=name,
        task_id=task_id,
        spider_id=spider_id,
        spider_name=spider_name,
        cfg=cfg,
    )


def _run_maps_group(client: ThordataClient) -> dict:
    cfg = AcceptanceConfig(timeout=120, poll_interval=3.0, max_wait=900.0)

    # Dashboard sample values (from your curl/examples)
    # Prefer place_id/cid since they are usually more stable than parsing a full URL.
    cases = [
        (
            "maps_by_placeid",
            GoogleMaps.DetailsByPlaceId(place_id="ChIJPTacEpBQwokRKwIlDXelxkA"),
        ),
        (
            "maps_by_cid",
            GoogleMaps.DetailsByCid(CID="2476046430038551731"),
        ),
        (
            "maps_by_url",
            GoogleMaps.DetailsByUrl(
                url="https://www.google.com/maps/place/Pizza%2BInn%2BMagdeburg/data=!4m7!3m6!1s0x47a5f50c083530a3:0xfdba8746b538141!8m2!3d52.1263086!4d11.6094743!16s%2Fg%2F11kqmtk3dt!19sChIJozA1CAz1pUcRQYFTa3So2w8?authuser=0&hl=en&rclk=1"
            ),
        ),
        (
            "maps_by_location",
            GoogleMaps.DetailsByLocation(country="us", keyword="pizza"),
        ),
    ]

    attempts: list[dict] = []

    for name, tool in cases:
        for retry_idx in range(2):
            r = _run_tool_case(client, name=name, tool=tool, cfg=cfg)
            r["retry_index"] = retry_idx
            attempts.append(r)
            if r.get("ok"):
                return {"ok": True, "attempts": attempts, "final": r}
            time.sleep(5 + retry_idx * 10)

    return {"ok": False, "attempts": attempts}


def main() -> bool:
    print("=" * 80)
    print("WEB SCRAPER API - TEXT TASKS (READ-ONLY)")
    print("=" * 80)

    if not is_integration_enabled():
        print("THORDATA_INTEGRATION not set, skipping.")
        return True

    out = ensure_output_dir("web_scraper_text")

    scraper_token = require_env("THORDATA_SCRAPER_TOKEN")
    public_token = require_env("THORDATA_PUBLIC_TOKEN")
    public_key = require_env("THORDATA_PUBLIC_KEY")

    client = ThordataClient(
        scraper_token=scraper_token,
        public_token=public_token,
        public_key=public_key,
        api_timeout=90,
    )

    results: list[dict] = []
    all_ok = True

    # Stable Amazon tasks
    for name, tool in [
        ("amazon_search", Amazon.Search(keyword="laptop", domain="amazon.com")),
        ("amazon_product", Amazon.Product(asin="B000000000", domain="amazon.com")),
    ]:
        print(f"\nRunning text task: {name} ({tool.get_spider_id()})")
        r = _run_tool_case(
            client, name=name, tool=tool, cfg=AcceptanceConfig(timeout=90, max_wait=600)
        )
        results.append(r)
        if not r.get("ok"):
            all_ok = False
            print(
                f"  [FAIL] {r.get('stage')}: {r.get('error')} (status={r.get('status')})"
            )
        else:
            print(f"  [OK] task_id={r.get('task_id')} status={r.get('status')}")

    print("\nRunning maps group (4 scraping methods, retries + hard timeout)")
    maps_group = _run_maps_group(client)
    results.append({"name": "google_maps_details", "group": maps_group})
    if not maps_group.get("ok"):
        all_ok = False
        print("  [FAIL] google_maps_details failed for all methods. See artifacts.")
    else:
        final = maps_group.get("final", {})
        print(
            f"  [OK] maps final task_id={final.get('task_id')} status={final.get('status')}"
        )

    write_json(out / "web_scraper_text_results.json", results)
    client.close()

    print("\n--- Web Scraper Text Summary ---")
    if all_ok:
        print("✅ Text tasks passed.")
    else:
        print("❌ Text tasks failed (strict). See artifacts for details.")

    return all_ok


if __name__ == "__main__":
    exit_with_result(main())
