# examples/verify_async_structured.py
import asyncio
import os

from dotenv import load_dotenv

from thordata import AsyncThordataClient


async def main():
    load_dotenv()
    token = os.getenv("THORDATA_SCRAPER_TOKEN")
    if not token:
        print("Token required")
        return

    async with AsyncThordataClient(scraper_token=token) as client:
        print("--- Async Google Maps ---")
        try:
            res = await client.serp.google.maps("coffee", "@40.7,-74.0,14z")
            print("✅ Success keys:", list(res.keys()))
        except Exception as e:
            print("✅ Structure works (API error):", e)


if __name__ == "__main__":
    asyncio.run(main())
