# D:\Thordata_Work\thordata-python-sdk\examples\demo_universal.py

import os
import sys

# Ensure thordata_sdk is in path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from thordata_sdk.client import ThordataClient 

def main():
    print("=== Thordata Universal API Demo ===")

    # -----------------------------------------------------
    # ⚠️ Replace with your actual tokens
    # -----------------------------------------------------
    SCRAPER_TOKEN = "fb6b478700dbbdf3651f314dde1e673a" 
    # Public token is not used for Universal API, but required for init
    PUBLIC_TOKEN = "eWEiAXxMfB05VQEAYXcLRgVYbQ18HjBTeGUkSgRZAGpWUnpmWVMLZ1JZB1g+BQ4tPQhIWzkP" 
    PUBLIC_KEY = "3ndjtera"

    client = ThordataClient(SCRAPER_TOKEN, PUBLIC_TOKEN, PUBLIC_KEY)

    # 1. Test HTML Scraping (e.g., extracting IP info)
    target_url = "http://httpbin.org/ip"
    print(f"\n[1] Scraping HTML from: {target_url}...")
    
    try:
        html_content = client.universal_scrape(
            url=target_url,
            js_render=False,
            country="us" # Use US Proxy
        )
        print("✅ HTML Scrape Success!")
        print(f"   Content Preview: {html_content[:200]}") # Print first 200 chars
    except Exception as e:
        print(f"❌ HTML Scrape Failed: {e}")

    # 2. Test PNG Screenshot (e.g., Google Homepage)
    target_url_img = "https://www.google.com"
    print(f"\n[2] Taking Screenshot of: {target_url_img}...")
    
    try:
        png_data = client.universal_scrape(
            url=target_url_img,
            output_format="PNG",
            js_render=True, 
            block_resources=False
        )
        
        # 🌟 简单检查：如果数据小于 1KB，肯定不是图片，而是报错信息
        if len(png_data) < 1000:
            print(f"❌ Error Content: {png_data}")
            raise Exception("Returned data is too small to be an image.")

        filename = "google_screenshot.png"
        with open(filename, "wb") as f:
            f.write(png_data)
            
        print(f"✅ Screenshot Success! Saved to '{filename}'")
        print(f"   Image Size: {len(png_data)} bytes")
    except Exception as e:
        print(f"❌ Screenshot Failed: {e}")

if __name__ == "__main__":
    main()