"""
Thordata Web Scraper API (Tasks) Demo
"""

import os
import sys

from thordata import ThordataClient


def main():
    s_token = os.getenv("THORDATA_SCRAPER_TOKEN")
    p_token = os.getenv("THORDATA_PUBLIC_TOKEN")
    p_key = os.getenv("THORDATA_PUBLIC_KEY")
    s_base = os.getenv("THORDATA_SCRAPERAPI_BASE_URL")
    w_base = os.getenv("THORDATA_WEB_SCRAPER_API_BASE_URL")

    if not all([s_token, p_token, p_key]):
        print("Missing tokens")
        return 1

    client = ThordataClient(
        scraper_token=s_token,
        public_token=p_token,
        public_key=p_key,
        scraperapi_base_url=s_base,
        web_scraper_api_base_url=w_base,
    )

    print("Creating task...")
    task_id = client.create_scraper_task(
        file_name="demo_task",
        spider_id="universal",
        spider_name="universal",
        parameters={"url": "https://example.com"},
    )
    print(f"Task ID: {task_id}")

    status = client.get_task_status(task_id)
    print(f"Status: {status}")

    # Mocking a download call for test coverage
    try:
        url = client.get_task_result(task_id)
        print(f"Result URL: {url}")
    except Exception:
        pass

    return 0


if __name__ == "__main__":
    sys.exit(main())
