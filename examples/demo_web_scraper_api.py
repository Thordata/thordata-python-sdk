"""
Web Scraper API Demo - Task-Based Scraping (Live-demo friendly, CI friendly)

Demonstrates:
- Creating scraping tasks (from env template copied from dashboard)
- Checking task status
- Waiting for completion
- Retrieving result download URL
- Using ScraperTaskConfig (include_errors)

Environment variables:
- THORDATA_SCRAPER_TOKEN (required)
- THORDATA_PUBLIC_TOKEN (required for tasks)
- THORDATA_PUBLIC_KEY (required for tasks)

Task template env (copy from Dashboard -> Web Scraper Store -> API Builder):
- THORDATA_TASK_SPIDER_ID
- THORDATA_TASK_SPIDER_NAME
- THORDATA_TASK_FILE_NAME (optional)
- THORDATA_TASK_PARAMETERS_JSON (object or array of objects)

Usage:
    python examples/demo_web_scraper_api.py
"""

from __future__ import annotations

import os
import sys
from typing import Any

from thordata import ScraperTaskConfig, ThordataClient, ThordataError
from thordata._example_utils import (
    load_env,
    normalize_task_parameters,
    parse_json_env,
    skip_if_missing,
)


def _configure_stdio() -> None:
    # Avoid UnicodeEncodeError on Windows consoles with legacy encodings.
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")


def _create_task(client: ThordataClient) -> str | None:
    # Skip if task template env is not provided (keeps CI/offline stable).
    if skip_if_missing(
        [
            "THORDATA_TASK_SPIDER_ID",
            "THORDATA_TASK_SPIDER_NAME",
            "THORDATA_TASK_PARAMETERS_JSON",
        ],
        tip="Set task template env vars from dashboard (API Builder) to run task creation.",
    ):
        return None

    raw: Any = parse_json_env("THORDATA_TASK_PARAMETERS_JSON", default="{}")
    params = normalize_task_parameters(raw)

    config = ScraperTaskConfig(
        file_name=os.getenv("THORDATA_TASK_FILE_NAME") or "demo_task",
        spider_id=os.environ["THORDATA_TASK_SPIDER_ID"],
        spider_name=os.environ["THORDATA_TASK_SPIDER_NAME"],
        parameters=params,
        include_errors=True,
    )

    # Prefer advanced method if available (supports include_errors via config).
    if hasattr(client, "create_scraper_task_advanced"):
        return client.create_scraper_task_advanced(config)  # type: ignore[attr-defined]

    # Fallback: basic create_scraper_task may not accept include_errors in this SDK version.
    return client.create_scraper_task(
        file_name=config.file_name,
        spider_id=config.spider_id,
        spider_name=config.spider_name,
        parameters=config.parameters,
    )


def main() -> int:
    _configure_stdio()
    load_env()

    if skip_if_missing(["THORDATA_SCRAPER_TOKEN"]):
        return 0

    # Tasks require public token/key
    if skip_if_missing(
        ["THORDATA_PUBLIC_TOKEN", "THORDATA_PUBLIC_KEY"],
        tip="Tasks APIs require public token + public key.",
    ):
        return 0

    client = ThordataClient(
        scraper_token=os.environ["THORDATA_SCRAPER_TOKEN"],
        public_token=os.environ.get("THORDATA_PUBLIC_TOKEN"),
        public_key=os.environ.get("THORDATA_PUBLIC_KEY"),
    )

    print("=" * 50)
    print("Thordata SDK - Web Scraper API Demo")
    print("=" * 50)

    try:
        task_id = _create_task(client)
        if not task_id:
            print("Task creation skipped.")
            return 0

        print("Task created:", task_id)

        print("Waiting for completion...")
        status = client.wait_for_task(task_id, poll_interval=5.0, max_wait=120.0)
        print("Final status:", status)

        if str(status).lower() in ("ready", "success", "finished"):
            download_url = client.get_task_result(task_id, file_type="json")
            print("Download URL:", download_url)

    except ThordataError as e:
        print("Task demo failed:", e)
        return 1

    print("Demo complete.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
