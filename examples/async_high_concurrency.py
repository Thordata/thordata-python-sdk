"""
Async Concurrency Demo (Offline-test friendly)

Demonstrates:
- AsyncThordataClient usage
- Parallel requests with asyncio.gather
- Basic performance measurement
- Error handling in concurrent context

Notes:
- This demo uses the SERP API to make concurrent calls.
- For CI/offline testing, set THORDATA_SCRAPERAPI_BASE_URL to a local mock server.

Environment variables:
- THORDATA_SCRAPER_TOKEN (required)
- THORDATA_CONCURRENCY (optional, default: 10)
- THORDATA_DEMO_QUERY (optional, default: "python")

Usage:
    python examples/async_high_concurrency.py
"""

from __future__ import annotations

import asyncio
import logging
import os
import sys
import time
from typing import Any

try:
    from dotenv import load_dotenv
except ImportError:
    load_dotenv = None

from thordata import AsyncThordataClient, ThordataError

logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")


def _configure_stdio() -> None:
    # Avoid UnicodeEncodeError on Windows consoles with legacy encodings.
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")


def _load_env() -> None:
    if load_dotenv is None:
        return
    from pathlib import Path

    repo_root = Path(__file__).resolve().parents[1]
    load_dotenv(dotenv_path=repo_root / ".env")


def _get_concurrency() -> int:
    try:
        return max(1, int(os.getenv("THORDATA_CONCURRENCY", "10")))
    except ValueError:
        return 10


async def _serp_once(
    client: AsyncThordataClient, query: str, request_id: int
) -> dict[str, Any]:
    try:
        data = await client.serp_search(query=query, num=3, engine="google")
        organic = data.get("organic", [])
        return {"id": request_id, "status": "success", "organic_count": len(organic)}
    except ThordataError as e:
        return {"id": request_id, "status": f"thordata_error: {e}", "organic_count": 0}
    except Exception as e:
        return {"id": request_id, "status": f"unexpected: {e}", "organic_count": 0}


async def demo_concurrent_serp(scraper_token: str) -> None:
    concurrency = _get_concurrency()
    query = os.getenv("THORDATA_DEMO_QUERY", "python")

    print("\n" + "=" * 50)
    print(f"Launching {concurrency} concurrent SERP requests")
    print("=" * 50)

    start_time = time.perf_counter()

    async with AsyncThordataClient(scraper_token=scraper_token) as client:
        tasks = [
            _serp_once(client, query=query, request_id=i + 1)
            for i in range(concurrency)
        ]
        results = await asyncio.gather(*tasks)

    elapsed = time.perf_counter() - start_time

    success_count = sum(1 for r in results if r["status"] == "success")
    counts = [r["organic_count"] for r in results if r["status"] == "success"]

    print("\nResults:")
    for r in results[: min(10, len(results))]:
        # Print only first 10 lines to keep output readable
        print(f"  Request {r['id']:02d}: {r['status']} (organic={r['organic_count']})")

    print("\n" + "-" * 50)
    print("Summary:")
    print(f"  Total requests:  {concurrency}")
    print(f"  Successful:      {success_count}")
    print(f"  Failed:          {concurrency - success_count}")
    print(
        f"  Avg organic:     {(sum(counts) / len(counts)):.2f}"
        if counts
        else "  Avg organic:     N/A"
    )
    print(f"  Total time:      {elapsed:.2f}s")
    print(
        f"  Requests/second: {(concurrency / elapsed):.2f}"
        if elapsed > 0
        else "  Requests/second: N/A"
    )


def main() -> int:
    _configure_stdio()
    _load_env()

    scraper_token = os.getenv("THORDATA_SCRAPER_TOKEN")
    if not scraper_token:
        print("Error: THORDATA_SCRAPER_TOKEN is missing.")
        return 1

    print("=" * 50)
    print("Thordata SDK - Async Concurrency Demo")
    print("=" * 50)

    asyncio.run(demo_concurrent_serp(scraper_token))

    print("\n" + "=" * 50)
    print("Demo complete.")
    print("=" * 50)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
