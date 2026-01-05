# Thordata Python SDK

<div align="center">

**Official Python Client for Thordata APIs**

*Proxy Network • SERP API • Web Unlocker • Web Scraper API*

[![PyPI version](https://img.shields.io/pypi/v/thordata-sdk.svg)](https://pypi.org/project/thordata-sdk/)
[![Python Versions](https://img.shields.io/pypi/pyversions/thordata-sdk.svg)](https://pypi.org/project/thordata-sdk/)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)

</div>

---

## 📦 Installation

```bash
pip install thordata-sdk
```

Optional dependencies for Scraping Browser examples:
```bash
pip install playwright
```

## 🔐 Configuration

Set the following environment variables (recommended):

```bash
# Required for SERP, Universal, and Proxy Network
export THORDATA_SCRAPER_TOKEN="your_scraper_token"

# Required for Web Scraper Tasks & Account Management
export THORDATA_PUBLIC_TOKEN="your_public_token"
export THORDATA_PUBLIC_KEY="your_public_key"

# Optional: Default Proxy Credentials (for Proxy Network)
export THORDATA_RESIDENTIAL_USERNAME="user"
export THORDATA_RESIDENTIAL_PASSWORD="pass"
```

## 🚀 Quick Start

```python
from thordata import ThordataClient

# Initialize (credentials loaded from env)
client = ThordataClient(scraper_token="...") 

# 1. SERP Search
print("--- SERP Search ---")
results = client.serp_search("python tutorial", engine="google")
print(f"Title: {results['organic'][0]['title']}")

# 2. Universal Scrape (Web Unlocker)
print("\n--- Universal Scrape ---")
html = client.universal_scrape("https://httpbin.org/html")
print(f"HTML Length: {len(html)}")
```

## 📚 Core Features

### 🌐 Proxy Network

Easily generate proxy URLs with geo-targeting and sticky sessions. The SDK handles connection pooling automatically.

```python
from thordata import ProxyConfig, ProxyProduct

# Create a proxy configuration
proxy = ProxyConfig(
    username="user",
    password="pass",
    product=ProxyProduct.RESIDENTIAL,
    country="us",
    city="new_york",
    session_id="session123",
    session_duration=10  # Sticky for 10 mins
)

# Use with the client (high performance)
response = client.get("https://httpbin.org/ip", proxy_config=proxy)
print(response.json())

# Or get the URL string for other libs (requests, scrapy, etc.)
proxy_url = proxy.build_proxy_url()
print(f"Proxy URL: {proxy_url}")
```

### 🔍 SERP API

Real-time search results from Google, Bing, Yandex, etc.

```python
from thordata import SerpRequest, Engine

# Simple
results = client.serp_search(
    query="pizza near me",
    engine=Engine.GOOGLE_MAPS,
    country="us"
)

# Advanced (Strongly Typed)
request = SerpRequest(
    query="AI news",
    engine="google_news",
    num=50,
    time_filter="week",
    location="San Francisco",
    render_js=True
)
results = client.serp_search_advanced(request)
```

### 🔓 Universal Scraping API (Web Unlocker)

Bypass Cloudflare, CAPTCHAs, and antibot systems.

```python
html = client.universal_scrape(
    url="https://example.com/protected",
    js_render=True,
    wait_for=".content",
    country="gb",
    output_format="html"
)
```

### 🕷️ Web Scraper API (Async Tasks)

Manage asynchronous scraping tasks for massive scale.

```python
# 1. Create Task
task_id = client.create_scraper_task(
    file_name="my_task",
    spider_id="universal",
    spider_name="universal",
    parameters={"url": "https://example.com"}
)
print(f"Task Created: {task_id}")

# 2. Wait for Completion
status = client.wait_for_task(task_id, max_wait=600)

# 3. Get Result
if status == "ready":
    download_url = client.get_task_result(task_id)
    print(f"Result: {download_url}")
```

### 📹 Video/Audio Tasks

Download content from YouTube and other supported platforms.

```python
from thordata import CommonSettings

task_id = client.create_video_task(
    file_name="video_{{VideoID}}",
    spider_id="youtube_video_by-url",
    spider_name="youtube.com",
    parameters={"url": "https://youtube.com/watch?v=..."},
    common_settings=CommonSettings(resolution="1080p")
)
```

### 📊 Account Management

Access usage statistics, manage sub-users, and whitelist IPs.

```python
# Get Usage Stats
stats = client.get_usage_statistics("2024-01-01", "2024-01-31")
print(f"Balance: {stats.balance_gb():.2f} GB")

# List Proxy Users
users = client.list_proxy_users()
print(f"Active Sub-users: {users.user_count}")

# Whitelist IP
client.add_whitelist_ip("1.2.3.4")
```

## ⚙️ Advanced Usage

### Async Client

For high-concurrency applications, use `AsyncThordataClient`.

```python
import asyncio
from thordata import AsyncThordataClient

async def main():
    async with AsyncThordataClient(scraper_token="...") as client:
        # SERP
        results = await client.serp_search("async python")
        
        # Universal
        html = await client.universal_scrape("https://example.com")

asyncio.run(main())
```

Note: `AsyncThordataClient` does not support HTTPS proxy tunneling (TLS-in-TLS) due to `aiohttp` limitations. For proxy network requests, use the sync client.

### Custom Retry Configuration

```python
from thordata import RetryConfig

retry = RetryConfig(
    max_retries=5,
    backoff_factor=1.5,
    retry_on_status_codes={429, 500, 502, 503, 504}
)

client = ThordataClient(..., retry_config=retry)
```

## 📄 License

MIT License