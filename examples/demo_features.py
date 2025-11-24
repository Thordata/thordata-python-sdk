# D:\Thordata_Work\thordata-python-sdk\examples\demo_features.py

import os
import sys
import time
import json

# Ensure thordata_sdk is in path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from thordata_sdk.client import ThordataClient 

def main():
    print("=== Thordata SDK Demo ===")

    # -----------------------------------------------------
    # ⚠️ USER CONFIGURATION ⚠️
    # Please replace these placeholders with your actual credentials from the Thordata Dashboard.
    # -----------------------------------------------------
    
    # 1. Scraper Token (From the bottom of Dashboard - for Creating Tasks & SERP)
    SCRAPER_TOKEN = "YOUR_SCRAPER_TOKEN_HERE" 
    
    # 2. Public API Token (From the top of Dashboard - for Checking Status)
    PUBLIC_TOKEN = "YOUR_LONG_PUBLIC_TOKEN_HERE"
    
    # 3. Public Key (From the top of Dashboard - for Signature)
    PUBLIC_KEY = "YOUR_PUBLIC_KEY_HERE"

    if SCRAPER_TOKEN == "YOUR_SCRAPER_TOKEN_HERE":
        print("❌ Error: Please edit 'examples/demo_features.py' and insert your real API tokens.")
        print("   (See README.md for instructions on where to find them)")
        return

    # Initialize Client
    client = ThordataClient(SCRAPER_TOKEN, PUBLIC_TOKEN, PUBLIC_KEY)

    # ==========================================
    # 1. Test SERP API
    # ==========================================
    print("\n--- 1. SERP Search (Google) ---")
    try:
        query = "Thordata technology"
        print(f"Searching for: '{query}'...")
        
        results = client.serp_search(query, engine="google")
        
        # Print Status
        metadata = results.get("search_metadata", {})
        print(f"✅ Status: {metadata.get('status', 'Unknown')}")
        
        # Print Organic Results (这就是你刚才缺少的打印部分)
        if "organic" in results:
            print(f"   Found {len(results['organic'])} organic results. Top 2:")
            for item in results["organic"][:2]:
                print(f"   - {item.get('title')}")
                print(f"     {item.get('link')}")
        else:
            print("   ⚠️ No organic results found.")
            
    except Exception as e:
        print(f"❌ SERP Failed: {e}")

    # ==========================================
    # 2. Test Web Scraper API
    # ==========================================
    print("\n--- 2. Web Scraper (YouTube) ---")
    try:
        # Create Task
        print("Creating task...")
        # Note: Using empty parameters as per Dashboard default to ensure success
        task_id = client.create_scraper_task(
            file_name="demo_youtube_data",
            spider_id="youtube_video-post_by-url",
            spider_name="youtube.com",
            individual_params={
                "url": "https://www.youtube.com/@stephcurry/videos",
                "order_by": "",
                "num_of_posts": ""
            }
        )
        print(f"✅ Task Created! ID: {task_id}")

        # Poll Status
        print("Waiting for completion...")
        for i in range(30):
            status = client.get_task_status(task_id)
            print(f"   Check {i+1}: {status}")
            
            if status in ["Ready", "Success"]:
                break
            elif status == "Failed":
                print("❌ Task failed on server side.")
                return
            time.sleep(5)

        # Get Result
        if status in ["Ready", "Success"]:
            # Wait a bit for CDN generation
            time.sleep(5)
            url = client.get_task_result(task_id)
            print(f"\n✅ Download URL: {url}")
            print("   (Note: If URL returns 404, please wait a moment or check if results are empty)")
            
    except Exception as e:
        print(f"❌ Scraper Failed: {e}")

if __name__ == "__main__":
    main()