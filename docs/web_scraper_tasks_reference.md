# Thordata Web Scraper Tasks API Reference (Python SDK)

> **SDK Version**: 1.6.0  
> **Last Updated**: 2025-01-21

Thordata Web Scraper Tasks API provides pre-built scraping tools for 120+ platforms (Amazon, Google Maps, YouTube, TikTok, etc.). Tasks are created asynchronously and results are downloaded when ready.

## Endpoint & Authentication

- **Task Builder Endpoint**: `https://builderapi.thordata.com/web_scraper_api/create_task`
- **Video Builder Endpoint**: `https://builderapi.thordata.com/video_builder_api/create_task`
- **Status Endpoint**: `https://publicapi.thordata.com/api/web_scraper_api/get_task_status`
- **Download Endpoint**: `https://publicapi.thordata.com/api/web_scraper_api/get_task_result`
- **Authentication**: `scraper_token` (for task creation), `public_token` + `public_key` (for status/result)

## SDK Quick Start

### Using Pre-built Tools

```python
from thordata import ThordataClient
from thordata.tools import Amazon, GoogleMaps, YouTube

client = ThordataClient(
    scraper_token="your_scraper_token",
    public_token="your_public_token",
    public_key="your_public_key"
)

# Create a task using a pre-built tool
task_id = client.run_tool(
    Amazon.ProductByAsin(asin="B0BZYCJK89")
)

# Wait for completion
status = client.wait_for_task(task_id, max_wait=300)

# Get results
if status == "ready":
    download_url = client.get_task_result(task_id)
    print(f"Download: {download_url}")
```

### Manual Task Creation

```python
from thordata import ThordataClient, ScraperTaskConfig

client = ThordataClient(
    scraper_token="your_scraper_token",
    public_token="your_public_token",
    public_key="your_public_key"
)

# Create task configuration
config = ScraperTaskConfig(
    file_name="my_scrape_task",
    spider_id="amazon_product_by-url",
    spider_name="amazon.com",
    parameters=[{"url": "https://www.amazon.com/dp/B000000000"}],
    include_errors=True
)

# Create task
task_id = client.create_scraper_task_advanced(config)

# Wait and get results
status = client.wait_for_task(task_id, max_wait=600)
if status == "ready":
    download_url = client.get_task_result(task_id)
```

## Available Tools

### E-Commerce Platforms

- **Amazon**: Product by ASIN, URL, Keywords, Category, Best Sellers, Reviews, Sellers
- **eBay**: Product by URL, Category URL, Keywords, List URL
- **Walmart**: Product by URL, Category URL, SKU, Keywords, Zipcodes

### Social Media Platforms

- **TikTok**: Post, Profile, Posts by Keywords/Profile/List, Shop, Profiles by List
- **Instagram**: Profile, Post, Profile by URL, Post by URL, All Reel, Reel by List
- **Facebook**: Post Details, Event by List/Search/Events, Profile, Comment
- **Twitter/X**: Profile, Post, Profile by Username, Post by Profile URL
- **Reddit**: Posts, Comment, Posts by Keywords/Subreddit
- **LinkedIn**: Company, Job by URL/Keyword

### Search & Maps

- **Google Maps**: Details by URL, CID, Location, Place ID
- **Google Shopping**: Product by URL, Keywords
- **Google Play**: App Info, Reviews

### Video Platforms

- **YouTube**: Video Download, Audio Download, Subtitle Download, Video Info, Profile by URL, Video Post by URL/Search/Hashtag/Keyword/Explore

### Code Platforms

- **GitHub**: Repository by URL, Repository by Search URL

### Professional Platforms

- **Indeed**: Job by URL/Keyword, Company by URL/Keyword/Industry/List
- **Glassdoor**: Company by URL/Keywords/List/Input Filter, Job by URL/Keywords/List
- **Crunchbase**: Company by URL/Keywords

### Travel & Real Estate

- **Booking**: Hotel by URL
- **Zillow**: Price by URL, Product by URL/Filter/List URL
- **Airbnb**: Product by Search URL/Location/URL

See [Tool Coverage Matrix](TOOL_COVERAGE_MATRIX.md) for complete list.

## Task Lifecycle

### 1. Create Task

```python
# Using pre-built tool (recommended)
task_id = client.run_tool(Amazon.ProductByAsin(asin="B0BZYCJK89"))

# Or manually
task_id = client.create_scraper_task(
    file_name="task_name",
    spider_id="amazon_product_by-asin",
    spider_name="amazon.com",
    parameters=[{"asin": "B0BZYCJK89"}]
)
```

