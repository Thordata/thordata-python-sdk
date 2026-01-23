"""
Google Maps Scraper Example
===========================

Demonstrates how to scrape Google Maps place details using Thordata Tools.
"""

import os

from thordata import ThordataClient
from thordata.tools import GoogleMaps


def main():
    # 1. Init
    client = ThordataClient(
        scraper_token=os.getenv("THORDATA_SCRAPER_TOKEN"),
        public_token=os.getenv("THORDATA_PUBLIC_TOKEN"),
        public_key=os.getenv("THORDATA_PUBLIC_KEY"),
    )

    # 2. Define Target (Eiffel Tower)
    place_url = "https://www.google.com/maps/place/Eiffel+Tower/@48.8584,2.2945,17z/data=!3m1!4b1!4m6!3m5!1s0x47e66e2964e34e2d:0x8ddca9ee380ef7e0!8m2!3d48.8583701!4d2.2944813!16zL20vMDJqODE?entry=ttu"

    print(f"📍 Target: {place_url[:60]}...")

    # 3. Create Request
    request = GoogleMaps.Details(url=place_url)

    # 4. Run
    task_id = client.run_tool(request)
    print(f"🚀 Task Created: {task_id}")

    # 5. Wait
    status = client.wait_for_task(task_id)
    print(f"🏁 Status: {status}")

    if status == "finished":
        link = client.get_task_result(task_id)
        print(f"💾 Download: {link}")
    else:
        print("❌ Scraping failed.")


if __name__ == "__main__":
    main()
