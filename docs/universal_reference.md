# Thordata Web Unlocker / Universal API Reference (Python SDK)

> **SDK Version**: 0.4.0  
> **Last Updated**: 2025-12-16

Thordata Web Unlocker (name on Dashboard) corresponds to the **Universal Scraping API** in the SDK, with the underlying request endpoint:

- `https://webunlocker.thordata.com/request`

In the Python SDK, accessed through the following interfaces:

- `ThordataClient.universal_scrape(...)`
- `ThordataClient.universal_scrape_advanced(UniversalScrapeRequest)`
- `AsyncThordataClient.universal_scrape(...)`
- `AsyncThordataClient.universal_scrape_advanced(UniversalScrapeRequest)`

---

## 0. Common Calling Pattern

### Synchronous

```python
from thordata import ThordataClient

client = ThordataClient(scraper_token="YOUR_SCRAPER_TOKEN")

html = client.universal_scrape(
    url="https://example.com",
    js_render=True,
    output_format="html",
    country="us",
    block_resources="image",
    clean_content="js,css",
    wait=5000,
    wait_for=".content",
)
```

### Asynchronous

```python
import asyncio
from thordata import AsyncThordataClient

async def main():
    async with AsyncThordataClient(scraper_token="YOUR_SCRAPER_TOKEN") as client:
        html = await client.universal_scrape(
            url="https://example.com",
            js_render=True,
            output_format="html",
            country="us",
        )
        print(html[:200])

asyncio.run(main())
```

### Note

The SDK automatically handles the Authorization: Bearer <token> header, you don't need to manually pass the token parameter.

The SDK automatically encodes Python list structures in headers/cookies as JSON strings to comply with API requirements.

## 1. SDK API vs Web Unlocker Parameter Mapping

In the Dashboard documentation, Web Unlocker parameters include:

- token (authentication)
- url
- js_render
- type
- block_resources
- country
- clean_content
- wait
- wait_for
- headers
- cookies

In the SDK's UniversalScrapeRequest / universal_scrape, the corresponding relationships are as follows:

| API param | SDK field/parameter | Type | Required | Default | Description |
|-----------|-------------------|------|----------|---------|-------------|
| token | scraper_token (Client) | str | Yes | — | Passed when initializing ThordataClient / AsyncThordataClient, SDK automatically sets Authorization header. |
| url | url | str | Yes | — | Target webpage URL to scrape. |
| js_render | js_render | bool | No | False | Whether to enable JS rendering (Headless browser) for SPA/dynamic websites. |
| type | output_format | "html" / "png" | No | "html" | Return HTML text or PNG screenshot. |
| block_resources | block_resources | str | No | None | Resource types to block loading, examples: "script", "image", "css", "media", can be combined. |
| country | country | str | No | None | Proxy country/region code (e.g.: "us", "de", "al"). |
| clean_content | clean_content | str | No | None | Content types to remove from returned results, examples: "js", "css", "js,css". |
| wait | wait | int | No | None | Page loading wait time (milliseconds), maximum 100000. |
| wait_for | wait_for | str | No | None | CSS selector, wait for this element to appear in DOM before returning (higher priority than wait). |
| headers | headers | list[dict[str, str]] | No | None | Custom request headers list, automatically encoded as JSON string. |
| cookies | cookies | list[dict[str, str]] | No | None | Custom Cookie list, automatically encoded as JSON string. |
| (Others) | extra_params / **kwargs | dict[str, Any] | No | {} | Future new parameters can be passed directly via kwargs. |

## 2. UniversalScrapeRequest Model (Internal Structure)

UniversalScrapeRequest dataclass definition in SDK (simplified version):

```python
from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List

@dataclass
class UniversalScrapeRequest:
    url: str
    js_render: bool = False
    output_format: str = "html"  # 'html' or 'png'
    country: Optional[str] = None
    block_resources: Optional[str] = None
    clean_content: Optional[str] = None
    wait: Optional[int] = None
    wait_for: Optional[str] = None
    headers: Optional[list[dict[str, str]]] = None
    cookies: Optional[list[dict[str, str]]] = None
    extra_params: dict[str, Any] = field(default_factory=dict)

    def to_payload(self) -> dict[str, Any]:
        # Convert to API form parameters
        ...
```

A typical advanced calling approach:

```python
from thordata import ThordataClient, UniversalScrapeRequest

client = ThordataClient(scraper_token="YOUR_SCRAPER_TOKEN")

request = UniversalScrapeRequest(
    url="https://example.com/dashboard",
    js_render=True,
    output_format="html",
    country="us",
    block_resources="image",
    clean_content="js,css",
    wait=8000,
    wait_for=".dashboard-loaded",
    headers=[{"name": "User-Agent", "value": "Mozilla/5.0 (ThordataBot)"}],
    cookies=[{"name": "session", "value": "abc123"}],
)

html = client.universal_scrape_advanced(request)
```

## 3. Common Usage Scenario Examples

