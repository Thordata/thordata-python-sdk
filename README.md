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

The **Thordata Python SDK v1.6.0** is a production-ready wrapper for Thordata's AI data infrastructure. It is architected for high reliability, strict type safety, and maximum performance.

**Why v1.6.0?**
*   **🛡️ Bulletproof Networking**: Custom core handles `HTTP`, `HTTPS`, and `SOCKS5h` (Remote DNS) tunneling, solving common SSL/TLS handshake issues in complex network environments.
*   **⚡ Async First**: First-class `asyncio` support with `aiohttp` for high-concurrency scraping (1000+ RPS).
*   **🧩 100% API Coverage**: Every endpoint documented by Thordata (including Hourly Usage, Server Monitor, and Task Management) is implemented.
*   **🤖 Type Safe**: Fully typed (`mypy` strict) for excellent IDE autocompletion and error checking.

---

## 📦 Installation

```bash
pip install thordata-sdk
```

---

## 🔐 Configuration

Set environment variables to avoid hardcoding credentials. **Full reference:** copy [.env.example](.env.example) to `.env` and fill in values.

```bash
# [Scraping APIs]
export THORDATA_SCRAPER_TOKEN="your_scraper_token"

# [Management APIs]
export THORDATA_PUBLIC_TOKEN="your_public_token"
export THORDATA_PUBLIC_KEY="your_public_key"

# [Proxy: Residential / Unlimited / Datacenter / Mobile / ISP]
export THORDATA_RESIDENTIAL_USERNAME="your_username"
export THORDATA_RESIDENTIAL_PASSWORD="your_password"
# Optional: Unlimited (high-bandwidth) if your plan has separate credentials
# export THORDATA_UNLIMITED_USERNAME="..."
# export THORDATA_UNLIMITED_PASSWORD="..."

# Optional: Upstream proxy when behind firewall (e.g. Clash Verge port 7897)
# export THORDATA_UPSTREAM_PROXY="http://127.0.0.1:7897"
```

Default proxy port is **9999** (residential); other products use different ports (see `.env.example`).

---

## 🚀 Quick Start

### 1. SERP Search (Google/Bing)

```python
from thordata import ThordataClient, Engine

client = ThordataClient() 

# Search Google
results = client.serp_search(
    query="latest AI trends",
    engine=Engine.GOOGLE,
    num=10,
    location="United States"
)

for item in results.get("organic", []):
    print(f"{item['title']} - {item['link']}")
```

### 2. Universal Scrape (Web Unlocker)

Automatically handles JS rendering, CAPTCHAs, and fingerprinting.

```python
html = client.universal_scrape(
    url="https://example.com",
    js_render=True,
    country="us",
    wait_for=".content-loaded"  # Smart waiting
)
```

### 3. High-Performance Proxy Tunneling

Use Thordata's residential IPs directly with `requests` (Sync) or `aiohttp` (Async). The SDK handles the complex authentication and rotation logic.

```python
from thordata import ProxyConfig, ProxyProduct

# Config is optional if env vars are set
proxy = ProxyConfig(
    product=ProxyProduct.RESIDENTIAL,
    country="jp",
    session_duration=10  # Sticky IP for 10 mins
)

# The client automatically routes this through Thordata's network
response = client.get("https://httpbin.org/ip", proxy_config=proxy)
print(response.json())
```

---

## ⚙️ Advanced Usage

### Async High-Concurrency

Perfect for building high-throughput AI agents.

```python
import asyncio
from thordata import AsyncThordataClient

async def main():
    async with AsyncThordataClient() as client:
        # Fire off 10 requests in parallel
        tasks = [client.serp_search(f"query {i}") for i in range(10)]
        results = await asyncio.gather(*tasks)
        print(f"Completed {len(results)} searches")

asyncio.run(main())
```

### Task Management (Batch Scraping)

Handle large-scale scraping jobs asynchronously.

```python
# 1. Create a task
task_id = client.create_scraper_task(
    file_name="daily_scrape",
    spider_id="universal",
    spider_name="universal",
    parameters={"url": "https://example.com"}
)

# 2. Poll for completion (Helper method)
status = client.wait_for_task(task_id, max_wait=600)

# 3. Download results
if status == "finished":
    data_url = client.get_task_result(task_id)
    print(f"Download: {data_url}")
```

### Web Scraper Tools (120+ Pre-built Tools)

Use pre-built tools for popular platforms. See [Tool Coverage Matrix](docs/TOOL_COVERAGE_MATRIX.md) for full list.

```python
from thordata import ThordataClient
from thordata.tools import Amazon, GoogleMaps, YouTube, TikTok, eBay, Walmart

client = ThordataClient()

# Amazon Product by ASIN
task_id = client.run_tool(Amazon.ProductByAsin(asin="B0BZYCJK89"))

# Google Maps by Place ID
task_id = client.run_tool(GoogleMaps.DetailsByPlaceId(place_id="ChIJPTacEpBQwokRKwIlDXelxkA"))

# YouTube Video Download
from thordata import CommonSettings
settings = CommonSettings(resolution="<=360p", video_codec="vp9")
task_id = client.run_tool(YouTube.VideoDownload(
    url="https://www.youtube.com/watch?v=jNQXAC9IVRw",
    common_settings=settings
))

# Wait and get results
status = client.wait_for_task(task_id, max_wait=300)
if status == "ready":
    download_url = client.get_task_result(task_id)
    print(f"Results: {download_url}")
```

**Available Platforms:**
- **E-Commerce**: Amazon, eBay, Walmart
- **Social Media**: TikTok, Instagram, Facebook, Twitter/X, Reddit, LinkedIn
- **Search**: Google Maps, Google Shopping, Google Play
- **Video**: YouTube (download, info, subtitles)
- **Code**: GitHub
- **Professional**: Indeed, Glassdoor, Crunchbase
- **Travel/Real Estate**: Booking, Airbnb, Zillow

See `examples/tools/` for more examples.

---

## 🛠️ Management APIs

Manage your infrastructure programmatically.

```python
# Check Balance
balance = client.get_traffic_balance()

# Manage Whitelist
client.add_whitelist_ip("1.2.3.4")

# Create Sub-users
client.create_proxy_user("new_user", "pass123", traffic_limit=500)

# Monitor Unlimited Proxies
monitor = client.unlimited.get_server_monitor(
    ins_id="ins-123", 
    region="us", 
    start_time=1700000000, 
    end_time=1700003600
)
```

---

## 🧪 Development & Testing

- **Full env reference**: Copy [.env.example](.env.example) to `.env` and fill in credentials.
- **Unit tests** (no network): `pytest` or `python -m coverage run -m pytest -p no:cov tests && python -m coverage report -m`
- **Integration tests** (live API/proxy): Set `THORDATA_INTEGRATION=true` in `.env`; optional `THORDATA_UPSTREAM_PROXY` (e.g. Clash) if behind a firewall. See [CONTRIBUTING.md](CONTRIBUTING.md#-testing-guidelines).

---

## 📄 License

MIT License. See [LICENSE](LICENSE) for details.