# D:\Thordata_Work\thordata-python-sdk\examples\demo_features.py

import os
import sys
import time
import json
from dotenv import load_dotenv # pip install python-dotenv

# 路径处理
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# 🌟 新增：导入 Engine 枚举
from thordata_sdk.client import ThordataClient 
from thordata_sdk.enums import Engine

def main():
    load_dotenv() # 自动读取 .env
    print("=== Thordata SDK Demo (v0.2.4+) ===")

    # 从环境变量获取，不再硬编码
    SCRAPER_TOKEN = os.getenv("THORDATA_SCRAPER_TOKEN")
    PUBLIC_TOKEN = os.getenv("THORDATA_PUBLIC_TOKEN") 
    PUBLIC_KEY = os.getenv("THORDATA_PUBLIC_KEY")

    if not SCRAPER_TOKEN:
        print("❌ Error: Missing Token. Please set THORDATA_SCRAPER_TOKEN in .env file.")
        return

    client = ThordataClient(SCRAPER_TOKEN, PUBLIC_TOKEN, PUBLIC_KEY)

    # ==========================================
    # 1. Test SERP API (Using Enum!)
    # ==========================================
    print("\n--- 1. SERP Search (Google) ---")
    try:
        query = "Thordata technology"
        print(f"Searching for: '{query}'...")
        
        # 🌟 最佳实践：使用 Engine.GOOGLE 而不是字符串 "google"
        results = client.serp_search(query, engine=Engine.GOOGLE)
        
        metadata = results.get("search_metadata", {})
        print(f"✅ Status: {metadata.get('status', 'Unknown')}")
        
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
        print("Creating task...")
        task_id = client.create_scraper_task(
            file_name="demo_youtube_data",
            spider_id="youtube_video-post_by-url",
            spider_name="youtube.com", # 这里依然可以用字符串，或者如果你定义了 ScraperTarget 枚举也可以用
            individual_params={
                "url": "https://www.youtube.com/@stephcurry/videos",
                "order_by": "",
                "num_of_posts": ""
            }
        )
        print(f"✅ Task Created! ID: {task_id}")

        print("Waiting for completion...")
        # 简单轮询逻辑
        for i in range(10): 
            status = client.get_task_status(task_id)
            print(f"   Check {i+1}: {status}")
            if status in ["Ready", "Success"]:
                break
            if status == "Failed":
                print("❌ Task failed.")
                return
            time.sleep(3)

        if status in ["Ready", "Success"]:
            url = client.get_task_result(task_id)
            print(f"\n✅ Download URL: {url}")
            
    except Exception as e:
        print(f"❌ Scraper Failed: {e}")

if __name__ == "__main__":
    main()