# Thordata Python SDK

<h4 align="center">
  Official Python client for Thordata's Proxy Network, SERP API, Universal Scraping API, and Web Scraper API.
  <br>
  <i>Async-ready, built for AI agents and large-scale data collection.</i>
</h4>

<p align="center">
  <a href="https://github.com/Thordata/thordata-python-sdk/actions/workflows/ci.yml">
    <img src="https://github.com/Thordata/thordata-python-sdk/actions/workflows/ci.yml/badge.svg" alt="CI">
  </a>
  <a href="https://pypi.org/project/thordata-sdk/">
    <img src="https://img.shields.io/pypi/v/thordata-sdk?color=blue" alt="PyPI version">
  </a>
  <a href="https://github.com/Thordata/thordata-python-sdk/blob/main/LICENSE">
    <img src="https://img.shields.io/badge/license-Apache%202.0-green" alt="License">
  </a>
  <a href="https://python.org">
    <img src="https://img.shields.io/badge/python-3.8+-blue" alt="Python Versions">
  </a>
</p>

---

## Installation

```bash
pip install thordata-sdk
```

## Quick Start

All examples below use the unified client:

```python
from thordata import ThordataClient, AsyncThordataClient
```

You can copy `examples/.env.example` to `.env` and fill in your tokens from the Thordata Dashboard.

### 1. Proxy Network (Simple GET)

```python
import os
from dotenv import load_dotenv
from thordata import ThordataClient

load_dotenv()

client = ThordataClient(
    scraper_token=os.getenv("THORDATA_SCRAPER_TOKEN"),
    public_token=os.getenv("THORDATA_PUBLIC_TOKEN"),
    public_key=os.getenv("THORDATA_PUBLIC_KEY"),
)

resp = client.get("http://httpbin.org/ip")
print(resp.json())
```

### 2. SERP API (Google, Bing, Yandex, DuckDuckGo)

```python
from thordata import ThordataClient, Engine

client = ThordataClient("SCRAPER_TOKEN", "PUBLIC_TOKEN", "PUBLIC_KEY")

results = client.serp_search(
    query="Thordata technology",
    engine=Engine.GOOGLE,
    num=10,
    # Any engine-specific parameters are passed via **kwargs
    # e.g. type="shopping", location="United States"
)

print(len(results.get("organic", [])))
```

### 3. Universal Scraping API

```python
from thordata import ThordataClient

client = ThordataClient("SCRAPER_TOKEN", "PUBLIC_TOKEN", "PUBLIC_KEY")

html = client.universal_scrape(
    url="https://www.google.com",
    js_render=True,
    output_format="HTML",
)
print(html[:200])
```

### 4. Web Scraper API (Task-based)

```python
import time
from thordata import ThordataClient

client = ThordataClient("SCRAPER_TOKEN", "PUBLIC_TOKEN", "PUBLIC_KEY")

task_id = client.create_scraper_task(
    file_name="demo_youtube_data",
    spider_id="youtube_video-post_by-url",
    spider_name="youtube.com",
    individual_params={
        "url": "https://www.youtube.com/@stephcurry/videos",
        "order_by": "",
        "num_of_posts": ""
    },
)

for _ in range(10):
    status = client.get_task_status(task_id)
    print("Status:", status)
    if status in ["Ready", "Success"]:
        break
    if status == "Failed":
        raise RuntimeError("Task failed")
    time.sleep(3)

download_url = client.get_task_result(task_id)
print("Download URL:", download_url)
```

### 5. Asynchronous Usage (High Concurrency)

```python
import asyncio
from thordata import AsyncThordataClient

async def main():
    async with AsyncThordataClient(
        scraper_token="SCRAPER_TOKEN",
        public_token="PUBLIC_TOKEN",
        public_key="PUBLIC_KEY",
    ) as client:
        resp = await client.get("http://httpbin.org/ip")
        print(await resp.json())

asyncio.run(main())
```

More examples are available in the `examples/` directory.

---

## Features

| Feature | Status | Description |
|---------|--------|-------------|
| Proxy Network | Stable | Residential, ISP, Mobile, Datacenter via HTTP/HTTPS gateway. |
| SERP API | Stable | Google / Bing / Yandex / DuckDuckGo, flexible parameters. |
| Universal Scraping API | Stable | JS rendering, HTML / PNG output, antibot bypass. |
| Web Scraper API | Stable | Task-based scraping for complex sites (YouTube, E-commerce). |
| Async Client | Stable | aiohttp-based client for high-concurrency workloads. |

---

## Development & Contributing

See `CONTRIBUTING.md` for local development and contribution guidelines.

## License

This project is licensed under the Apache License 2.0.

## Support

For technical support, please contact support@thordata.com
or verify your tokens and quotas in the Thordata Dashboard.