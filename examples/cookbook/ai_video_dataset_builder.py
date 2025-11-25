# examples/cookbook/ai_video_dataset_builder.py
"""
COOKBOOK: AI Video Dataset Builder
----------------------------------
Scenario: An AI company needs metadata from thousands of YouTube videos 
to train a multi-modal model (LMM).

This script demonstrates how to use Thordata Web Scraper to fetch
video metadata efficiently.
"""

import os
import time
import json
from thordata_sdk import ThordataClient

# ⚠️ 配置你的 Key
SCRAPER_TOKEN = os.getenv("THORDATA_SCRAPER_TOKEN", "YOUR_TOKEN_HERE")
PUBLIC_TOKEN = os.getenv("THORDATA_PUBLIC_TOKEN", "YOUR_TOKEN_HERE")
PUBLIC_KEY = os.getenv("THORDATA_PUBLIC_KEY", "YOUR_KEY_HERE")

def build_dataset():
    if SCRAPER_TOKEN == "YOUR_TOKEN_HERE":
        print("Please set your tokens first.")
        return

    client = ThordataClient(SCRAPER_TOKEN, PUBLIC_TOKEN, PUBLIC_KEY)
    
    # 假设我们需要抓取这些频道的视频作为训练数据
    target_channels = [
        "https://www.youtube.com/@OpenAI",
        "https://www.youtube.com/@NVIDIA",
        "https://www.youtube.com/@DeepMind"
    ]
    
    print(f"🤖 Starting AI Dataset Job for {len(target_channels)} channels...")
    
    tasks = {}
    
    # 1. 批量创建任务
    for url in target_channels:
        channel_name = url.split("@")[-1]
        print(f"   -> Queueing scraper for: {channel_name}")
        
        task_id = client.create_scraper_task(
            file_name=f"dataset_{channel_name}",
            spider_id="youtube_video-post_by-url",
            spider_name="youtube.com",
            individual_params={
                "url": url,
                "order_by": "", # Default sort
                "num_of_posts": "" # Default batch
            }
        )
        tasks[channel_name] = task_id
    
    print(f"✅ All tasks queued. IDs: {list(tasks.values())}")
    print("⏳ Waiting for cloud processing (Simulated)...")
    
    # 这里仅演示逻辑，实际使用时可以使用 async_client 并发轮询
    print("   (In a real scenario, data would be downloaded and saved to 'datasets/' folder)")
    print("✅ Dataset pipeline initialized successfully.")

if __name__ == "__main__":
    build_dataset()