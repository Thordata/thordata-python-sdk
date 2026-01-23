# Thordata Python SDK

<div align="center">

<img src="https://img.shields.io/badge/Thordata-AI%20Infrastructure-blue?style=for-the-badge" alt="Thordata Logo">

**The Official Python Client for Thordata APIs**

*Proxy Network • SERP API • Web Unlocker • Web Scraper API*

[![PyPI version](https://img.shields.io/pypi/v/thordata-sdk.svg?style=flat-square)](https://pypi.org/project/thordata-sdk/)
[![Python Versions](https://img.shields.io/pypi/pyversions/thordata-sdk.svg?style=flat-square)](https://pypi.org/project/thordata-sdk/)
[![License](https://img.shields.io/badge/license-MIT-green?style=flat-square)](LICENSE)
[![CI Status](https://img.shields.io/github/actions/workflow/status/Thordata/thordata-python-sdk/ci.yml?branch=main&style=flat-square)](https://github.com/Thordata/thordata-python-sdk/actions)

</div>

---

## 📖 Introduction

This SDK provides a robust, high-performance interface to Thordata's AI data infrastructure. It is designed for high-concurrency scraping, reliable proxy tunneling, and seamless data extraction.

**Key Features:**
*   **🚀 Production Ready:** Built on `urllib3` connection pooling for low-latency proxy requests.
*   **⚡ Async Support:** Native `aiohttp` client for high-concurrency SERP/Universal scraping.
*   **🛡️ Robust:** Handles TLS-in-TLS tunneling, retries, and error parsing automatically.
*   **✨ Developer Experience:** Fully typed (`mypy` compatible) with intuitive IDE autocomplete.
*   **🧩 Lazy Validation:** Only validate credentials for the features you actually use.

---

## 📦 Installation

```bash
pip install thordata-sdk
```

---

## 🔐 Configuration

Set environment variables to avoid hardcoding credentials. You only need to set the variables for the features you use.

```bash
# [Required for SERP & Web Unlocker]
export THORDATA_SCRAPER_TOKEN="your_token_here"

# [Required for Proxy Network]
export THORDATA_RESIDENTIAL_USERNAME="your_username"
export THORDATA_RESIDENTIAL_PASSWORD="your_password"
export THORDATA_PROXY_HOST="vpnXXXX.pr.thordata.net"

# [Required for Task Management]
export THORDATA_PUBLIC_TOKEN="public_token"
export THORDATA_PUBLIC_KEY="public_key"
```

---

## 🚀 Quick Start

### 1. SERP Search (Google/Bing/Yandex)

```python
from thordata import ThordataClient, Engine

client = ThordataClient()  # Loads THORDATA_SCRAPER_TOKEN from env

# Simple Search
print("Searching...")
results = client.serp_search("latest AI trends", engine=Engine.GOOGLE_NEWS)

for news in results.get("news_results", [])[:3]:
    print(f"- {news['title']} ({news['source']})")
```

### 2. Universal Scrape (Web Unlocker)

Bypass Cloudflare/Akamai and render JavaScript automatically.

```python
html = client.universal_scrape(
    url="https://example.com/protected-page",
    js_render=True,
    wait_for=".content-loaded",
    country="us"
)
print(f"Scraped {len(html)} bytes")
```

### 3. High-Performance Proxy

Use Thordata's residential IPs with automatic connection pooling.

```python
from thordata import ProxyConfig, ProxyProduct

# Config is optional if env vars are set, but allows granular control
proxy = ProxyConfig(
    product=ProxyProduct.RESIDENTIAL,
    country="jp",
    city="tokyo",
    session_id="session-001",
    session_duration=10  # Sticky IP for 10 mins
)

# Use the client to make requests (Reuses TCP connections)
response = client.get("https://httpbin.org/ip", proxy_config=proxy)
print(response.json())
```

---

## ⚙️ Advanced Usage

### Async Client (High Concurrency)

For building AI agents or high-throughput spiders.

```python
import asyncio
from thordata import AsyncThordataClient

async def main():
    async with AsyncThordataClient() as client:
        # Fire off multiple requests in parallel
        tasks = [
            client.serp_search(f"query {i}") 
            for i in range(5)
        ]
        results = await asyncio.gather(*tasks)
        print(f"Completed {len(results)} searches")

asyncio.run(main())
```

### Web Scraper API (Task Management)

Create and manage large-scale scraping tasks asynchronously.

```python
# 1. Create a task
task_id = client.create_scraper_task(
    file_name="daily_scrape",
    spider_id="universal",
    spider_name="universal",
    parameters={"url": "https://example.com"}
)

# 2. Wait for completion (Polling)
status = client.wait_for_task(task_id)

# 3. Get results
if status == "ready":
    url = client.get_task_result(task_id)
    print(f"Download Data: {url}")
```

---

## 🔥 Web Scraper Tools (High-Level API)

Stop guessing parameters! The SDK provides strongly-typed classes for 30+ popular websites including Amazon, Google, TikTok, Twitter, LinkedIn, and YouTube.

### Amazon Product Scraper
```python
from thordata.tools import Amazon

task_id = client.run_tool(
    Amazon.Product(asin="B08N5WRWNW", domain="amazon.co.uk")
)
```

### Google Maps Scraper
```python
from thordata.tools import GoogleMaps

task_id = client.run_tool(
    GoogleMaps.Details(url="https://www.google.com/maps/place/...")
)
```

### TikTok Profile Scraper
```python
from thordata.tools import TikTok

task_id = client.run_tool(
    TikTok.Profile(url="https://www.tiktok.com/@tiktok", country="us")
)
```

### YouTube Video Downloader
```python
from thordata.tools import YouTube
from thordata import CommonSettings

task_id = client.run_tool(
    YouTube.VideoDownload(
        url="https://youtu.be/...",
        common_settings=CommonSettings(resolution="1080p")
    )
)
```

## 📄 License

MIT License. See [LICENSE](LICENSE) for details.