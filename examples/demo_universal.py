"""
Thordata Universal API (Web Unlocker) Demo
"""

import os
import sys

from thordata import ThordataClient


def main():
    token = os.getenv("THORDATA_SCRAPER_TOKEN")
    base_url = os.getenv("THORDATA_UNIVERSALAPI_BASE_URL")

    if not token:
        print("Missing THORDATA_SCRAPER_TOKEN")
        return 1

    client = ThordataClient(scraper_token=token, universalapi_base_url=base_url)

    print("Scraping Example...")
    # Using format type to trigger specific mock handler in test
    html = client.universal_scrape(
        url="https://example.com", js_render=False, output_format="html"
    )

    print(f"Scraped {len(html)} bytes")
    return 0


if __name__ == "__main__":
    sys.exit(main())
