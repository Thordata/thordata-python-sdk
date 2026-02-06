"""
Thordata Universal API (Web Unlocker) Demo.

This script is designed to work both with the real API and the test
environment used in `tests/test_examples.py`:

- In tests, THORDATA_UNIVERSALAPI_BASE_URL points to a local mock server.
- In production, you normally do NOT need to set this; defaults are used.

The script:
- Optionally loads .env from the repo root (if present).
- Uses THORDATA_SCRAPER_TOKEN for authentication.
- Performs a simple HTML scrape against https://example.com.
"""

from __future__ import annotations

import os

from thordata import ThordataClient, ThordataError, load_env_file


def main() -> int:
    # Best-effort .env load (no-op if file is missing)
    repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    load_env_file(os.path.join(repo_root, ".env"))

    token = os.getenv("THORDATA_SCRAPER_TOKEN")
    base_url = os.getenv("THORDATA_UNIVERSALAPI_BASE_URL")

    if not token:
        print("Missing THORDATA_SCRAPER_TOKEN")
        return 1

    client = ThordataClient(scraper_token=token, universalapi_base_url=base_url)

    url = os.getenv("THORDATA_DEMO_UNIVERSAL_URL", "https://www.example.com")
    print(f"Scraping Example via Universal API: {url}")
    try:
        # Using output_format to trigger specific mock handler in tests.
        html = client.universal_scrape(
            url=url,
            js_render=True,
            output_format="html",
        )
    except ThordataError as e:
        # Friendlier message for real-world usage
        print(f"Universal scrape failed: {e}")
        return 2

    # In real calls, html should be a string; in tests, it's a small fixed HTML.
    print(f"Scraped {len(html)} bytes")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
