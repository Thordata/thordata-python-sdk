# Web Scraper Tools - User Guide

## Overview

The Thordata Python SDK provides access to **110+ pre-built web scraper tools** (spiders) covering:
- E-commerce (Amazon, eBay, etc.)
- Social Media (TikTok, Instagram, etc.)
- Search Engines (Google Maps, etc.)
- Video Platforms (YouTube, etc.)
- And more...

## Quick Start - Easiest Way to Use

### Method 1: Using Tool Classes (Recommended)

```python
from thordata import ThordataClient
from thordata.tools import Amazon, GoogleMaps, YouTube

client = ThordataClient(
    scraper_token="your_scraper_token",
    public_token="your_public_token",
    public_key="your_public_key"
)

# 1. Create task (one line!)
task_id = client.run_tool(Amazon.Search(keyword="laptop", domain="amazon.com"))

# 2. Wait for completion
status = client.wait_for_task(task_id, max_wait=300)

# 3. Get results
if status.lower() in {"ready", "success", "finished"}:
    result_url = client.get_task_result(task_id)
    print(f"Download results from: {result_url}")
```

### Method 2: Using Tool Key (Alternative)

```python
# If you know the tool key
task_id = client.run_tool_by_key(
    tool="amazon_product-list_by-keywords-domain",
    parameters={"keyword": "laptop", "domain": "amazon.com"}
)
```

### Method 3: Batch Processing

```python
# Run multiple tools in parallel
tasks = [
    Amazon.Search(keyword="laptop", domain="amazon.com"),
    GoogleMaps.DetailsByPlaceId(place_id="ChIJPTacEpBQwokRKwIlDXelxkA"),
    YouTube.VideoInfo(video_id="jNQXAC9IVRw")
]

results = client.run_tools_batch(tasks, concurrency=3)
for result in results:
    if result.get("success"):
        print(f"Task {result['task_id']} completed")
```

## Available Tool Categories

### E-commerce Tools

```python
from thordata.tools import Amazon

# Search products
Amazon.Search(keyword="laptop", domain="amazon.com")

# Get product by ASIN
Amazon.ProductByAsin(asin="B08N5WRWNW")

# Get product by URL
Amazon.ProductByUrl(url="https://www.amazon.com/dp/B08N5WRWNW")

# Get products by category
Amazon.ProductByCategoryUrl(url="https://www.amazon.com/s?k=laptop")
```

### Search/Maps Tools

```python
from thordata.tools import GoogleMaps

# Get place details by Place ID
GoogleMaps.DetailsByPlaceId(place_id="ChIJPTacEpBQwokRKwIlDXelxkA")

# Get place details by CID
GoogleMaps.DetailsByCid(CID="2476046430038551731")

# Search places
GoogleMaps.Search(query="restaurants in New York")
```

### Video Tools

```python
from thordata.tools import YouTube

# Get video info
YouTube.VideoInfo(video_id="jNQXAC9IVRw")

# Get video comments
YouTube.VideoComments(video_id="jNQXAC9IVRw")

# Download video (with settings)
from thordata import CommonSettings
settings = CommonSettings(
    resolution="<=360p",
    video_codec="vp9",
    audio_format="opus"
)
YouTube.VideoDownload(url="https://www.youtube.com/watch?v=jNQXAC9IVRw", common_settings=settings)
```

### Social Media Tools

```python
from thordata.tools import TikTok

# Get user profile
TikTok.UserProfile(username="example_user")

# Get user videos
TikTok.UserVideos(username="example_user")

# Get video by URL
TikTok.VideoByUrl(url="https://www.tiktok.com/@user/video/123456")
```

## Complete Workflow Example

```python
from thordata import ThordataClient
from thordata.tools import Amazon
import time

# Initialize client
client = ThordataClient(
    scraper_token="your_token",
    public_token="your_public_token",
    public_key="your_public_key"
)

# Step 1: Create task
print("Creating task...")
task_id = client.run_tool(Amazon.Search(keyword="laptop", domain="amazon.com"))
print(f"Task ID: {task_id}")

# Step 2: Check status
print("Checking status...")
status = client.get_task_status(task_id)
print(f"Status: {status}")

# Step 3: Wait for completion (with progress updates)
print("Waiting for completion...")
def on_status_update(current_status, elapsed):
    print(f"  Status: {current_status}, Elapsed: {elapsed:.1f}s")

final_status = client.wait_for_task(
    task_id,
    max_wait=300,
    poll_interval=3,
    on_status_update=on_status_update
)

# Step 4: Get results
if final_status.lower() in {"ready", "success", "finished"}:
    result_url = client.get_task_result(task_id)
    print(f"\nResults ready!")
    print(f"Download URL: {result_url}")
    
    # Download and process results
    import requests
    response = requests.get(result_url)
    data = response.json()
    
    print(f"\nFound {len(data.get('products', []))} products")
    for product in data.get('products', [])[:5]:
        print(f"  - {product.get('title', 'N/A')}")
else:
    print(f"Task failed with status: {final_status}")
```