### 2. Check Status

```python
# Get current status
status = client.get_task_status(task_id)
print(f"Status: {status}")

# Wait for completion (with polling)
status = client.wait_for_task(
    task_id,
    poll_interval=5.0,  # Check every 5 seconds
    max_wait=600.0       # Maximum 10 minutes
)
```

### 3. Get Results

```python
# Get download URL
download_url = client.get_task_result(task_id, file_type="json")

# Download and parse
import requests
response = requests.get(download_url)
data = response.json()
```

## Task Status Values

- **`ready`**: Task completed successfully
- **`success`**: Task completed successfully (alias)
- **`finished`**: Task completed successfully (alias)
- **`failed`**: Task failed
- **`error`**: Task encountered an error
- **`cancelled`**: Task was cancelled
- **`running`**: Task is currently executing
- **`pending`**: Task is queued

## Video Tasks

Video tasks require `CommonSettings` for download configuration:

```python
from thordata import ThordataClient, CommonSettings
from thordata.tools import YouTube

client = ThordataClient(...)

settings = CommonSettings(
    resolution="<=360p",
    video_codec="vp9",
    audio_format="opus",
    bitrate="<=320",
    selected_only=False
)

task_id = client.run_tool(
    YouTube.VideoDownload(
        url="https://www.youtube.com/watch?v=jNQXAC9IVRw",
        common_settings=settings
    )
)
```

## Batch Operations

### List Tasks

```python
# Get task list
tasks = client.list_tasks(page=1, size=20)
print(f"Total tasks: {tasks['count']}")
for task in tasks['list']:
    print(f"Task {task['task_id']}: {task['status']}")
```

### Get Latest Task Status

```python
latest = client.get_latest_task_status()
print(f"Latest task: {latest.get('task_id')} - {latest.get('status')}")
```

## Error Handling

```python
from thordata import (
    ThordataClient,
    ThordataError,
    ThordataAuthError,
    ThordataAPIError
)

client = ThordataClient(...)

try:
    task_id = client.run_tool(Amazon.ProductByAsin(asin="B0BZYCJK89"))
    status = client.wait_for_task(task_id, max_wait=300)
    
    if status == "ready":
        download_url = client.get_task_result(task_id)
    else:
        print(f"Task failed with status: {status}")
        
except ThordataAuthError as e:
    print(f"Authentication error: {e}")
except ThordataAPIError as e:
    print(f"API error: {e}")
except ThordataError as e:
    print(f"SDK error: {e}")
```

## Output Format

Results are returned as download URLs. Download the file to get JSON data:

```json
{
  "spider_parameter": {
    "spider_id": "amazon_product_by-asin",
    "spider_name": "amazon.com",
    "parameters": [{"asin": "B0BZYCJK89"}]
  },
  "data": [
    {
      "title": "Product Title",
      "price": "$99.99",
      ...
    }
  ],
  "metadata": {
    "task_id": "xxx",
    "created_at": "2025-01-01T00:00:00Z",
    "status": "Ready"
  }
}
```

See [Output Format Alignment](OUTPUT_FORMAT_ALIGNMENT.md) for details.

## Best Practices

1. **Use Pre-built Tools**: Prefer `run_tool()` with tool classes over manual task creation
2. **Set Appropriate Timeouts**: Use `max_wait` based on expected task duration
3. **Poll Efficiently**: Use `poll_interval` to balance responsiveness and API calls
4. **Handle Errors**: Always check task status before downloading results
5. **Batch Processing**: Use `list_tasks()` to monitor multiple tasks

## Comparison with Other APIs

| Feature | Web Scraper Tasks | Universal API | Browser API |
|---------|------------------|---------------|-------------|
| **Setup Complexity** | Low (pre-built tools) | Medium | High (framework setup) |
| **Platform Coverage** | 120+ platforms | Any website | Any website |
| **Execution Model** | Async (task-based) | Sync/Async | Manual control |
| **Use Case** | Platform-specific scraping | General scraping | Complex automation |

## Summary

Web Scraper Tasks API provides the easiest way to scrape popular platforms with pre-built tools. Use it when you need:

- Quick setup for supported platforms
- Platform-specific optimizations
- Batch processing of multiple tasks
- Asynchronous task execution

For unsupported platforms or custom requirements, use Universal API or Browser API.
