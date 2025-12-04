"""
Demo: Web Scraper API usage (Task-based scraping).

Corresponds to the "Web Scraper API -> Send your first request" section in the docs.

Example:
- Creates a scraping task using a known Spider ID (from Dashboard).
- Polls task status until completion.
- Retrieves the download URL for the results.
"""

from __future__ import annotations

import os
import time
import logging
from dotenv import load_dotenv

from thordata import (
    ThordataClient,
    ThordataRateLimitError,
    ThordataAuthError,
)

logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")

load_dotenv()
SCRAPER_TOKEN = os.getenv("THORDATA_SCRAPER_TOKEN")
PUBLIC_TOKEN = os.getenv("THORDATA_PUBLIC_TOKEN")
PUBLIC_KEY = os.getenv("THORDATA_PUBLIC_KEY")

if not SCRAPER_TOKEN or not PUBLIC_TOKEN or not PUBLIC_KEY:
    raise ValueError(
        "Missing credentials. Please set THORDATA_SCRAPER_TOKEN, "
        "THORDATA_PUBLIC_TOKEN, and THORDATA_PUBLIC_KEY in .env."
    )

# You must replace these with a valid spider from your Thordata Dashboard
SPIDER_ID = os.getenv("DEMO_SPIDER_ID", "youtube_video-post_by-url")
SPIDER_NAME = os.getenv("DEMO_SPIDER_NAME", "youtube.com")
SPIDER_PARAMS = {
    "url": "https://www.youtube.com/@stephcurry/videos",
    "order_by": "",
    "num_of_posts": "",
}


def main() -> None:
    print("=== Thordata Web Scraper API Demo ===")
    client = ThordataClient(SCRAPER_TOKEN, PUBLIC_TOKEN, PUBLIC_KEY)

    # 1. Create Task
    print(f"\n[1] Creating task for spider: {SPIDER_NAME} ({SPIDER_ID})...")
    try:
        task_id = client.create_scraper_task(
            file_name="demo_youtube_data",
            spider_id=SPIDER_ID,
            spider_name=SPIDER_NAME,
            individual_params=SPIDER_PARAMS,
        )
        print(f"✅ Task created. ID: {task_id}")
    except ThordataRateLimitError as e:
        print("❌ Task creation failed: Insufficient balance or permissions (402).")
        print(f"   Details: {e}")
        return
    except ThordataAuthError as e:
        print("❌ Task creation failed: Authentication error (401/403).")
        return
    except Exception as e:
        print(f"❌ Task creation failed: {e}")
        return

    # 2. Poll Status
    print("\n[2] Waiting for task completion...")
    final_status = "Unknown"
    for i in range(10):
        final_status = client.get_task_status(task_id)
        print(f"   Check {i + 1}: {final_status}")
        if final_status.lower() in ["ready", "success", "finished", "completed"]:
            break
        if final_status.lower() in ["failed", "error"]:
            print("❌ Task reported failure.")
            return
        time.sleep(3)

    if final_status.lower() not in ["ready", "success", "finished", "completed"]:
        print("⚠️ Task did not finish within the polling window.")
        return

    # 3. Get Download URL
    print("\n[3] Fetching download URL...")
    try:
        download_url = client.get_task_result(task_id, file_type="json")
        print("✅ Task result ready.")
        print(f"📥 Download URL: {download_url}")
    except Exception as e:
        print(f"❌ Failed to get result URL: {e}")


if __name__ == "__main__":
    main()