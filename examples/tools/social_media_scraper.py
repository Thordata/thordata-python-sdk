"""
Social Media Scraper Example (TikTok & Twitter/X)
=================================================

Demonstrates scraping social media profiles and posts using Thordata Tools.
"""

import os

from thordata import ThordataClient
from thordata.tools import TikTok, Twitter


def main():
    client = ThordataClient(
        scraper_token=os.getenv("THORDATA_SCRAPER_TOKEN"),
        public_token=os.getenv("THORDATA_PUBLIC_TOKEN"),
        public_key=os.getenv("THORDATA_PUBLIC_KEY"),
    )

    # --- Example 1: TikTok Profile ---
    print("\n--- Scraping TikTok Profile ---")
    tiktok_req = TikTok.Profile(url="https://www.tiktok.com/@tiktok", country="us")

    # Using run_task wrapper which handles polling internally for convenience
    # Note: run_tool creates the task; wait_for_task polls it.
    # To do it in one line (create + wait), use client.run_task(...)
    # OR helper function below for tools.

    task_id = client.run_tool(tiktok_req)
    print(f"TikTok Task ID: {task_id}")

    # --- Example 2: X (Twitter) Post ---
    print("\n--- Scraping X (Twitter) Post ---")
    twitter_req = Twitter.Post(url="https://x.com/ElonMusk/status/1234567890")

    task_id_x = client.run_tool(twitter_req)
    print(f"Twitter Task ID: {task_id_x}")

    print("\nCheck your dashboard or use client.wait_for_task(id) to get results.")


if __name__ == "__main__":
    main()
