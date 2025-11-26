"""
Demo: Web Scraper API usage (task-based scraping).

Example:
- Creates a YouTube spider task (configured in Thordata Dashboard).
- Polls task status until completion.
- Retrieves the download URL for the scraped data.
"""

import os
import time
from dotenv import load_dotenv

from thordata import ThordataClient, Engine  # Engine imported if you want to mix SERP in future

# Load credentials from .env
load_dotenv()
SCRAPER_TOKEN = os.getenv("THORDATA_SCRAPER_TOKEN")
PUBLIC_TOKEN = os.getenv("THORDATA_PUBLIC_TOKEN")
PUBLIC_KEY = os.getenv("THORDATA_PUBLIC_KEY")

if not SCRAPER_TOKEN:
    raise ValueError(
        "Missing THORDATA_SCRAPER_TOKEN. "
        "Please copy .env.example to .env and fill in your credentials."
    )


def main() -> None:
    print("=== Thordata Web Scraper API Demo ===")

    client = ThordataClient(SCRAPER_TOKEN, PUBLIC_TOKEN, PUBLIC_KEY)

    # ------------------------------------------------------------------
    # 1. Create Web Scraper Task (example: YouTube channel videos)
    # ------------------------------------------------------------------
    print("\n[1] Creating YouTube scraper task...")

    try:
        task_id = client.create_scraper_task(
            file_name="demo_youtube_data",
            spider_id="youtube_video-post_by-url",  # from Dashboard
            spider_name="youtube.com",              # from Dashboard
            individual_params={
                "url": "https://www.youtube.com/@stephcurry/videos",
                "order_by": "",
                "num_of_posts": "",
            },
        )
        print(f"✅ Task created. ID: {task_id}")
    except Exception as e:
        print(f"❌ Task creation failed: {e}")
        return

    # ------------------------------------------------------------------
    # 2. Poll Task Status
    # ------------------------------------------------------------------
    print("\n[2] Waiting for task completion...")

    status = "Unknown"
    for i in range(10):
        status = client.get_task_status(task_id)
        print(f"   Check {i + 1}: {status}")
        if status in ["Ready", "Success", "finished", "completed"]:
            break
        if status in ["Failed", "Error"]:
            print("❌ Task failed.")
            return
        time.sleep(3)

    if status not in ["Ready", "Success", "finished", "completed"]:
        print("⚠️ Task did not finish within the polling window.")
        return

    # ------------------------------------------------------------------
    # 3. Get Task Result (Download URL)
    # ------------------------------------------------------------------
    print("\n[3] Fetching download URL for completed task...")
    try:
        download_url = client.get_task_result(task_id, file_type="json")
        print("✅ Task completed successfully.")
        print(f"📥 Download URL: {download_url}")
    except Exception as e:
        print(f"❌ Failed to get task result: {e}")


if __name__ == "__main__":
    main()