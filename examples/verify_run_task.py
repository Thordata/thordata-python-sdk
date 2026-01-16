"""
Verify the new 'run_task' method (Sync & Async).
Usage: python examples/verify_run_task.py
"""

import asyncio
import json
import os
from typing import Any

from thordata import AsyncThordataClient, ThordataClient

try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    pass

# 1. Load configuration strictly to satisfy Pylance (str instead of str|None)
SCRAPER_TOKEN = os.getenv("THORDATA_SCRAPER_TOKEN", "")
PUBLIC_TOKEN = os.getenv("THORDATA_PUBLIC_TOKEN", "")
PUBLIC_KEY = os.getenv("THORDATA_PUBLIC_KEY", "")

SPIDER_ID = os.getenv("THORDATA_TASK_SPIDER_ID", "")
SPIDER_NAME = os.getenv("THORDATA_TASK_SPIDER_NAME", "")
RAW_PARAMS = os.getenv("THORDATA_TASK_PARAMETERS_JSON", "{}")

# 2. Parse Parameters safely
try:
    PARAMS: Any = json.loads(RAW_PARAMS)
    # Check if it's a list (Dashboard sometimes copies as [{...}])
    if isinstance(PARAMS, list):
        PARAMS = PARAMS[0]
except json.JSONDecodeError:
    print("❌ Error: Invalid JSON in THORDATA_TASK_PARAMETERS_JSON")
    PARAMS = {}


def check_env():
    if not all([SCRAPER_TOKEN, PUBLIC_TOKEN, PUBLIC_KEY, SPIDER_ID, SPIDER_NAME]):
        print("❌ Missing required .env variables.")
        print(
            f"Token: {bool(SCRAPER_TOKEN)}, Pub: {bool(PUBLIC_TOKEN)}, Key: {bool(PUBLIC_KEY)}"
        )
        print(f"Spider ID: {bool(SPIDER_ID)}, Name: {bool(SPIDER_NAME)}")
        return False
    return True


def test_sync():
    print(f"\n--- Testing Sync run_task [{SPIDER_NAME}] ---")

    client = ThordataClient(
        scraper_token=SCRAPER_TOKEN, public_token=PUBLIC_TOKEN, public_key=PUBLIC_KEY
    )

    try:
        # Use parameters from .env so the spider actually works
        url = client.run_task(
            file_name="sync_verify_" + SPIDER_ID,
            spider_id=SPIDER_ID,
            spider_name=SPIDER_NAME,
            parameters=PARAMS,
            max_wait=600,
            initial_poll_interval=3,
        )
        print(f"✅ Sync Success! Download URL: {url}")
    except Exception as e:
        print(f"❌ Sync Failed: {e}")


async def test_async():
    print(f"\n--- Testing Async run_task [{SPIDER_NAME}] ---")

    async with AsyncThordataClient(
        scraper_token=SCRAPER_TOKEN, public_token=PUBLIC_TOKEN, public_key=PUBLIC_KEY
    ) as client:
        try:
            url = await client.run_task(
                file_name="async_verify_" + SPIDER_ID,
                spider_id=SPIDER_ID,
                spider_name=SPIDER_NAME,
                parameters=PARAMS,
                max_wait=600,
                initial_poll_interval=3,
            )
            print(f"✅ Async Success! Download URL: {url}")
        except Exception as e:
            print(f"❌ Async Failed: {e}")


if __name__ == "__main__":
    if check_env():
        print(f"Parameters: {PARAMS}")
        test_sync()
        asyncio.run(test_async())
