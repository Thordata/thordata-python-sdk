"""
Web Scraper API Demo - Task-Based Scraping (Offline-test friendly)

Demonstrates:
- Creating async scraping tasks
- Checking task status
- Waiting for completion
- Retrieving result download URL
- Using ScraperTaskConfig

Environment variables:
- THORDATA_SCRAPER_TOKEN (required)
- THORDATA_PUBLIC_TOKEN (required)
- THORDATA_PUBLIC_KEY (required)

Usage:
    python examples/demo_web_scraper_api.py
"""

from __future__ import annotations

import json
import logging
import os
import sys
from typing import Optional

try:
    from dotenv import load_dotenv
except ImportError:
    load_dotenv = None

from thordata import ScraperTaskConfig, ThordataClient, ThordataError

logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")


def _configure_stdio() -> None:
    # Avoid UnicodeEncodeError on Windows consoles with legacy encodings.
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")


def _load_env() -> None:
    if load_dotenv is None:
        return
    from pathlib import Path

    repo_root = Path(__file__).resolve().parents[1]
    load_dotenv(dotenv_path=repo_root / ".env")


def demo_create_task(client: ThordataClient) -> Optional[str]:
    print("\n" + "=" * 50)
    print("1) Create Scraper Task")
    print("=" * 50)

    print("Creating task for YouTube scraping...")
    print("(Example only - adjust spider_id/spider_name for your use case.)")

    try:
        spider_id = os.getenv("THORDATA_TASK_SPIDER_ID")
        spider_name = os.getenv("THORDATA_TASK_SPIDER_NAME")
        file_name = os.getenv("THORDATA_TASK_FILE_NAME") or "demo_task"
        parameters_json = os.getenv("THORDATA_TASK_PARAMETERS_JSON") or "{}"

        if not spider_id or not spider_name:
            print(
                "Skipping task creation: set THORDATA_TASK_SPIDER_ID and THORDATA_TASK_SPIDER_NAME in .env"
            )
            return None

        try:
            raw = json.loads(parameters_json)
            if isinstance(raw, list):
                raw = raw[0] if raw else {}
            if not isinstance(raw, dict):
                raise ValueError("parameters must be object or array of objects")
            parameters = raw
        except Exception:
            print(
                "THORDATA_TASK_PARAMETERS_JSON must be valid JSON (object or array of objects)"
            )
            return None

        task_id = client.create_scraper_task(
            file_name=file_name,
            spider_id=spider_id,
            spider_name=spider_name,
            parameters=parameters,
        )

        print("Task created.")
        print(f"Task ID: {task_id}")
        return task_id

    except ThordataError as e:
        print(f"Task creation failed: {e}")
        return None


def demo_poll_status(client: ThordataClient, task_id: str) -> Optional[str]:
    print("\n" + "=" * 50)
    print("2) Check Task Status")
    print("=" * 50)

    print(f"Checking status for: {task_id}")

    try:
        status = client.get_task_status(task_id)
        print(f"Current status: {status}")
        return status
    except ThordataError as e:
        print(f"Status check failed: {e}")
        return None


def demo_wait_for_completion(client: ThordataClient, task_id: str) -> bool:
    print("\n" + "=" * 50)
    print("3) Wait for Completion")
    print("=" * 50)

    print(f"Waiting for task {task_id}...")

    try:
        status = client.wait_for_task(
            task_id,
            poll_interval=5.0,
            max_wait=60.0,
        )

        if status.lower() in ("ready", "success", "finished"):
            print(f"Task completed: {status}")
            return True

        print(f"Task ended with status: {status}")
        return False

    except TimeoutError:
        print("Task did not complete within the time limit.")
        return False
    except ThordataError as e:
        print(f"Error while waiting: {e}")
        return False


def demo_get_result(client: ThordataClient, task_id: str) -> None:
    print("\n" + "=" * 50)
    print("4) Get Result Download URL")
    print("=" * 50)

    try:
        download_url = client.get_task_result(task_id, file_type="json")
        print("Result ready.")
        print(f"Download URL: {download_url}")
    except ThordataError as e:
        print(f"Get result failed: {e}")


def demo_using_config() -> None:
    print("\n" + "=" * 50)
    print("5) Using ScraperTaskConfig")
    print("=" * 50)

    config = ScraperTaskConfig(
        file_name="demo_config_task",
        spider_id="example-spider-id",
        spider_name="example.com",
        parameters={"url": "https://example.com", "depth": "1"},
        include_errors=True,
    )

    print("ScraperTaskConfig created:")
    print(f"- file_name: {config.file_name}")
    print(f"- spider_id: {config.spider_id}")
    print(f"- spider_name: {config.spider_name}")
    print("To create a task with this config, call:")
    print("client.create_scraper_task_advanced(config)")


def main() -> int:
    _configure_stdio()
    _load_env()

    scraper_token = os.getenv("THORDATA_SCRAPER_TOKEN")
    public_token = os.getenv("THORDATA_PUBLIC_TOKEN")
    public_key = os.getenv("THORDATA_PUBLIC_KEY")

    if not scraper_token:
        print("Error: THORDATA_SCRAPER_TOKEN is missing.")
        return 1

    if not public_token or not public_key:
        print("Error: THORDATA_PUBLIC_TOKEN and THORDATA_PUBLIC_KEY are required.")
        return 1

    print("=" * 50)
    print("Thordata SDK - Web Scraper API Demo")
    print("=" * 50)

    client = ThordataClient(
        scraper_token=scraper_token,
        public_token=public_token,
        public_key=public_key,
    )

    task_id = demo_create_task(client)

    if task_id:
        demo_poll_status(client, task_id)
        completed = demo_wait_for_completion(client, task_id)
        if completed:
            demo_get_result(client, task_id)

    demo_using_config()

    print("\n" + "=" * 50)
    print("Demo complete.")
    print("=" * 50)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
