# Thordata Python SDK

<div align="center">

**Official Python client for Thordata's Proxy Network, SERP API, Web Unlocker, and Web Scraper API.**

*Async-ready, type-safe, built for AI agents and large-scale data collection.*

[![PyPI](https://img.shields.io/pypi/v/thordata-sdk?color=blue)](https://pypi.org/project/thordata-sdk/)
[![Python](https://img.shields.io/badge/python-3.9+-blue)](https://python.org)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)

[Documentation](https://doc.thordata.com) • [Dashboard](https://www.thordata.com) • [Examples](examples/)

</div>

---

## ✨ Features

- 🌐 **Proxy Network**: Residential, Mobile, Datacenter, ISP proxies with geo-targeting
- 🔍 **SERP API**: Google, Bing, Yandex, DuckDuckGo search results
- 🔓 **Web Unlocker**: Bypass Cloudflare, CAPTCHAs, anti-bot systems
- 🕷️ **Web Scraper API**: Async task-based scraping (Text & Video/Audio)
- 📊 **Account Management**: Usage stats, sub-users, IP whitelist
- ⚡ **Async Support**: Full async/await support with aiohttp
- 🔄 **Auto Retry**: Configurable retry with exponential backoff

---

## 📦 Installation

```bash
pip install thordata-sdk
```

---

## 🔐 Configuration

Set environment variables:

```bash
# Required for Scraper APIs (SERP, Universal, Tasks)
export THORDATA_SCRAPER_TOKEN=your_token

# Required for Public/Location APIs (Dashboard -> My Account)
export THORDATA_PUBLIC_TOKEN=your_public_token
export THORDATA_PUBLIC_KEY=your_public_key

# Required for Public API NEW (Dashboard -> Public API NEW)
# If not set, SDK falls back to PUBLIC_TOKEN/KEY
export THORDATA_SIGN=your_sign
export THORDATA_API_KEY=your_api_key
```

---

## 🚀 Quick Start

```python
from thordata import ThordataClient, Engine

# Initialize (reads from env vars)
client = ThordataClient(
    scraper_token="your_token", 
    public_token="pub_token", 
    public_key="pub_key"
)

# SERP Search
results = client.serp_search("python tutorial", engine=Engine.GOOGLE)
print(f"Found {len(results.get('organic', []))} results")

# Universal Scrape
html = client.universal_scrape("https://httpbin.org/html")
print(html[:100])
```

---

## 📖 Feature Guide

### SERP API

```python
from thordata import SerpRequest

# Advanced search
results = client.serp_search_advanced(SerpRequest(
    query="pizza",
    engine="google_local",
    country="us",
    location="New York",
    num=10
))
```

### Web Scraper API (Async Tasks)

**Create Task:**
```python
task_id = client.create_scraper_task(
    file_name="my_task",
    spider_id="universal",
    spider_name="universal",
    parameters={"url": "https://example.com"}
)
```

**Video Download (New):**
```python
from thordata import CommonSettings

task_id = client.create_video_task(
    file_name="{{VideoID}}",
    spider_id="youtube_video_by-url",
    spider_name="youtube.com",
    parameters={"url": "https://youtube.com/watch?v=..."},
    common_settings=CommonSettings(resolution="1080p")
)
```

**Wait & Download:**
```python
status = client.wait_for_task(task_id)
if status == "ready":
    url = client.get_task_result(task_id)
    print(url)
```

### Account Management

```python
# Usage Statistics
stats = client.get_usage_statistics("2024-01-01", "2024-01-31")
print(f"Balance: {stats.balance_gb():.2f} GB")

# Proxy Users
users = client.list_proxy_users()
print(f"Sub-users: {users.user_count}")

# Whitelist IP
client.add_whitelist_ip("1.2.3.4")
```

### Proxy Network

```python
from thordata import ProxyConfig

# Generate Proxy URL
proxy_url = client.build_proxy_url(
    username="proxy_user",
    password="proxy_pass",
    country="us",
    city="ny"
)

# Use with requests
import requests
requests.get("https://httpbin.org/ip", proxies={"http": proxy_url, "https": proxy_url})
```

---

## 📄 License

MIT License