"""
High-Concurrency Async Demo

Demonstrates:
- AsyncThordataClient usage
- Parallel requests with asyncio.gather
- Performance measurement
- Error handling in concurrent context

Usage:
    python examples/async_high_concurrency.py
"""

import asyncio
import logging
import os
import sys
import time

from dotenv import load_dotenv

from thordata import (
    AsyncThordataClient,
    ThordataError,
    ThordataNetworkError,
    ThordataTimeoutError,
)

logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")

load_dotenv()

SCRAPER_TOKEN = os.getenv("THORDATA_SCRAPER_TOKEN")

if not SCRAPER_TOKEN:
    print("❌ Error: THORDATA_SCRAPER_TOKEN is missing in .env")
    sys.exit(1)

# Number of concurrent requests
CONCURRENCY = 10


async def fetch_ip(client: AsyncThordataClient, request_id: int) -> dict:
    """Fetch IP through proxy, return result dict."""
    url = "https://httpbin.org/ip"

    try:
        response = await client.get(url)
        data = await response.json()
        ip = data.get("origin", "Unknown")

        return {
            "id": request_id,
            "status": "success",
            "ip": ip,
        }

    except ThordataTimeoutError:
        return {"id": request_id, "status": "timeout", "ip": None}
    except ThordataNetworkError as e:
        return {"id": request_id, "status": f"network_error: {e}", "ip": None}
    except ThordataError as e:
        return {"id": request_id, "status": f"error: {e}", "ip": None}
    except Exception as e:
        return {"id": request_id, "status": f"unexpected: {e}", "ip": None}


async def demo_concurrent_requests():
    """Run multiple concurrent requests."""
    print("\n" + "=" * 50)
    print(f"🚀 Launching {CONCURRENCY} Concurrent Requests")
    print("=" * 50)

    start_time = time.perf_counter()

    async with AsyncThordataClient(scraper_token=SCRAPER_TOKEN) as client:
        # Create tasks
        tasks = [fetch_ip(client, i + 1) for i in range(CONCURRENCY)]

        # Execute all concurrently
        results = await asyncio.gather(*tasks)

    elapsed = time.perf_counter() - start_time

    # Display results
    print("\n📊 Results:")
    success_count = 0
    unique_ips = set()

    for result in results:
        status_icon = "✅" if result["status"] == "success" else "❌"
        ip_display = result["ip"] or result["status"]
        print(f"   {status_icon} Request {result['id']:2d}: {ip_display}")

        if result["status"] == "success":
            success_count += 1
            unique_ips.add(result["ip"])

    # Summary
    print("\n" + "-" * 50)
    print("📈 Summary:")
    print(f"   Total requests:    {CONCURRENCY}")
    print(f"   Successful:        {success_count}")
    print(f"   Failed:            {CONCURRENCY - success_count}")
    print(f"   Unique IPs:        {len(unique_ips)}")
    print(f"   Total time:        {elapsed:.2f}s")
    print(f"   Requests/second:   {CONCURRENCY / elapsed:.1f}")


async def demo_serp_concurrent():
    """Concurrent SERP searches."""
    print("\n" + "=" * 50)
    print("🔍 Concurrent SERP Searches")
    print("=" * 50)

    queries = ["python", "javascript", "rust", "golang", "typescript"]

    async with AsyncThordataClient(scraper_token=SCRAPER_TOKEN) as client:

        async def search(query: str) -> dict:
            try:
                results = await client.serp_search(query=query, num=3)
                count = len(results.get("organic", []))
                return {"query": query, "results": count, "status": "success"}
            except Exception as e:
                return {"query": query, "results": 0, "status": str(e)}

        start = time.perf_counter()
        results = await asyncio.gather(*[search(q) for q in queries])
        elapsed = time.perf_counter() - start

    print("\n📊 Search Results:")
    for r in results:
        icon = "✅" if r["status"] == "success" else "❌"
        print(f"   {icon} '{r['query']}': {r['results']} results")

    print(f"\n   Total time: {elapsed:.2f}s")


if __name__ == "__main__":
    print("=" * 50)
    print("   Thordata SDK - Async High Concurrency Demo")
    print("=" * 50)

    asyncio.run(demo_concurrent_requests())
    asyncio.run(demo_serp_concurrent())

    print("\n" + "=" * 50)
    print("   Demo Complete!")
    print("=" * 50)
