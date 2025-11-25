# examples/quick_test.py
# Goal: Demonstrate how to use ThordataClient for proxy requests (Synchronous)

import os
from thordata_sdk import ThordataClient

# --- Configuration ---
# ⚠️ WARNING: Use Environment Variables for security in production!
# Replace placeholders below with your actual credentials from the Dashboard.
SCRAPER_TOKEN = os.getenv("THORDATA_SCRAPER_TOKEN", "fb6b478700dbbdf3651f314dde1e673a") 
# For simple proxy usage, public tokens are not strictly required, but good to initialize correctly.
PUBLIC_TOKEN = os.getenv("THORDATA_PUBLIC_TOKEN", "placeholder_token")
PUBLIC_KEY = os.getenv("THORDATA_PUBLIC_KEY", "placeholder_key")

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
        response = client.get(TARGET_URL, timeout=15)

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
    print("=== Thordata SDK Quick Test ===")
    run_quick_test()
    print("===============================")