"""
Demo: High-concurrency requests using AsyncThordataClient.

Demonstrates:
- Async client initialization (context manager).
- Concurrent execution using asyncio.gather.
- Proper resource management (aiohttp).
"""

import os
import asyncio
import time
import logging
import aiohttp

from dotenv import load_dotenv
from thordata import AsyncThordataClient

logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")

load_dotenv()

SCRAPER_TOKEN = os.getenv("THORDATA_SCRAPER_TOKEN")
PUBLIC_TOKEN = os.getenv("THORDATA_PUBLIC_TOKEN", "")
PUBLIC_KEY = os.getenv("THORDATA_PUBLIC_KEY", "")

if not SCRAPER_TOKEN:
    raise ValueError("Missing THORDATA_SCRAPER_TOKEN in .env file.")

# Target: Request multiple endpoints concurrently
TARGET_URLS = [
    "http://httpbin.org/ip",
    "http://httpbin.org/ip",
    "http://httpbin.org/ip",
    "http://httpbin.org/ip",
    "http://httpbin.org/ip",
]


async def fetch_url(client: AsyncThordataClient, url: str, index: int) -> str:
    """Async fetch a single URL."""
    try:
        # client.get returns an aiohttp.ClientResponse
        # We use 'async with' to ensure the connection is released promptly.
        async with await client.get(url) as response:
            response.raise_for_status()
            data = await response.json()
            origin = data.get("origin")
            print(f"[Req {index}] ✅ Success | Status: {response.status} | IP: {origin}")
            return f"Req {index} OK"

    except aiohttp.ClientResponseError as e:
        print(f"[Req {index}] ❌ HTTP Error: {e.status}")
        return f"Req {index} Fail"
    except aiohttp.ClientError as e:
        print(f"[Req {index}] ❌ Connection Error: {e}")
        return f"Req {index} Fail"
    except Exception as e:
        print(f"[Req {index}] ❌ Unexpected Error: {e}")
        return f"Req {index} Fail"


async def run_async_test() -> None:
    print("--- 1. Initialize Async Client ---")

    # Context manager ensures the underlying session is closed properly
    async with AsyncThordataClient(
        scraper_token=SCRAPER_TOKEN,
        public_token=PUBLIC_TOKEN,
        public_key=PUBLIC_KEY,
    ) as client:

        print(f"--- 2. Launching {len(TARGET_URLS)} concurrent tasks ---")

        start_time = time.perf_counter()

        # Create tasks
        tasks = [fetch_url(client, url, i) for i, url in enumerate(TARGET_URLS)]

        # Execute concurrently
        results = await asyncio.gather(*tasks)

        duration = time.perf_counter() - start_time

        print("\n--- 3. Summary ---")
        print(f"Total Requests: {len(results)}")
        success_count = sum(1 for r in results if "OK" in r)
        print(f"Success: {success_count} / {len(results)}")
        print(f"Time Taken: {duration:.2f} seconds")


if __name__ == "__main__":
    print("=== Thordata SDK Async Test ===")
    asyncio.run(run_async_test())
    print("===============================")