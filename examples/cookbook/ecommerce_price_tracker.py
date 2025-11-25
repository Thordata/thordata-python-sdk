# examples/cookbook/ecommerce_price_tracker.py
import os
from dotenv import load_dotenv
# 🌟 导入新的枚举
from thordata_sdk import ThordataClient, Engine, GoogleSearchType

load_dotenv()

SCRAPER_TOKEN = os.getenv("THORDATA_SCRAPER_TOKEN")
PUBLIC_TOKEN = os.getenv("THORDATA_PUBLIC_TOKEN")
PUBLIC_KEY = os.getenv("THORDATA_PUBLIC_KEY")

def track_prices():
    if not SCRAPER_TOKEN:
        print("Please check your .env file.")
        return

    client = ThordataClient(SCRAPER_TOKEN, PUBLIC_TOKEN, PUBLIC_KEY)
    
    product_name = "iPhone 15 Pro Max 256GB"
    target_markets = ["us", "uk", "jp"]
    
    print(f"🌍 Starting Global Price Tracking for: {product_name}")
    
    for market in target_markets:
        print(f"\n🔍 Searching in market: {market.upper()}...")
        
        try:
            # 🌟 使用新 SDK 的参数透传功能
            # 我们直接把 gl=market 传进去，SDK 会自动处理
            results = client.serp_search(
                query=product_name, 
                engine=Engine.GOOGLE, 
                type=GoogleSearchType.SHOPPING, # 指定搜索类型为购物
                gl=market, 
                num=3
            )
            
            # 注意：Shopping 结果的结构可能和 organic 不一样，这里做个通用打印
            if "shopping_results" in results:
                top_hit = results["shopping_results"][0]
                print(f"   💰 Price: {top_hit.get('price')} ({top_hit.get('source')})")
                print(f"      Link: {top_hit.get('link')}")
            elif "organic" in results:
                top_hit = results["organic"][0]
                print(f"   👉 Top Result: {top_hit.get('title')}")
            else:
                print("   ⚠️ No results found.")
                
        except Exception as e:
            print(f"   ❌ Error tracking {market}: {e}")

if __name__ == "__main__":
    track_prices()