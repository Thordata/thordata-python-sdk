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

## Overview

The **Thordata Python SDK** is an officially supported client library for Thordata APIs:
SERP, Universal Scrape (Web Unlocker), Web Scraper Tasks, and Proxy Network.

## Installation

```bash
pip install thordata-sdk
```

## Configuration

Use environment variables (recommended). For local development, copy
[.env.example](.env.example) to `.env` and fill in values (**never commit `.env`**).

```bash
# [Scraping APIs]
export THORDATA_SCRAPER_TOKEN="your_scraper_token"

# [Management APIs]
export THORDATA_PUBLIC_TOKEN="your_public_token"
export THORDATA_PUBLIC_KEY="your_public_key"

# [Proxy: Residential / Unlimited / Datacenter / Mobile / ISP]
export THORDATA_RESIDENTIAL_USERNAME="your_username"
export THORDATA_RESIDENTIAL_PASSWORD="your_password"
```

### Loading `.env` (optional)

The SDK does not automatically load a `.env` file. If you want `.env` support:

```python
from thordata import load_env_file

load_env_file()  # loads ./.env if present, without overriding existing env vars
```

## Quick Start

### SERP Search

```python
from thordata import Engine, ThordataClient

client = ThordataClient()
results = client.serp_search(query="latest AI trends", engine=Engine.GOOGLE, num=10)
for item in results.get("organic", []):
    print(item.get("title"), item.get("link"))
```

### Universal Scrape

```python
from thordata import ThordataClient

client = ThordataClient()
html = client.universal_scrape(url="https://example.com", js_render=True, country="us")
print(type(html), len(str(html)))
```

### Web Scraper Tools

```python
from thordata import ThordataClient
from thordata.tools import Amazon

client = ThordataClient()
task_id = client.run_tool(Amazon.ProductByAsin(asin="B0BZYCJK89"))
status = client.wait_for_task(task_id, max_wait=300)
if status == "ready":
    print(client.get_task_result(task_id))
```

See `examples/` for more runnable scripts.

## Documentation

- `docs/README.md` (index)
- `docs/SDK_FEATURES_AND_USAGE.md`
- `docs/serp_reference.md`
- `docs/universal_reference.md`
- `docs/browser_reference.md`
- `docs/web_scraper_tasks_reference.md`

## Development & Testing

```bash
pip install -e ".[dev]"
ruff check src tests examples
black --check src tests examples
mypy src --ignore-missing-imports
pytest
```

### Live / Integration tests

Integration tests are skipped by default. Enable them explicitly:

```bash
THORDATA_INTEGRATION=true pytest -m integration -v
```

For live end-to-end checks (requires real credentials in `.env`), see:
- `scripts/run_comprehensive_acceptance.py`
- `scripts/acceptance/` (targeted read-only acceptance scripts)

## License

MIT License. See [LICENSE](LICENSE) for details.
