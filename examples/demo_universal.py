"""
Universal API Demo - Web Unlocker / Universal Scrape

Demonstrates:
- Fetching HTML via Universal API
- Fetching screenshot (PNG) via Universal API
- Optional async usage

Environment variables:
- THORDATA_SCRAPER_TOKEN (required)
- THORDATA_DEMO_OUTPUT_DIR (optional) if set, writes universal.html and screenshot.png

Usage:
    python examples/demo_universal.py
"""

from __future__ import annotations

import asyncio
import os
import sys

try:
    from dotenv import load_dotenv
except ImportError:
    load_dotenv = None

from thordata import AsyncThordataClient, ThordataClient


def _configure_stdio() -> None:
    # Avoid UnicodeEncodeError on Windows consoles with legacy encodings.
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")


def _load_env() -> None:
    if load_dotenv is not None:
        load_dotenv()


def _maybe_write_files(html: str, png: bytes) -> None:
    out_dir = os.getenv("THORDATA_DEMO_OUTPUT_DIR")
    if not out_dir:
        return

    os.makedirs(out_dir, exist_ok=True)

    html_path = os.path.join(out_dir, "universal.html")
    png_path = os.path.join(out_dir, "screenshot.png")

    with open(html_path, "w", encoding="utf-8") as f:
        f.write(html)

    with open(png_path, "wb") as f:
        f.write(png)

    print(f"Wrote demo outputs to: {out_dir}")


def demo_sync(scraper_token: str) -> None:
    print("=" * 50)
    print("1) Sync Universal Scrape")
    print("=" * 50)

    with ThordataClient(scraper_token=scraper_token) as client:
        html = client.universal_scrape(
            "https://example.com",
            js_render=False,
            output_format="html",
        )
        png = client.universal_scrape(
            "https://example.com",
            js_render=True,
            output_format="png",
        )

    assert isinstance(html, str)
    assert isinstance(png, (bytes, bytearray))

    print(f"HTML length: {len(html)}")
    print(f"PNG bytes: {len(png)}")

    _maybe_write_files(html, bytes(png))


async def demo_async(scraper_token: str) -> None:
    print("=" * 50)
    print("2) Async Universal Scrape")
    print("=" * 50)

    async with AsyncThordataClient(scraper_token=scraper_token) as client:
        html = await client.universal_scrape(
            "https://example.com",
            js_render=False,
            output_format="html",
        )
        png = await client.universal_scrape(
            "https://example.com",
            js_render=True,
            output_format="png",
        )

    assert isinstance(html, str)
    assert isinstance(png, (bytes, bytearray))

    print(f"Async HTML length: {len(html)}")
    print(f"Async PNG bytes: {len(png)}")


def main() -> int:
    _configure_stdio()
    _load_env()

    scraper_token = os.getenv("THORDATA_SCRAPER_TOKEN")
    if not scraper_token:
        print("Error: THORDATA_SCRAPER_TOKEN is missing.")
        return 1

    print("=" * 50)
    print("Thordata SDK - Universal API Demo")
    print("=" * 50)

    demo_sync(scraper_token)
    asyncio.run(demo_async(scraper_token))

    print("=" * 50)
    print("Demo complete.")
    print("=" * 50)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
