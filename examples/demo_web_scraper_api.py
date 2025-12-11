"""
Web Scraper API Demo - Task-Based Scraping

Demonstrates:
- Creating async scraping tasks
- Polling task status
- Retrieving results
- Using wait_for_task helper

Usage:
    python examples/demo_web_scraper_api.py
"""

import logging
import os
import sys

from dotenv import load_dotenv

from thordata import (
    ThordataClient,
    ScraperTaskConfig,
    ThordataError,
)

logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")

load_dotenv()

SCRAPER_TOKEN = os.getenv("THORDATA_SCRAPER_TOKEN")
PUBLIC_TOKEN = os.getenv("THORDATA_PUBLIC_TOKEN")
PUBLIC_KEY = os.getenv("THORDATA_PUBLIC_KEY")

if not SCRAPER_TOKEN:
    print("❌ Error: THORDATA_SCRAPER_TOKEN is missing in .env")
    sys.exit(1)

if not PUBLIC_TOKEN or not PUBLIC_KEY:
    print("❌ Error: PUBLIC_TOKEN and PUBLIC_KEY required for Web Scraper API")
    print("   Set THORDATA_PUBLIC_TOKEN and THORDATA_PUBLIC_KEY in .env")
    sys.exit(1)


def demo_create_task():
    """Create a web scraper task."""
    print("\n" + "=" * 50)
    print("1️⃣  Create Scraper Task")
    print("=" * 50)

    client = ThordataClient(
        scraper_token=SCRAPER_TOKEN,
        public_token=PUBLIC_TOKEN,
        public_key=PUBLIC_KEY,
    )

    # Example: YouTube channel scrape
    # Note: Get spider_id and spider_name from Thordata Dashboard
    print("   Creating task for YouTube scraping...")
    print("   (This is an example - adjust spider_id for your use case)")

    try:
        task_id = client.create_scraper_task(
            file_name="demo_youtube_data",
            spider_id="youtube_video-post_by-url",  # From Dashboard
            spider_name="youtube.com",
            parameters={
                "url": "https://www.youtube.com/@YouTube/videos",
                "num_of_posts": "5",
            },
        )

        print("✅ Task created!")
        print(f"   Task ID: {task_id}")
        return task_id

    except ThordataError as e:
        print(f"❌ Task creation failed: {e}")
        return None


def demo_poll_status(client: ThordataClient, task_id: str):
    """Poll task status manually."""
    print("\n" + "=" * 50)
    print("2️⃣  Check Task Status")
    print("=" * 50)

    print(f"   Checking status for: {task_id}")

    try:
        status = client.get_task_status(task_id)
        print(f"   Current status: {status}")
        return status

    except ThordataError as e:
        print(f"❌ Status check failed: {e}")
        return None


def demo_wait_for_completion(client: ThordataClient, task_id: str):
    """Wait for task to complete using helper."""
    print("\n" + "=" * 50)
    print("3️⃣  Wait for Completion")
    print("=" * 50)

    print(f"   Waiting for task {task_id}...")
    print("   (Max wait: 60 seconds)")

    try:
        status = client.wait_for_task(
            task_id,
            poll_interval=5.0,
            max_wait=60.0,
        )

        if status.lower() in ("ready", "success", "finished"):
            print(f"✅ Task completed: {status}")
            return True
        else:
            print(f"⚠️  Task ended with status: {status}")
            return False

    except TimeoutError:
        print("⏱️  Task did not complete within 60 seconds")
        return False
    except ThordataError as e:
        print(f"❌ Error waiting: {e}")
        return False


def demo_get_result(client: ThordataClient, task_id: str):
    """Get task result download URL."""
    print("\n" + "=" * 50)
    print("4️⃣  Get Result")
    print("=" * 50)

    try:
        download_url = client.get_task_result(task_id, file_type="json")

        print("✅ Result ready!")
        print(f"   Download URL: {download_url}")

    except ThordataError as e:
        print(f"❌ Get result failed: {e}")


def demo_using_config():
    """Create task using ScraperTaskConfig."""
    print("\n" + "=" * 50)
    print("5️⃣  Using ScraperTaskConfig")
    print("=" * 50)

    config = ScraperTaskConfig(
        file_name="demo_config_task",
        spider_id="example-spider-id",
        spider_name="example.com",
        parameters={
            "url": "https://example.com",
            "depth": "1",
        },
        include_errors=True,
    )

    print("   ScraperTaskConfig created:")
    print(f"   - file_name: {config.file_name}")
    print(f"   - spider_id: {config.spider_id}")
    print(f"   - spider_name: {config.spider_name}")

    # To actually create the task:
    # client.create_scraper_task_advanced(config)


if __name__ == "__main__":
    print("=" * 50)
    print("   Thordata SDK - Web Scraper API Demo")
    print("=" * 50)

    # Initialize client
    client = ThordataClient(
        scraper_token=SCRAPER_TOKEN,
        public_token=PUBLIC_TOKEN,
        public_key=PUBLIC_KEY,
    )

    # Demo the workflow
    task_id = demo_create_task()

    if task_id:
        demo_poll_status(client, task_id)
        completed = demo_wait_for_completion(client, task_id)

        if completed:
            demo_get_result(client, task_id)

    # Show config usage
    demo_using_config()

    print("\n" + "=" * 50)
    print("   Demo Complete!")
    print("=" * 50)