### 3.1 Basic HTML Scraping (No JS Rendering)

```python
html = client.universal_scrape(
    url="https://httpbin.org/html",
    js_render=False,
    output_format="html",
)

print(html[:200])
```

**Features:**

- Fast speed
- Suitable for static pages or simple sites that don't depend on JS rendering

### 3.2 Enable JS Rendering (SPA / Dynamic Pages)

```python
html = client.universal_scrape(
    url="https://example.com/spa",
    js_render=True,
    output_format="html",
    wait=5000,                 # Wait 5 seconds
)
```

Or more recommended "wait for specified element" approach:

```python
html = client.universal_scrape(
    url="https://example.com/spa",
    js_render=True,
    output_format="html",
    wait_for=".main-content",  # Wait for .main-content to appear on page
)
```

**Description:**

- When wait_for exists, it takes priority over wait, maximum wait time is generally 30 seconds (controlled by server)
- Suitable for React/Vue/Angular single-page applications

### 3.3 Use Proxy Country (country)

```python
html = client.universal_scrape(
    url="https://www.google.com/search?q=weather",
    js_render=True,
    output_format="html",
    country="de",              # Use German exit IP
)
```

For strongly regional websites/search results (such as Google/Bing/ecommerce sites), setting country allows you to see the real experience of users in the corresponding region.

### 3.4 Block Resources to Improve Performance (block_resources)

```python
html = client.universal_scrape(
    url="https://example.com/heavy-page",
    js_render=True,
    output_format="html",
    block_resources="image,media",  # Block image and media resources
)
```

**Common values:**

- script
- image
- css
- media

Can be combined using comma separation.

### 3.5 Clean Returned Content (clean_content)

```python
html = client.universal_scrape(
    url="https://example.com",
    js_render=True,
    output_format="html",
    clean_content="js,css",      # Remove JS and CSS content from HTML
)
```

**Suitable for:**

- Reducing noise in LLM input (remove script/style content)
- Reducing page size, controlling token usage cost

### 3.6 Pass Custom Headers and Cookies (Advanced Usage)

Recommend using UniversalScrapeRequest + universal_scrape_advanced:

```python
from thordata import UniversalScrapeRequest

request = UniversalScrapeRequest(
    url="https://example.com/account",
    js_render=True,
    output_format="html",
    headers=[
        {"name": "User-Agent", "value": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"},
        {"name": "Accept-Language", "value": "en-US,en;q=0.9"},
    ],
    cookies=[
        {"name": "sessionid", "value": "session_abc123"},
        {"name": "prefs", "value": "dark_mode=1"},
    ],
)

html = client.universal_scrape_advanced(request)
```

**Note:**

The SDK automatically converts headers/cookies to JSON strings, complying with API documentation requirements:

```json
headers=[{"name":"name1","value":"value1"}, ...]
cookies=[{"name":"name2","value":"value2"}, ...]
```

### 3.7 Screenshots (PNG Output)

```python
png_bytes = client.universal_scrape(
    url="https://example.com",
    js_render=True,
    output_format="png",
)

with open("screenshot.png", "wb") as f:
    f.write(png_bytes)
```

**Asynchronous version:**

```python
async with AsyncThordataClient(scraper_token="YOUR_SCRAPER_TOKEN") as client:
    png_bytes = await client.universal_scrape(
        url="https://example.com",
        js_render=True,
        output_format="png",
    )
    ...
```

## 4. Error Handling Recommendations

When using Universal API, it's recommended to catch the following types of exceptions:

```python
from thordata import (
    ThordataClient,
    ThordataError,
    ThordataAuthError,
    ThordataRateLimitError,
    ThordataNetworkError,
    ThordataTimeoutError,
)

client = ThordataClient(scraper_token="YOUR_SCRAPER_TOKEN")

try:
    html = client.universal_scrape(
        url="https://example.com",
        js_render=True,
        output_format="html",
    )
except ThordataAuthError as e:
    print(f"Auth error: {e}. Check your token or account permissions.")
except ThordataRateLimitError as e:
    print(f"Rate limited: {e}. Consider backing off or upgrading your plan.")
except ThordataTimeoutError as e:
    print(f"Timeout: {e}. Try increasing wait time or output timeout.")
except ThordataNetworkError as e:
    print(f"Network error: {e}. Check connectivity or proxy settings.")
except ThordataError as e:
    print(f"Thordata SDK error: {e}")
except Exception as e:
    print(f"Unexpected error: {e}")
```

## Summary

Web Unlocker / Universal API provides a unified way to scrape complex webpages, automatically handling JS rendering, anti-crawling, CAPTCHA and other issues.

In the SDK, most parameters can be set through explicit fields of universal_scrape, and other parameters can be extended via kwargs or extra_params.

For complex scenarios (such as custom headers/cookies, multi-parameter combinations), it's recommended to use the UniversalScrapeRequest + universal_scrape_advanced pattern to keep configuration clear and reusable.