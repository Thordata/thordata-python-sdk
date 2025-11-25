# examples/async_high_concurrency.py
# Goal: Demonstrate high-concurrency requests using AsyncThordataClient

import os
import asyncio
import aiohttp
from thordata_sdk import AsyncThordataClient

# --- Configuration ---
SCRAPER_TOKEN = os.getenv("THORDATA_SCRAPER_TOKEN", "fb6b478700dbbdf3651f314dde1e673a") 
PUBLIC_TOKEN = os.getenv("THORDATA_PUBLIC_TOKEN", "placeholder_token")
PUBLIC_KEY = os.getenv("THORDATA_PUBLIC_KEY", "placeholder_key")

# Target: Request multiple endpoints concurrently
TARGET_URLS = [
    "http://httpbin.org/ip",
    "http://httpbin.org/ip",
    "http://httpbin.org/ip",
    "http://httpbin.org/ip",
    "http://httpbin.org/ip",
]

async def fetch_url(client: AsyncThordataClient, url: str, index: int):
    """Async fetch a single URL."""
    try:
        # Note: client.get returns an awaited ClientResponse
        response = await client.get(url, headers={'X-Request-Index': str(index)})
        
        # In aiohttp, we should ensure we read the body to release the connection
        try:
            data = await response.json()
            print(f"[Req {index}] ✅ Success | Status: {response.status} | IP: {data.get('origin')}")
            return f"Req {index} OK"
        finally:
            # Ensure the response is released
            response.release()

    except aiohttp.ClientError as e:
        print(f"[Req {index}] ❌ ClientError: {e}")
        return f"Req {index} Fail"
    except Exception as e:
        print(f"[Req {index}] ❌ Error: {e}")
        return f"Req {index} Fail"

async def run_async_test():
    print("--- 1. Initialize Async Client ---")
    
    # Context manager ensures the underlying session is closed properly
    async with AsyncThordataClient(
        scraper_token=SCRAPER_TOKEN,
        public_token=PUBLIC_TOKEN,
        public_key=PUBLIC_KEY
    ) as client:
        
        print(f"--- 2. Launching {len(TARGET_URLS)} concurrent tasks ---")
        
        # Create tasks
        tasks = [fetch_url(client, url, i) for i, url in enumerate(TARGET_URLS)]
        
        # Execute concurrently
        results = await asyncio.gather(*tasks)
        
        print("\n--- 3. Summary ---")
        print(f"Total Requests: {len(results)}")

if __name__ == "__main__":
    print("=== Thordata SDK Async Test ===")
    asyncio.run(run_async_test())
    print("===============================")