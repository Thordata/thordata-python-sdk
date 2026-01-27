# Thordata Python SDK — Features & Usage (All-in-One)

> **Package**: `thordata-sdk`  
> **Repository**: `thordata-python-sdk`  
> **Python**: 3.9+  
> **Version**: 1.6.0

This document is the single entry point for the SDK capabilities and usage examples.

## Contents

1. [Quick Start](#quick-start)
2. [Authentication](#authentication)
3. [SERP API](#serp-api)
4. [Web Unlocker (Universal Scraping API)](#web-unlocker-universal-scraping-api)
5. [Browser API (Scraping Browser)](#browser-api-scraping-browser)
6. [Web Scraper Tasks (Pre-built Tools)](#web-scraper-tasks-pre-built-tools)
7. [Proxy Network](#proxy-network)
8. [Async Client](#async-client)
9. [Error Handling](#error-handling)
10. [Output Formats](#output-formats)
11. [Related Docs](#related-docs)

---

## Quick Start

```python
from thordata import ThordataClient

client = ThordataClient(
    scraper_token="YOUR_SCRAPER_TOKEN",
    public_token="YOUR_PUBLIC_TOKEN",
    public_key="YOUR_PUBLIC_KEY",
)

data = client.serp_search(query="pizza", engine="google", country="us")
print(len(data.get("organic", [])))
```

---

## Authentication

The SDK supports multiple credentials depending on which product you use:

- **SERP API**: `THORDATA_SCRAPER_TOKEN`
- **Web Unlocker (Universal)**: `THORDATA_SCRAPER_TOKEN`
- **Web Scraper Tasks**:
  - Create tasks: `THORDATA_SCRAPER_TOKEN`
  - Poll status / download: `THORDATA_PUBLIC_TOKEN` + `THORDATA_PUBLIC_KEY`
- **Browser API**: `THORDATA_BROWSER_USERNAME` + `THORDATA_BROWSER_PASSWORD`
- **Proxy Network**: product-specific username/password (e.g. `THORDATA_RESIDENTIAL_USERNAME`)

Recommended: set environment variables via `.env`.

---

## SERP API

### What it does

Fetch search results from search engines.

### Primary SDK entry points

- `ThordataClient.serp_search(...)`
- `ThordataClient.serp_search_advanced(SerpRequest)`
- `AsyncThordataClient.serp_search(...)`
- `AsyncThordataClient.serp_search_advanced(SerpRequest)`

### Example

```python
from thordata import ThordataClient, Engine

client = ThordataClient(scraper_token="YOUR_SCRAPER_TOKEN")

data = client.serp_search(
    query="latest AI trends",
    engine=Engine.GOOGLE,
    country="us",
    language="en",
    num=10,
)

for item in data.get("organic", []):
    print(item.get("title"), item.get("link"))
```

---

## Web Unlocker (Universal Scraping API)

### What it does

General web scraping with optional JavaScript rendering (Web Unlocker in Dashboard).

### Primary SDK entry points

- `ThordataClient.universal_scrape(...)`
- `ThordataClient.universal_scrape_advanced(UniversalScrapeRequest)`
- `AsyncThordataClient.universal_scrape(...)`
- `AsyncThordataClient.universal_scrape_advanced(UniversalScrapeRequest)`

### Example

```python
from thordata import ThordataClient

client = ThordataClient(scraper_token="YOUR_SCRAPER_TOKEN")

html = client.universal_scrape(
    url="https://example.com",
    js_render=True,
    output_format="html",
    country="us",
    wait_for=".content",
)
print(html[:200])
```

---

## Browser API (Scraping Browser)

### What it does

Provides a remote browser session endpoint for Playwright / Puppeteer / Selenium.

### Primary SDK entry points

- `ThordataClient.get_browser_connection_url(username=None, password=None)`
- `AsyncThordataClient.get_browser_connection_url(username=None, password=None)`

### Example (Playwright)

```python
import asyncio
from playwright.async_api import async_playwright
from thordata import ThordataClient

async def main():
    client = ThordataClient()
    ws_url = client.get_browser_connection_url()

    async with async_playwright() as pw:
        browser = await pw.chromium.connect_over_cdp(ws_url)
        try:
            page = await browser.new_page()
            await page.goto("https://example.com", timeout=120000)
            await page.screenshot(path="screenshot.png")
        finally:
            await browser.close()

asyncio.run(main())
```

---

## Web Scraper Tasks (Pre-built Tools)

### What it does

Create async scraping tasks using pre-built tools for popular platforms.

### Primary SDK entry points

- `ThordataClient.run_tool(tool_request, ...)`
- `ThordataClient.create_scraper_task(...)`
- `ThordataClient.create_scraper_task_advanced(ScraperTaskConfig)`
- `ThordataClient.wait_for_task(task_id, ...)`
- `ThordataClient.get_task_status(task_id)`
- `ThordataClient.get_task_result(task_id)`

### Example (Amazon tool)

```python
from thordata import ThordataClient
from thordata.tools import Amazon

client = ThordataClient(
    scraper_token="YOUR_SCRAPER_TOKEN",
    public_token="YOUR_PUBLIC_TOKEN",
    public_key="YOUR_PUBLIC_KEY",
)

task_id = client.run_tool(Amazon.ProductByAsin(asin="B0BZYCJK89"))
status = client.wait_for_task(task_id, max_wait=300)
if status.lower() == "ready":
    url = client.get_task_result(task_id)
    print(url)
```

---

## Proxy Network

### What it does

Route arbitrary HTTP(S) requests through Thordata proxies.

### Primary SDK entry points

- `ThordataClient.get(url, proxy_config=...)`
- `ThordataClient.post(url, proxy_config=...)`
- `ProxyConfig` / `ProxyProduct`

### Example

```python
from thordata import ThordataClient, ProxyConfig, ProxyProduct

client = ThordataClient()

proxy = ProxyConfig(product=ProxyProduct.RESIDENTIAL, country="us", session_duration=10)
resp = client.get("https://httpbin.org/ip", proxy_config=proxy)
print(resp.json())
```

---

## Async Client

```python
import asyncio
from thordata import AsyncThordataClient

async def main():
    async with AsyncThordataClient(scraper_token="YOUR_SCRAPER_TOKEN") as client:
        data = await client.serp_search(query="pizza", engine="google", country="us")
        print(len(data.get("organic", [])))

asyncio.run(main())
```

---

## Error Handling

```python
from thordata import ThordataClient
from thordata.exceptions import ThordataError, ThordataAuthError

client = ThordataClient(scraper_token="YOUR_SCRAPER_TOKEN")

try:
    client.serp_search(query="pizza", engine="google", country="us")
except ThordataAuthError as e:
    print("Auth error:", e)
except ThordataError as e:
    print("SDK error:", e)
```

---

## Output Formats

- Task APIs return a download URL via `get_task_result()`.
- Downloaded JSON structure is aligned with Dashboard.

See: [OUTPUT_FORMAT_ALIGNMENT.md](./OUTPUT_FORMAT_ALIGNMENT.md)

---

## Related Docs

- [Docs Index](./README.md)
- [API Alignment Summary](./API_ALIGNMENT_SUMMARY.md)
- [SERP Reference](./serp_reference.md)
- [Universal Reference](./universal_reference.md)
- [Browser Reference](./browser_reference.md)
- [Web Scraper Tasks Reference](./web_scraper_tasks_reference.md)
