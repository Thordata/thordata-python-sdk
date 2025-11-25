# Thordata Python SDK

<h4 align="center">
  The Official Python Client for the Thordata Proxy Network & Web Scraper API.
  <br>
  <i>High-performance, async-ready, designed for AI Agents and large-scale data collection.</i>
</h4>

<p align="center">
  <a href="https://pypi.org/project/thordata-sdk/"><img src="https://img.shields.io/pypi/v/thordata-sdk?color=blue" alt="PyPI version"></a>
  <a href="https://github.com/Thordata/thordata-python-sdk/blob/main/LICENSE"><img src="https://img.shields.io/badge/license-Apache%202.0-green" alt="License"></a>
  <a href="https://python.org"><img src="https://img.shields.io/badge/python-3.8+-blue" alt="Python Versions"></a>
</p>

---

## 🛠 Installation

Install via pip:

```bash
pip install thordata-sdk
```

## ⚡ Quick Start

### 1. Proxy Usage (Simple GET Request)

**Python**

```python
from thordata_sdk import ThordataClient

# Initialize with your credentials from the Thordata Dashboard
client = ThordataClient(
    scraper_token="YOUR_SCRAPER_TOKEN", # From "Scraping Tool Token"
    public_token="YOUR_PUBLIC_TOKEN",   # From "Public API"
    public_key="YOUR_PUBLIC_KEY"        # From "Public API"
)

# Send a request through the proxy
response = client.get("http://httpbin.org/ip")
print(response.json())
```

### 2. Real-time SERP Search

**Python**

```python
results = client.serp_search("Thordata technology", engine="google")
print(f"Results found: {len(results.get('organic', []))}")
```

### 3. Asynchronous Usage (High Concurrency)

**Python**

```python
import asyncio
from thordata_sdk import AsyncThordataClient

async def main():
    async with AsyncThordataClient(scraper_token="...", public_token="...", public_key="...") as client:
        response = await client.get("http://httpbin.org/ip")
        print(await response.json())

asyncio.run(main())
```

## ⚙️ Features Status

| Feature | Status | Description |
|---------|--------|-------------|
| Proxy Network | ✅ Stable | Synchronous & Asynchronous support via aiohttp. |
| SERP API | ✅ Stable | Real-time Google/Bing/Yandex search results. |
| Web Scraper | ✅ Stable | Async task management for scraping complex sites (e.g., YouTube). |
| Authentication | ✅ Secure | Dual-token system for enhanced security. |

## 📄 License

This project is licensed under the Apache License 2.0.

## 📞 Support

For technical assistance, please contact support@thordata.com or verify your tokens in the Thordata Dashboard.