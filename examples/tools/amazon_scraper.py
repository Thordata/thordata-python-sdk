"""
Amazon Scraper Example using Thordata SDK
=========================================

This script demonstrates how to scrape Amazon Product Data, Reviews, and Search Results
using the high-level Tool API.

Requirements:
    pip install thordata-sdk
    Set THORDATA_SCRAPER_TOKEN, THORDATA_PUBLIC_TOKEN, THORDATA_PUBLIC_KEY in .env
"""

import os

from thordata import ThordataClient
from thordata.tools import Amazon


def main():
    # 1. Initialize Client
    client = ThordataClient(
        scraper_token=os.getenv("THORDATA_SCRAPER_TOKEN"),
        public_token=os.getenv("THORDATA_PUBLIC_TOKEN"),
        public_key=os.getenv("THORDATA_PUBLIC_KEY"),
    )

    print("🚀 Starting Amazon Scraper...")

    # 2. Define the Request (Strongly Typed!)
    # Scrape a product by ASIN
    request = Amazon.Product(asin="B08N5WRWNW", domain="amazon.com")  # Example ASIN

    # 3. Run the Tool
    print(f"Submitting task for ASIN: {request.asin}...")
    task_id = client.run_tool(request)
    print(f"✅ Task Created! ID: {task_id}")

    # 4. Wait for Results
    print("Waiting for data...")
    status = client.wait_for_task(task_id)

    if status == "finished":
        # 5. Get Download URL
        url = client.get_task_result(task_id)
        print(f"🎉 Success! Download Data Here: {url}")
    else:
        print(f"❌ Task Failed with status: {status}")


if __name__ == "__main__":
    main()
