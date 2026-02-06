#!/usr/bin/env python
"""Web Scraper API acceptance - VIDEO tasks (read-only).

Runs 3 representative *video* tasks through the full lifecycle:
- create_video_task (video_builder)
- wait_for_task
- get_task_result (download url)

Strict pass criteria:
- Each task must end in a success-like status (Ready/Success/Finished)
- Any Failed/Error/Cancelled status is treated as a failure.

Notes:
- Aligns with examples/full_acceptance_test.py: use a stable sample video and
  explicit CommonSettings for better success rate.
- When a task fails, we still try to fetch task result URL (if any) to aid
  debugging.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from thordata import CommonSettings, ThordataClient
from thordata.tools import YouTube

from .common import (
    AcceptanceConfig,
    ensure_output_dir,
    exit_with_result,
    is_integration_enabled,
    now_ts,
    print_header,
    require_env,
    safe_call,
    write_json,
)

_SUCCESS_STATUSES = {"ready", "success", "finished"}
_FAILURE_STATUSES = {"failed", "error", "cancelled"}


def _run_one(client: ThordataClient, *, name: str, tool, cfg: AcceptanceConfig) -> dict:
    params = tool.to_task_parameters()
    spider_id = tool.get_spider_id()
    spider_name = tool.get_spider_name()

    file_name = f"accept_video_{name}_{now_ts()}"

    ok, task_or_err = safe_call(
        client.create_video_task,
        file_name,
        spider_id,
        spider_name,
        params,
        tool.common_settings,
    )
    if not ok:
        return {"name": name, "ok": False, "stage": "create", "error": str(task_or_err)}

    task_id = task_or_err

    ok, status_or_err = safe_call(
        client.wait_for_task,
        task_id,
        poll_interval=cfg.poll_interval,
        max_wait=cfg.max_wait,
    )
    if not ok:
        return {
            "name": name,
            "ok": False,
            "task_id": task_id,
            "stage": "wait",
            "error": str(status_or_err),
        }

    status = str(status_or_err)
    status_lower = status.strip().lower()

    # Try to fetch result URL even on failure (may contain error payload link)
    ok_dl, dl_or_err = safe_call(client.get_task_result, task_id)
    download_url = dl_or_err if ok_dl else None

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


def main() -> bool:
    print_header("WEB SCRAPER API - VIDEO TASKS (READ-ONLY)")

    if not is_integration_enabled():
        print("THORDATA_INTEGRATION not set, skipping.")
        return True

    out = ensure_output_dir("web_scraper_video")
    cfg = AcceptanceConfig(timeout=120, max_wait=900)

    scraper_token = require_env("THORDATA_SCRAPER_TOKEN")
    public_token = require_env("THORDATA_PUBLIC_TOKEN")
    public_key = require_env("THORDATA_PUBLIC_KEY")

    client = ThordataClient(
        scraper_token=scraper_token,
        public_token=public_token,
        public_key=public_key,
        api_timeout=cfg.timeout,
    )

    # Align with examples/full_acceptance_test.py
    # Use a stable public sample video URL.
    video_url = "https://www.youtube.com/watch?v=jNQXAC9IVRw"
    video_id = "jNQXAC9IVRw"

    # Explicit settings improve determinism and match historical passing config.
    settings = CommonSettings(
        resolution="<=360p",
        video_codec="vp9",
        audio_format="opus",
        bitrate="<=320",
        selected_only=False,
        is_subtitles=False,
    )

    cases = [
        (
            "youtube_video_download",
            YouTube.VideoDownload(url=video_url, common_settings=settings),
        ),
        (
            "youtube_audio_download",
            YouTube.AudioDownload(url=video_url, common_settings=settings),
        ),
        (
            "youtube_subtitle_download",
            YouTube.SubtitleDownload(video_id=video_id, common_settings=settings),
        ),
    ]

    results = []
    all_ok = True

    for name, tool in cases:
        print(f"\nRunning video task: {name} ({tool.get_spider_id()})")
        r = _run_one(client, name=name, tool=tool, cfg=cfg)
        results.append(r)
        if not r.get("ok"):
            all_ok = False
            print(
                f"  [FAIL] {r.get('stage')}: {r.get('error')} (status={r.get('status')})"
            )
        else:
            print(f"  [OK] task_id={r.get('task_id')} status={r.get('status')}")

    write_json(out / "web_scraper_video_results.json", results)
    client.close()

    print("\n--- Web Scraper Video Summary ---")
    if all_ok:
        print("Video tasks passed.")
    else:
        print("Video tasks failed (strict). See artifacts for details.")

    return all_ok


if __name__ == "__main__":
    exit_with_result(main())
