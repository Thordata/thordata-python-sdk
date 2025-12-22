# Thordata Python SDK

<div align="center">

**Official Python client for Thordata's Proxy Network, SERP API, Web Unlocker, and Web Scraper API.**

*Async-ready, type-safe, built for AI agents and large-scale data collection.*

[![CI](https://github.com/Thordata/thordata-python-sdk/actions/workflows/ci.yml/badge.svg)](https://github.com/Thordata/thordata-python-sdk/actions/workflows/ci.yml)
[![PyPI version](https://img.shields.io/pypi/v/thordata-sdk?color=blue)](https://pypi.org/project/thordata-sdk/)
[![Python](https://img.shields.io/badge/python-3.9+-blue)](https://python.org)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)
[![Typed](https://img.shields.io/badge/typing-typed-purple)](https://github.com/Thordata/thordata-python-sdk)

[Documentation](https://doc.thordata.com) • [Dashboard](https://www.thordata.com) • [Examples](examples/) • [Changelog](CHANGELOG.md)

</div>

---

## ✨ Features

| Feature | Description |
|---------|-------------|
| 🌐 **Proxy Network** | Residential, Mobile, Datacenter, ISP proxies with geo-targeting |
| 🔍 **SERP API** | Google, Bing, Yandex, DuckDuckGo, Baidu search results |
| 🔓 **Web Unlocker** | Bypass Cloudflare, CAPTCHAs, anti-bot systems automatically |
| 🕷️ **Web Scraper** | Async task-based scraping for complex sites |
| ⚡ **Async Support** | Full async/await support with aiohttp |
| 🔄 **Auto Retry** | Configurable retry with exponential backoff |
| 📝 **Type Safe** | Full type annotations for IDE autocomplete |

---

## 📦 Installation

```bash
pip install thordata-sdk
```

For development:

```bash
pip install thordata-sdk[dev]
```

---

## 🚀 Quick Start

### Get Your Credentials

1. Sign up at [thordata.com](https://www.thordata.com)
2. Navigate to your Dashboard
3. Copy your Scraper Token, Public Token, and Public Key

### Basic Usage

```python
from thordata import ThordataClient

# Initialize the client
client = ThordataClient(
    scraper_token="your_scraper_token",
    public_token="your_public_token",  # Optional, for task APIs
    public_key="your_public_key"        # Optional, for task APIs
)

# Make a request through the proxy network
response = client.get("https://httpbin.org/ip")
print(response.json())
# {'origin': '123.45.67.89'}  # Residential IP
```

### Environment Variables

Create a `.env` file:

```env
THORDATA_SCRAPER_TOKEN=your_scraper_token
THORDATA_PUBLIC_TOKEN=your_public_token
THORDATA_PUBLIC_KEY=your_public_key
```

Then use with python-dotenv:

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
```

---

## 📖 Usage Guide

### 1. Proxy Network

#### Basic Proxy Request

```python
from thordata import ThordataClient

client = ThordataClient(scraper_token="your_token")

# GET request through proxy
response = client.get("https://example.com")
print(response.text)

# POST request through proxy
response = client.post("https://httpbin.org/post", json={"key": "value"})
print(response.json())
```

#### Geo-Targeting

```python
from thordata import ThordataClient, ProxyConfig

client = ThordataClient(scraper_token="your_token")

# Create a proxy config with geo-targeting
config = ProxyConfig(
    username="your_username",
    password="your_password",
    country="us",           # Target country
    state="california",     # Target state
    city="los_angeles",     # Target city
)

response = client.get("https://httpbin.org/ip", proxy_config=config)
print(response.json())
```

#### Sticky Sessions

Keep the same IP for multiple requests:

```python
from thordata import ThordataClient, StickySession

client = ThordataClient(scraper_token="your_token")

# Create a sticky session (same IP for 10 minutes)
session = StickySession(
    username="your_username",
    password="your_password",
    country="gb",
    duration_minutes=10,
)

# All requests use the same IP
for i in range(5):
    response = client.get("https://httpbin.org/ip", proxy_config=session)
    print(f"Request {i+1}: {response.json()['origin']}")
```

#### Proxy Credentials

Each proxy product requires **separate credentials** from Thordata Dashboard:

```env
# Residential Proxy (port 9999)
THORDATA_RESIDENTIAL_USERNAME=your_residential_username
THORDATA_RESIDENTIAL_PASSWORD=your_residential_password

# Datacenter Proxy (port 7777)
THORDATA_DATACENTER_USERNAME=your_datacenter_username
THORDATA_DATACENTER_PASSWORD=your_datacenter_password

# Mobile Proxy (port 5555)
THORDATA_MOBILE_USERNAME=your_mobile_username
THORDATA_MOBILE_PASSWORD=your_mobile_password

# Static ISP Proxy (port 6666, direct IP connection)
THORDATA_ISP_HOST=your_static_ip_address
THORDATA_ISP_USERNAME=your_isp_username
THORDATA_ISP_PASSWORD=your_isp_password
```

#### Residential Proxy

```python
from thordata import ProxyConfig, ProxyProduct

proxy = ProxyConfig(
    username="your_username",
    password="your_password",
    product=ProxyProduct.RESIDENTIAL,
    country="us",
)

response = requests.get(
    "http://httpbin.org/ip",
    proxies=proxy.to_proxies_dict(),
)
print(response.json())
```

#### Datacenter Proxy

```python
proxy = ProxyConfig(
    username="your_username",
    password="your_password",
    product=ProxyProduct.DATACENTER,
)
```

#### Mobile Proxy

```python
proxy = ProxyConfig(
    username="your_username",
    password="your_password",
    product=ProxyProduct.MOBILE,
    country="gb",
)
```

#### Static ISP Proxy

Static ISP proxies connect directly to your purchased IP address:

```python
from thordata import StaticISPProxy

proxy = StaticISPProxy(
    host="your_static_ip_address",  # Your purchased IP
    username="your_username",
    password="your_password",
)

response = requests.get(
    "http://httpbin.org/ip",
    proxies=proxy.to_proxies_dict(),
)
# Returns your purchased static IP
```

#### Proxy Examples

```bash
python examples/proxy_residential.py
python examples/proxy_datacenter.py
python examples/proxy_mobile.py
python examples/proxy_isp.py
```

### Run All Examples

```bash
# SERP API examples
python examples/demo_serp_api.py
python examples/demo_serp_google_news.py

# Universal API examples
python examples/demo_universal.py
python examples/demo_scraping_browser.py

# Web Scraper API examples
python examples/demo_web_scraper_api.py

# Proxy Network examples
python examples/proxy_residential.py
python examples/proxy_datacenter.py
python examples/proxy_mobile.py
python examples/proxy_isp.py

# Async high concurrency example
python examples/async_high_concurrency.py
```

### 2. SERP API (Search Engine Results)

#### Basic Search

```python
from thordata import ThordataClient, Engine

client = ThordataClient(scraper_token="your_token")

# Google search
results = client.serp_search(
    query="python programming",
    engine=Engine.GOOGLE,
    num=10
)

# Print organic results
for result in results.get("organic", []):
    print(f"{result['title']}: {result['link']}")
```

#### General Calling Method

```python
from thordata import ThordataClient

client = ThordataClient(scraper_token="YOUR_SCRAPER_TOKEN")

# Recommended: use dedicated engines for Google verticals when available
news = client.serp_search(
    query="pizza",
    engine="google_news",
    country="us",
    language="en",
    num=10,
    so=1,  # 0=relevance, 1=date (Google News)
)

# Alternative: use Google generic engine + tbm via `search_type`
# Note: `search_type` maps to Google tbm and is mainly intended for engine="google".
results = client.serp_search(
    query="pizza",
    engine="google",
    num=10,
    country="us",
    language="en",
    search_type="news",  # tbm=nws (Google generic engine)
    ibp="some_ibp_value",
    lsig="some_lsig_value",
)
```

**Note**: All parameters above will be assembled into Thordata SERP API request parameters.

#### Advanced Search Options

```python
from thordata import ThordataClient, SerpRequest

client = ThordataClient(scraper_token="your_token")

# Create a detailed search request
request = SerpRequest(
    query="best laptops 2024",
    engine="google_shopping",
    num=20,
    country="us",
    language="en",
    safe_search=True,
    device="mobile",
    # Shopping-specific params can be passed via extra_params
    # e.g. min_price=500, max_price=1500, sort_by=1, shoprs="..."
)

results = client.serp_search_advanced(request)
```

#### Multiple Search Engines

```python
from thordata import ThordataClient, Engine

client = ThordataClient(scraper_token="your_token")

# Google
google_results = client.serp_search("AI news", engine=Engine.GOOGLE)

# Bing
bing_results = client.serp_search("AI news", engine=Engine.BING)

# Yandex (Russian search engine)
yandex_results = client.serp_search("AI news", engine=Engine.YANDEX)

# DuckDuckGo
ddg_results = client.serp_search("AI news", engine=Engine.DUCKDUCKGO)
```

---

## 🔧 SERP API Parameter Mapping

Thordata's SERP API supports multiple search engines and sub-features (Google Search/Shopping/News, etc.).  
This SDK wraps common parameters through `ThordataClient.serp_search` and `SerpRequest`, while other parameters can be passed directly through `**kwargs`.

### Google Search Parameter Mapping

| Document Parameter | SDK Field/Usage | Description |
|-------------------|-----------------|-------------|
| q | query | Search keyword |
| engine | engine | Engine.GOOGLE / "google" |
| google_domain | google_domain | e.g., "google.co.uk" |
| gl | country | Country/region, e.g., "us" |
| hl | language | Language, e.g., "en", "zh-CN" |
| cr | countries_filter | Multi-country filter, e.g., "countryFR |
| lr | languages_filter | Multi-language filter, e.g., "lang_en |
| location | location | Exact location, e.g., "India" |
| uule | uule | Base64 encoded location string |
| tbm | search_type | "images"→tbm=isch, "shopping"→tbm=shop, "news"→tbm=nws, "videos"→tbm=vid, other values passed through as-is |
| start | start | Result offset for pagination |
| num | num | Number of results per page |
| ludocid | ludocid | Google Place ID |
| kgmid | kgmid | Google Knowledge Graph ID |
| ibp | ibp="..." (kwargs) | Passed through **kwargs |
| lsig | lsig="..." (kwargs) | Same as above |
| si | si="..." (kwargs) | Same as above |
| uds | uds="ADV" (kwargs) | Same as above |
| tbs | time_filter or tbs="..." | time_filter="week" generates tbs=qdr:w, can also pass complete tbs directly |
| safe | safe_search | True → safe=active, False → safe=off |
| nfpr | no_autocorrect | True → nfpr=1 |
| filter | filter_duplicates | True → filter=1, False → filter=0 |

**Example: Google Search Basic Usage**

```python
results = client.serp_search(
    query="python web scraping best practices",
    engine=Engine.GOOGLE,
    country="us",
    language="en",
    num=10,
    time_filter="week",      # Last week
    safe_search=True,        # Adult content filter
)
```

### Google Shopping Parameter Mapping

Recommended: use the dedicated Google Shopping engine (`engine="google_shopping"`):

```python
results = client.serp_search(
    query="iPhone 15",
    engine="google_shopping",
    country="us",
    language="en",
    num=20,
    # Shopping parameters are passed through kwargs
    min_price=500,
    max_price=1500,
    sort_by=1,
    free_shipping=True,
    on_sale=True,
    small_business=True,
    direct_link=True,
    shoprs="FILTER_ID_HERE",
)
shopping_items = results.get("shopping_results", [])
```
Alternative: use `engine="google"` with `search_type="shopping"` (tbm=shop).

| Document Parameter | SDK Field/Usage | Description |
|-------------------|-----------------|-------------|
| q | query | Search keyword |
| google_domain | google_domain | Same as above |
| gl | country | Same as above |
| hl | language | Same as above |
| location | location | Same as above |
| uule | uule | Same as above |
| start | start | Offset |
| num | num | Quantity |
| tbs | time_filter or tbs="..." | Same as above |
| shoprs | shoprs="..." (kwargs) | Filter ID |
| min_price | min_price=... (kwargs) | Minimum price |
| max_price | max_price=... (kwargs) | Maximum price |
| sort_by | sort_by=1/2 (kwargs) | Sort order |
| free_shipping | free_shipping=True/False (kwargs) | Free shipping |
| on_sale | on_sale=True/False (kwargs) | On sale |
| small_business | small_business=True/False (kwargs) | Small business |
| direct_link | direct_link=True/False (kwargs) | Include direct links |

### Google Local Parameter Mapping

Google Local is mainly about location-based local searches.  
In the SDK, you can use search_type="local" to mark Local mode (tbm passed through as "local"), combined with location + uule.

```python
results = client.serp_search(
    query="pizza near me",
    engine=Engine.GOOGLE,
    search_type="local",
    google_domain="google.com",
    country="us",
    language="en",
    location="San Francisco",
    uule="w+CAIQICIFU2FuIEZyYW5jaXNjbw",  # Example value
    start=0,  # Local only accepts 0, 20, 40...
)
local_results = results.get("local_results", results.get("organic", []))
```

| Document Parameter | SDK Field/Usage | Description |
|-------------------|-----------------|-------------|
| q | query | Search term |
| google_domain | google_domain | Domain |
| gl | country | Country |
| hl | language | Language |
| location location |
| u | location | Localule | uule | Encoded location |
| start | start | Offset (must be 0,20,40...) |
| ludocid | ludocid | Place ID (commonly used in Local results) |
| tbs | time_filter or tbs="..." | Advanced filtering |

### Google Videos Parameter Mapping

```python
results = client.serp_search(
    query="python async tutorial",
    engine=Engine.GOOGLE,
    search_type="videos",   # tbm=vid
    country="us",
    language="en",
    languages_filter="lang_en|lang_fr",
    location="United States",
    uule="ENCODED_LOCATION_HERE",
    num=10,
    time_filter="month",
    safe_search=True,
    filter_duplicates=True,
)
video_results = results.get("video_results", results.get("organic", []))
```

| Document Parameter | SDK Field/Usage | Description |
|-------------------|-----------------|-------------|
| q | query | Search term |
| google_domain | google_domain | Domain |
| gl | country | Country |
| hl | language | Language |
| lr | languages_filter | Multi-language filter |
| location | location | Geographic location |
| uule | uule | Encoded location |
| start | start | Offset |
| num | num | Quantity |
| tbs | time_filter or tbs="..." | Time and advanced filtering |
| safe | safe_search | Adult content filter |
| nfpr | no_autocorrect | Disable auto-correction |
| filter | filter_duplicates | Remove duplicates |

### Google News Parameter Mapping

Google News has a set of exclusive token parameters for precise control of "topics/media/sections/stories".

```python
results = client.serp_search(
    query="AI regulation",
    engine="google_news",
    country="us",
    language="en",
    topic_token="YOUR_TOPIC_TOKEN",
    publication_token="YOUR_PUBLICATION_TOKEN",
    section_token="YOUR_SECTION_TOKEN",
    story_token="YOUR_STORY_TOKEN",
    so=1,  # 0=relevance, 1=date
)
news_results = results.get("news_results", results.get("organic", []))
```

| Document Parameter | SDK Field/Usage | Description |
|-------------------|-----------------|-------------|
| q | query | Search term |
| gl | country | Country |
| hl | language | Language |
| topic_token | topic_token="..." (kwargs) | Topic token |
| publication_token | publication_token="..." (kwargs) | Media token |
| section_token | section_token="..." (kwargs) | Section token |
| story_token | story_token="..." (kwargs) | Story token |
| so | so=0/1 (kwargs) | Sort: 0=relevance, 1=time |

---

👉 For more SERP modes and parameter mappings, see docs/serp_reference.md.

## 🔓 Web Unlocker (Universal Scraping API)

Automatically bypass anti-bot protections:

#### Basic Usage

```python
from thordata import ThordataClient

client = ThordataClient(scraper_token="your_token")

# Get HTML content
html = client.universal_scrape(
    url="https://example.com",
    js_render=True,  # Enable JavaScript rendering
)
print(html[:500])
```

#### Advanced Options

```python
from thordata import ThordataClient, UniversalScrapeRequest

client = ThordataClient(scraper_token="your_token")

request = UniversalScrapeRequest(
    url="https://example.com",
    js_render=True,
    output_format="html",
    country="us",
    block_resources="image,font",  # Speed up by blocking resources
    clean_content="js,css",        # Remove JS/CSS from output
    wait=5000,                     # Wait 5 seconds after load
    wait_for=".content-loaded",    # Wait for CSS selector
    headers=[
        {"name": "Accept-Language", "value": "en-US"}
    ],
    cookies=[
        {"name": "session", "value": "abc123"}
    ],
)

html = client.universal_scrape_advanced(request)
```

#### Take Screenshots

```python
from thordata import ThordataClient

client = ThordataClient(scraper_token="your_token")

# Get PNG screenshot
png_bytes = client.universal_scrape(
    url="https://example.com",
    js_render=True,
    output_format="png",
)

# Save to file
with open("screenshot.png", "wb") as f:
    f.write(png_bytes)
```

### Web Scraper API (Async Tasks)

For complex scraping jobs that run asynchronously:

```python
from thordata import ThordataClient

client = ThordataClient(
    scraper_token="your_token",
    public_token="your_public_token",
    public_key="your_public_key",
)

# Create a scraping task
task_id = client.create_scraper_task(
    file_name="youtube_channel_data",
    spider_id="youtube_video-post_by-url",  # From Dashboard
    spider_name="youtube.com",
    parameters={
        "url": "https://www.youtube.com/@PewDiePie/videos",
        "num_of_posts": "50"
    }
)
print(f"Task created: {task_id}")

# Wait for completion (with timeout)
status = client.wait_for_task(task_id, max_wait=300)
print(f"Task status: {status}")

# Get results
if status in ("ready", "success"):
    download_url = client.get_task_result(task_id)
    print(f"Download: {download_url}")
```

### Async Client (High Concurrency)

For maximum performance with concurrent requests:

```python
import asyncio
from thordata import AsyncThordataClient

async def main():
    async with AsyncThordataClient(
        scraper_token="your_token",
        public_token="your_public_token",
        public_key="your_public_key",
    ) as client:
        
        # Concurrent proxy requests
        urls = [
            "https://httpbin.org/ip",
            "https://httpbin.org/headers",
            "https://httpbin.org/user-agent",
        ]
        
        tasks = [client.get(url) for url in urls]
        responses = await asyncio.gather(*tasks)
        
        for resp in responses:
            print(await resp.json())

asyncio.run(main())
```

#### Async SERP Search

```python
import asyncio
from thordata import AsyncThordataClient, Engine

async def search_multiple():
    async with AsyncThordataClient(scraper_token="your_token") as client:
        queries = ["python", "javascript", "rust", "go"]
        
        tasks = [
            client.serp_search(q, engine=Engine.GOOGLE)
            for q in queries
        ]
        
        results = await asyncio.gather(*tasks)
        
        for query, result in zip(queries, results):
            count = len(result.get("organic", []))
            print(f"{query}: {count} results")

asyncio.run(search_multiple())
```

### Location APIs

Discover available geo-targeting options:

```python
from thordata import ThordataClient, ProxyType

client = ThordataClient(
    scraper_token="your_token",
    public_token="your_public_token",
    public_key="your_public_key",
)

# List all supported countries
countries = client.list_countries(proxy_type=ProxyType.RESIDENTIAL)
print(f"Supported countries: {len(countries)}")

# List states for a country
states = client.list_states("US")
for state in states[:5]:
    print(f"  {state['state_code']}: {state['state_name']}")

# List cities
cities = client.list_cities("US", state_code="california")
print(f"Cities in California: {len(cities)}")

# List ASNs (for ISP targeting)
asns = client.list_asn("US")
for asn in asns[:5]:
    print(f"  {asn['asn_code']}: {asn['asn_name']}")
```

### Error Handling

```python
from thordata import (
    ThordataClient,
    ThordataError,
    ThordataAuthError,
    ThordataRateLimitError,
    ThordataNetworkError,
    ThordataTimeoutError,
)

client = ThordataClient(scraper_token="your_token")

try:
    result = client.serp_search("test query")
except ThordataAuthError as e:
    print(f"Authentication failed: {e}")
    print(f"Check your token. Status code: {e.status_code}")
except ThordataRateLimitError as e:
    print(f"Rate limited: {e}")
    if e.retry_after:
        print(f"Retry after {e.retry_after} seconds")
except ThordataTimeoutError as e:
    print(f"Request timed out: {e}")
except ThordataNetworkError as e:
    print(f"Network error: {e}")
except ThordataError as e:
    print(f"General error: {e}")
```

### Retry Configuration

Customize automatic retry behavior:

```python
from thordata import ThordataClient, RetryConfig

# Custom retry configuration
retry_config = RetryConfig(
    max_retries=5,           # Maximum retry attempts
    backoff_factor=2.0,      # Exponential backoff multiplier
    max_backoff=120.0,       # Maximum wait between retries
    jitter=True,             # Add randomness to prevent thundering herd
)

client = ThordataClient(
    scraper_token="your_token",
    retry_config=retry_config,
)

# Requests will automatically retry on transient failures
response = client.get("https://example.com")
```

---

## 🔧 Configuration Reference

### ThordataClient Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| scraper_token | str | required | API token from Dashboard |
| public_token | str | None | Public API token (for tasks/locations) |
| public_key | str | None | Public API key |
| proxy_host | str | "pr.thordata.net" | Proxy gateway host |
| proxy_port | int | 9999 | Proxy gateway port |
| timeout | int | 30 | Default request timeout (seconds) |
| retry_config | RetryConfig | None | Retry configuration |

### ProxyConfig Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| username | str | required | Proxy username |
| password | str | required | Proxy password |
| product | ProxyProduct | RESIDENTIAL | Proxy type |
| country | str | None | ISO 3166-1 alpha-2 code |
| state | str | None | State name (lowercase) |
| city | str | None | City name (lowercase) |
| continent | str | None | Continent code (af/an/as/eu/na/oc/sa) |
| asn | str | None | ASN code (requires country) |
| session_id | str | None | Session ID for sticky sessions |
| session_duration | int | None | Session duration (1-90 minutes) |

### Proxy Products & Ports

| Product | Port | Description |
|---------|------|-------------|
| RESIDENTIAL | 9999 | Rotating residential IPs |
| MOBILE | 5555 | Mobile carrier IPs |
| DATACENTER | 7777 | Datacenter IPs |
| ISP | 6666 | Static ISP IPs |

---

## 📁 Project Structure

```
thordata-python-sdk/
├── src/thordata/
│   ├── __init__.py         # Public API exports
│   ├── client.py           # Sync client
│   ├── async_client.py     # Async client
│   ├── models.py           # Data models (ProxyConfig, SerpRequest, etc.)
│   ├── enums.py            # Enumerations
│   ├── exceptions.py       # Exception hierarchy
│   ├── retry.py            # Retry mechanism
│   ├── parameters.py       # Parameter definitions
│   ├── demo.py             # Demo functionality
│   └── _utils.py           # Internal utilities
├── tests/
│   ├── __init__.py         # Test initialization
│   ├── conftest.py         # Pytest configuration
│   ├── test_client.py      # Client tests
│   ├── test_async_client.py # Async client tests
│   ├── test_client_errors.py # Client error tests
│   ├── test_async_client_errors.py # Async client error tests
│   ├── test_enums.py       # Enums tests
│   ├── test_models.py      # Models tests
│   ├── test_exceptions.py  # Exceptions tests
│   ├── test_demo_entrypoint.py # Demo entrypoint tests
│   ├── test_task_status_and_wait.py # Task status tests
│   ├── test_user_agent.py  # User agent tests
│   ├── test_examples_demo_serp_api.py # SERP API examples tests
│   ├── test_examples_demo_universal.py # Universal API examples tests
│   ├── test_examples_demo_web_scraper_api.py # Web scraper examples tests
│   └── test_examples_async_high_concurrency.py # Async high concurrency tests
├── examples/
│   ├── demo_serp_api.py            # SERP API demo
│   ├── demo_serp_google_news.py    # Google News demo
│   ├── demo_universal.py           # Universal API demo
│   ├── demo_web_scraper_api.py     # Web scraper demo
│   ├── demo_scraping_browser.py    # Scraping browser demo
│   ├── async_high_concurrency.py   # Async high concurrency demo
│   ├── proxy_residential.py        # Residential proxy example
│   ├── proxy_datacenter.py         # Datacenter proxy example
│   ├── proxy_mobile.py             # Mobile proxy example
│   ├── proxy_isp.py                # Static ISP proxy example
│   └── .env.example                # Environment variables template
├── docs/
│   ├── serp_reference.md           # SERP API reference
│   ├── serp_reference_legacy.md    # Legacy SERP reference
│   └── universal_reference.md      # Universal API reference
├── .github/
│   ├── dependabot.yml              # Dependabot configuration
│   ├── pull_request_template.md    # PR template
│   ├── ISSUE_TEMPLATE/
│   │   ├── bug_report.md           # Bug report template
│   │   └── feature_request.md      # Feature request template
│   └── workflows/
│       ├── ci.yml                  # Continuous integration
│       └── pypi-publish.yml        # PyPI publishing workflow
├── .env.example                    # Environment variables template
├── .prettierrc                     # Prettier configuration
├── .prettierignore                 # Prettier ignore patterns
├── eslint.config.cjs               # ESLint configuration
├── LICENSE                         # License file
├── package.json                    # Package configuration
├── py.typed                        # Type hints marker
├── pyproject.toml                  # Python package configuration
├── pytest.ini                     # Pytest configuration
├── requirements.txt                # Python dependencies
├── tsconfig.json                   # TypeScript configuration
├── tsconfig.build.json             # TypeScript build configuration
├── vitest.config.ts                # Vitest testing configuration
└── README.md                       # This file
```

---

## 🧪 Development

### Setup

```bash
# Clone the repository
git clone https://github.com/Thordata/thordata-python-sdk.git
cd thordata-python-sdk

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install with dev dependencies
pip install -e ".[dev]"
```

### Run Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=thordata --cov-report=html

# Run specific test file
pytest tests/test_client.py -v
```

### Code Quality

```bash
# Format code
black src tests

# Lint
ruff check src tests

# Type check
mypy src
```

---

## 📝 Changelog

See [CHANGELOG.md](CHANGELOG.md) for version history.

---

## 🤝 Contributing

Contributions are welcome! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 🆘 Support

- 📧 **Email**: support@thordata.com
- 📚 **Documentation**: [doc.thordata.com](https://doc.thordata.com)
- 🐛 **Issues**: [GitHub Issues](https://github.com/Thordata/thordata-python-sdk/issues)
- 💬 **Dashboard**: [thordata.com](https://www.thordata.com)

<div align="center">
<sub>Built with ❤️ by the Thordata Team</sub>
</div>