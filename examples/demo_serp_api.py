"""
Thordata SERP API Demo
"""

import os
import sys

from thordata import Engine, ThordataClient


def main():
    token = os.getenv("THORDATA_SCRAPER_TOKEN")
    base_url = os.getenv("THORDATA_SCRAPERAPI_BASE_URL")

    if not token:
        print("Missing THORDATA_SCRAPER_TOKEN")
        return 1

    client = ThordataClient(scraper_token=token, scraperapi_base_url=base_url)

    print("Searching Google...")
    results = client.serp_search(query="thordata sdk", engine=Engine.GOOGLE, num=3)

    # Simple output for test verification
    if "organic" in results:
        print(f"Got {len(results['organic'])} results")
    elif "organic_results" in results:
        print(f"Got {len(results['organic_results'])} results")

    return 0


if __name__ == "__main__":
    sys.exit(main())
