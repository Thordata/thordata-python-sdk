# Goal: Demonstrate how to use ThordataClient for basic proxy requests.

import os
import logging
from dotenv import load_dotenv
# Note the import: it is 'thordata', not 'thordata_sdk'
from thordata import ThordataClient

# Load environment variables from .env file
load_dotenv()

# --- Configuration ---
SCRAPER_TOKEN = os.getenv("THORDATA_SCRAPER_TOKEN")
PUBLIC_TOKEN = os.getenv("THORDATA_PUBLIC_TOKEN")
PUBLIC_KEY = os.getenv("THORDATA_PUBLIC_KEY")

# Ensure tokens are present
if not SCRAPER_TOKEN:
    raise ValueError("Please set THORDATA_SCRAPER_TOKEN in your .env file.")

TARGET_URL = "http://httpbin.org/ip"

def run_quick_test():
    print("--- 1. Initialize Thordata Client ---")
    try:
        client = ThordataClient(
            scraper_token=SCRAPER_TOKEN,
            public_token=PUBLIC_TOKEN,
            public_key=PUBLIC_KEY
        )
        
        print(f"--- 2. Requesting via Proxy: {TARGET_URL} ---")
        # This request goes through the Residential Proxy Network
        response = client.get(TARGET_URL, timeout=30)

        if response.status_code == 200:
            data = response.json()
            print("✅ Success! Request routed via Thordata.")
            print(f"   Origin IP: {data.get('origin')}")
            print(f"   Status Code: {response.status_code}")
        else:
            print(f"❌ Failed. Status Code: {response.status_code}")
            print(f"   Response: {response.text}")
            
    except Exception as e:
        print(f"❌ An unexpected error occurred: {e}")

if __name__ == "__main__":
    print("=== Thordata SDK Quick Start ===")
    run_quick_test()
    print("================================")