# Goal: Demonstrate Universal Scraping API (HTML & Screenshots).

import os
from dotenv import load_dotenv
from thordata import ThordataClient 

load_dotenv()

SCRAPER_TOKEN = os.getenv("THORDATA_SCRAPER_TOKEN")
PUBLIC_TOKEN = os.getenv("THORDATA_PUBLIC_TOKEN") 
PUBLIC_KEY = os.getenv("THORDATA_PUBLIC_KEY")

if not SCRAPER_TOKEN:
    print("❌ Error: Please configure your .env file.")
    exit(1)

client = ThordataClient(SCRAPER_TOKEN, PUBLIC_TOKEN, PUBLIC_KEY)

def scrape_html():
    target_url = "http://httpbin.org/ip"
    print(f"\n📄 [1] Scraping HTML from: {target_url}...")
    
    try:
        # js_render=False is faster for simple sites
        html = client.universal_scrape(url=target_url, js_render=False)
        print("✅ HTML Scrape Success!")
        print(f"   Content Preview: {str(html)[:100]}...")
    except Exception as e:
        print(f"❌ HTML Scrape Failed: {e}")

def take_screenshot():
    # Using example.com as it is stable for demos
    target_url = "https://www.example.com"
    filename = "screenshot_result.png"
    print(f"\n📸 [2] Taking Screenshot of: {target_url}...")
    
    try:
        # The SDK automatically handles Base64 decoding and cleaning
        image_bytes = client.universal_scrape(
            url=target_url,
            output_format="PNG",
            js_render=True,
            block_resources=False
        )
        
        with open(filename, "wb") as f:
            f.write(image_bytes)
            
        print(f"✅ Screenshot Success!")
        print(f"📂 Saved to: {os.path.abspath(filename)}")
        print(f"📊 Size: {len(image_bytes)} bytes")
        
    except Exception as e:
        print(f"❌ Screenshot Failed: {e}")

if __name__ == "__main__":
    print("=== Thordata Universal API Demo ===")
    scrape_html()
    take_screenshot()