# examples/cookbook/ecommerce_price_tracker.py
"""
COOKBOOK: Cross-border E-commerce Price Tracker
-----------------------------------------------
Scenario: An e-commerce seller wants to monitor competitor prices 
for a specific product on Google Shopping globally.
"""

import os
from thordata_sdk import ThordataClient

# ⚠️ 配置你的 Key
SCRAPER_TOKEN = os.getenv("THORDATA_SCRAPER_TOKEN", "YOUR_TOKEN_HERE")
PUBLIC_TOKEN = os.getenv("THORDATA_PUBLIC_TOKEN", "YOUR_TOKEN_HERE")
PUBLIC_KEY = os.getenv("THORDATA_PUBLIC_KEY", "YOUR_KEY_HERE")

def track_prices():
    if SCRAPER_TOKEN == "YOUR_TOKEN_HERE":
        print("Please set your tokens first.")
        return

    client = ThordataClient(SCRAPER_TOKEN, PUBLIC_TOKEN, PUBLIC_KEY)
    
    product_name = "iPhone 15 Pro Max 256GB"
    target_markets = ["us", "uk", "jp"] # 美国, 英国, 日本
    
    print(f"🌍 Starting Global Price Tracking for: {product_name}")
    
    for market in target_markets:
        print(f"\n🔍 Searching in market: {market.upper()}...")
        
        # 使用 SERP API 指定国家 (gl=country code)
        try:
            results = client.serp_search(
                query=product_name, 
                engine="google", 
                gl=market, # Google Location parameter
                num=3
            )
            
            if "organic" in results:
                top_hit = results["organic"][0]
                print(f"   👉 Top Result: {top_hit.get('title')}")
                print(f"      Link: {top_hit.get('link')}")
            else:
                print("   ⚠️ No results found.")
                
        except Exception as e:
            print(f"   ❌ Error tracking {market}: {e}")

if __name__ == "__main__":
    track_prices()