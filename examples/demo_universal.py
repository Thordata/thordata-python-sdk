import os
import sys
from dotenv import load_dotenv

# Ensure thordata_sdk is in path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from thordata_sdk.client import ThordataClient 

def main():
    load_dotenv()
    print("=== Thordata Universal API Demo ===")

    # Load Tokens
    SCRAPER_TOKEN = os.getenv("THORDATA_SCRAPER_TOKEN")
    PUBLIC_TOKEN = os.getenv("THORDATA_PUBLIC_TOKEN") 
    PUBLIC_KEY = os.getenv("THORDATA_PUBLIC_KEY")

    if not SCRAPER_TOKEN:
        print("❌ Error: Please configure your .env file.")
        return

    client = ThordataClient(SCRAPER_TOKEN, PUBLIC_TOKEN, PUBLIC_KEY)

    # 1. Test HTML Scraping
    target_url = "http://httpbin.org/ip"
    print(f"\n[1] Scraping HTML from: {target_url}...")
    
    try:
        html = client.universal_scrape(url=target_url, js_render=False)
        print("✅ HTML Scrape Success!")
        print(f"   Content Preview: {html[:100]}...")
    except Exception as e:
        print(f"❌ HTML Scrape Failed: {e}")

    # 2. Test Screenshot
    # 使用 example.com 因为它加载快且稳定，适合演示
    target_url_img = "https://www.example.com"
    print(f"\n[2] Taking Screenshot of: {target_url_img}...")
    
    try:
        # SDK 现在会自动处理 Base64 解码和前缀清洗
        image_bytes = client.universal_scrape(
            url=target_url_img,
            output_format="PNG",
            js_render=True,
            block_resources=False
        )
        
        filename = "screenshot_result.png"
        with open(filename, "wb") as f:
            f.write(image_bytes)
            
        print(f"✅ Screenshot Success!")
        print(f"📂 Saved to: {os.path.abspath(filename)}")
        print(f"📊 Size: {len(image_bytes)} bytes")
        
    except Exception as e:
        print(f"❌ Screenshot Failed: {e}")

if __name__ == "__main__":
    main()