## Finding Available Tools

### List All Tools

```python
# Get all tools
tools = client.list_tools()
print(f"Total tools: {tools['meta']['total']}")

# Get tools by group
ecommerce_tools = client.list_tools(group="ecommerce")
print(f"E-commerce tools: {len(ecommerce_tools['tools'])}")

# Search tools
amazon_tools = client.search_tools("amazon")
print(f"Amazon tools: {len(amazon_tools['tools'])}")
```

### Get Tool Information

```python
# Get tool info by key
tool_info = client.get_tool_info("amazon_product-list_by-keywords-domain")
print(f"Tool name: {tool_info['spider_name']}")
print(f"Parameters: {tool_info['parameters']}")

# Resolve tool key from name
tool_key = client.resolve_tool_key("Amazon Product Search")
print(f"Tool key: {tool_key}")
```

## Best Practices

### 1. Error Handling

```python
from thordata.exceptions import ThordataError

try:
    task_id = client.run_tool(Amazon.Search(keyword="laptop"))
    status = client.wait_for_task(task_id)
    result_url = client.get_task_result(task_id)
except ThordataError as e:
    print(f"API Error: {e}")
    if hasattr(e, 'payload'):
        print(f"Details: {e.payload}")
except TimeoutError:
    print("Task timed out")
except Exception as e:
    print(f"Unexpected error: {e}")
```

### 2. Batch Processing

```python
# Process multiple tasks efficiently
tasks = [
    Amazon.Search(keyword="laptop"),
    Amazon.Search(keyword="phone"),
    Amazon.Search(keyword="tablet")
]

results = client.run_tools_batch(tasks, concurrency=3)

for i, result in enumerate(results):
    if result.get("success"):
        print(f"Task {i+1} succeeded: {result['task_id']}")
    else:
        print(f"Task {i+1} failed: {result.get('error')}")
```

### 3. Async Processing

```python
from thordata import AsyncThordataClient
import asyncio

async def scrape_multiple():
    client = AsyncThordataClient(
        scraper_token="your_token",
        public_token="your_public_token",
        public_key="your_public_key"
    )
    
    # Run multiple tasks concurrently
    tasks = [
        client.run_tool(Amazon.Search(keyword="laptop")),
        client.run_tool(GoogleMaps.Search(query="restaurants")),
        client.run_tool(YouTube.VideoInfo(video_id="jNQXAC9IVRw"))
    ]
    
    task_ids = await asyncio.gather(*tasks)
    
    # Wait for all to complete
    for task_id in task_ids:
        status = await client.wait_for_task(task_id)
        if status.lower() in {"ready", "success"}:
            result_url = await client.get_task_result(task_id)
            print(f"Result: {result_url}")
    
    await client.close()

asyncio.run(scrape_multiple())
```

## Common Use Cases

### 1. Price Monitoring

```python
# Monitor product prices
task_id = client.run_tool(Amazon.ProductByAsin(asin="B08N5WRWNW"))
status = client.wait_for_task(task_id)
if status.lower() == "ready":
    result_url = client.get_task_result(task_id)
    # Process result to extract price
```

### 2. Competitor Analysis

```python
# Search competitor products
competitors = ["laptop", "notebook", "ultrabook"]
tasks = [Amazon.Search(keyword=kw, domain="amazon.com") for kw in competitors]
results = client.run_tools_batch(tasks)
```

### 3. Location Data Collection

```python
# Collect location data
place_ids = ["ChIJPTacEpBQwokRKwIlDXelxkA", "ChIJ..."]
tasks = [GoogleMaps.DetailsByPlaceId(place_id=pid) for pid in place_ids]
results = client.run_tools_batch(tasks)
```

## Tips

1. **Use appropriate wait times**: Some tools take longer (e.g., Google Maps ~50s, Amazon ~7-15s)
2. **Handle failures gracefully**: Not all tasks succeed; check status before getting results
3. **Use batch processing**: More efficient for multiple tasks
4. **Check tool parameters**: Use `get_tool_info()` to see required/optional parameters
5. **Monitor quota**: Track usage with `get_usage_statistics()`

## Support

- Documentation: See individual tool docstrings
- Examples: Check `examples/tools/` directory
- Issues: Report on GitHub
