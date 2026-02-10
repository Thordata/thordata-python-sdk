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

The **Thordata Python SDK v1.8.4** is a production-ready wrapper for Thordata's AI data infrastructure. It is architected for high reliability, strict type safety, and maximum performance.

**Highlights**
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

### 🔄 Loading `.env` in your project

The SDK **does not automatically load** a `.env` file. If you keep your
credentials in a local `.env`, you have two options:

- Use `python-dotenv`:

```python
from dotenv import load_dotenv

load_dotenv()  # loads ./.env by default
```

- Or use the built‑in lightweight helper (no extra dependency):

```python
from thordata import load_env_file

load_env_file()  # loads ./.env if present, without overriding existing env vars
```

This keeps import side effects predictable while still making local development
 ergonomic.

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

### Web Scraper Tools (100+ Pre-built Tools)

Use pre-built tools for popular platforms. To inspect the full set of tools at runtime, call `client.list_tools()` or consult the Web Scraper section in the official documentation.

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

### 🔍 Discovering Available Web Scraper Tools

You can introspect all available tools and groups directly from the SDK:

```python
from thordata import ThordataClient

client = ThordataClient()

# List all tools with basic metadata
tools = client.list_tools()
print(f"Total tools: {tools['meta']['total']}")

# Group summary (e.g. ecommerce / social / video / search / professional / travel)
groups = client.get_tool_groups()
for g in groups["groups"]:
    print(g["id"], g["count"])

# Search tools by keyword (in key / spider_id / spider_name)
google_tools = client.search_tools("google")
for t in google_tools["tools"][:5]:
    print(t["key"], "->", t.get("spider_id"))
```

This is the recommended way to explore new tools without leaving your IDE.

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

### Running Tests

```bash
# Run all unit tests
pytest

# Run with coverage
coverage run -m pytest && coverage report -m

# Run integration tests (requires real credentials)
THORDATA_INTEGRATION=true pytest -m integration -v

# Run specific test file
pytest tests/test_tools_registry.py -v

# Run specific test class
pytest tests/test_integration_full.py::TestSerpIntegration -v
```

### Test Coverage

The SDK includes comprehensive test coverage:

- **Unit Tests**: Tests core logic, models, and utilities without network dependencies
- **Integration Tests**: Tests real API connectivity and functionality (requires `THORDATA_INTEGRATION=true`)
- **Registry Tests**: Tests tool discovery and caching mechanisms
- **Connectivity Tests**: Tests proxy and API connectivity across all modules

### Architecture Notes

The SDK is built with a shared internal API layer to ensure consistency between sync and async clients:

- **Shared Base Layer**: `src/thordata/_api_base.py` contains common logic for URL construction, header building, and validation
- **Caching**: Tools registry uses caching to avoid repeated reflection overhead
- **Unified .env Loading**: Uses `thordata.env.load_env_file` consistently across all modules
- **Type Safety**: Full type annotations throughout the codebase for excellent IDE support

### 🧩 Local Self‑Check Flow (Developer Checklist)

Complete end-to-end acceptance flow to ensure all core features work correctly:

#### 1. Environment Setup

```bash
# Copy environment variable template
cp .env.example .env

# Edit .env and fill in your real credentials:
# - THORDATA_SCRAPER_TOKEN
# - THORDATA_PUBLIC_TOKEN
# - THORDATA_PUBLIC_KEY
# - THORDATA_RESIDENTIAL_USERNAME / PASSWORD
# - THORDATA_BROWSER_USERNAME / PASSWORD (optional, for Browser API)
```

#### 2. Upstream Proxy Configuration (Optional, if using Clash)

If you are using a local proxy such as Clash, configure upstream proxy:

```bash
# Method 1: HTTPS proxy (recommended, port 7899)
export THORDATA_UPSTREAM_PROXY="https://127.0.0.1:7899"

# Method 2: SOCKS5 proxy (port 7898)
export THORDATA_UPSTREAM_PROXY="socks5://127.0.0.1:7898"
```

Or add to `.env` file:
```bash
THORDATA_UPSTREAM_PROXY=https://127.0.0.1:7899
```

#### 3. Quick Validation (Recommended First Step)

**✅ Step 0: Environment Validation**
```bash
python examples/validate_env.py
```
Validates all credential configurations and provides helpful error messages.

**✅ Step 0.5: Quick Start Test**
```bash
python examples/quick_start.py
```
Fast validation of all core features (completes in ~11 seconds).

#### 4. Core Feature Acceptance (Execute in order)

**✅ Step 1: Proxy Network Acceptance**
```bash
python examples/demo_proxy_network.py
```
Verify proxy network works correctly, including connections through upstream proxies like Clash.

**✅ Step 2: SERP API Acceptance**
```bash
python examples/demo_serp_api.py
```
Verify Google/Bing search API works correctly.

**✅ Step 3: Universal Scrape Acceptance**
```bash
python examples/demo_universal.py
```
Verify Web Unlocker functionality works correctly.

**✅ Step 4: Web Scraper API Acceptance (Complete Workflow)**
```bash
python examples/demo_web_scraper_api.py
```
Complete demonstration from task creation → waiting for completion → result retrieval.

**✅ Step 5: Multi-Spider ID Acceptance (Comprehensive)**
```bash
python examples/demo_web_scraper_multi_spider.py
```
Tests multiple spider IDs across different categories (E-commerce, Search, Video).

**✅ Step 6: Browser API Acceptance (One-Click)**
```bash
# First install Playwright
pip install thordata[browser]
playwright install chromium

# Run acceptance script
python examples/demo_browser_api.py
```
Verify Browser API connection, navigation, screenshots, and other basic functions.

#### 5. Full Acceptance Test (Optional)

For deeper coverage, run the full acceptance suite:

```bash
# Set integration test flag
export THORDATA_INTEGRATION=true

# Run full acceptance test
python examples/full_acceptance_test.py
```

#### 6. Acceptance Script Reference

| Script | Function | Required Credentials |
|--------|----------|---------------------|
| `validate_env.py` | Environment validation | None (checks config) |
| `quick_start.py` | Quick acceptance test | Scraper Token + Public Token/Key |
| `demo_proxy_network.py` | Proxy network connectivity test | Residential account |
| `demo_serp_api.py` | SERP search API | Scraper Token |
| `demo_universal.py` | Universal Scrape | Scraper Token |
| `demo_web_scraper_api.py` | Web Scraper complete workflow | Scraper Token + Public Token/Key |
| `demo_web_scraper_multi_spider.py` | Multi-spider ID testing | Scraper Token + Public Token/Key |
| `demo_browser_api.py` | Browser API one-click acceptance | Scraper Token + Browser account |
| `full_acceptance_test.py` | Complete feature suite | All credentials |

#### 7. Troubleshooting

If an acceptance script fails:

1. **Proxy Network Issues**:
   - Ensure Clash is running
   - Check if `THORDATA_UPSTREAM_PROXY` configuration is correct
   - Try direct connection (without upstream proxy) for testing

2. **API Authentication Issues**:
   - Verify credentials in `.env` file are correct
   - Check if credentials have expired

3. **Browser API Issues**:
   - Ensure `playwright` is installed: `pip install thordata[browser]`
   - Ensure browser is installed: `playwright install chromium`
   - Check if browser credentials are correct

All acceptance scripts output detailed error messages and troubleshooting tips.

---

## 📄 License

MIT License. See [LICENSE](LICENSE) for details.