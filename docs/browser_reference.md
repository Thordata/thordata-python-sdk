# Thordata Browser API Reference (Python SDK)

> **SDK Version**: 1.8.4  
> **Last Updated**: 2025-01-21

Thordata Browser API (Scraping Browser) provides remote browser automation capabilities through WebSocket connections. It supports Playwright, Puppeteer, and Selenium frameworks.

## Endpoint & Authentication

- **WebSocket Endpoint**: `wss://{username}:{password}@ws-browser.thordata.com`
- **HTTP Endpoint** (Selenium): `https://{username}:{password}@hs-browser.thordata.com`
- **Authentication**: Username and password (separate from scraper_token)

## SDK Quick Start

### Get Browser Connection URL

```python
from thordata import ThordataClient

client = ThordataClient()

# Get WebSocket URL for Playwright/Puppeteer
ws_url = client.get_browser_connection_url(
    username="your_browser_username",
    password="your_browser_password"
)
print(ws_url)
# Output: wss://td-customer-your_username:your_password@ws-browser.thordata.com
```

### Environment Variables

Set browser credentials via environment variables:

```bash
export THORDATA_BROWSER_USERNAME="your_browser_username"
export THORDATA_BROWSER_PASSWORD="your_browser_password"
```

Then use without arguments:

```python
ws_url = client.get_browser_connection_url()
```

## Framework Integration Examples

### Python - Playwright

```python
import asyncio
from playwright.async_api import async_playwright
from thordata import ThordataClient

async def main():
    client = ThordataClient()
    ws_url = client.get_browser_connection_url()
    
    async with async_playwright() as pw:
        print('Connecting to Browser API...')
        browser = await pw.chromium.connect_over_cdp(ws_url)
        try:
            print('Connected! Navigating to target...')
            page = await browser.new_page()
            await page.goto('https://example.com', timeout=120000)
            
            # Screenshot
            print('Taking screenshot...')
            await page.screenshot(path='./screenshot.png')
            
            # Get HTML content
            print('Getting page content...')
            html = await page.content()
            print(html[:200])
            
        finally:
            await browser.close()

asyncio.run(main())
```

### Python - Selenium

```python
from selenium.webdriver import Remote, ChromeOptions
from selenium.webdriver.chromium.remote_connection import ChromiumRemoteConnection
from thordata import ThordataClient

client = ThordataClient()
ws_url = client.get_browser_connection_url()

# Convert WebSocket URL to HTTP endpoint for Selenium
http_url = ws_url.replace('wss://', 'https://').replace('ws-browser', 'hs-browser')

sbr_connection = ChromiumRemoteConnection(http_url, 'goog', 'chrome')

with Remote(sbr_connection, options=ChromeOptions()) as driver:
    print('Connected! Navigating to target...')
    driver.get('https://example.com')
    
    # Screenshot
    print('Taking screenshot...')
    driver.get_screenshot_as_file('./screenshot.png')
    
    # Get HTML content
    print('Getting page content...')
    html = driver.page_source
    print(html[:200])
```

### Node.js - Playwright

```javascript
const playwright = require('playwright');

// Get connection URL from SDK or construct manually
const AUTH = 'td-customer-username:password';
const WS_URL = `wss://${AUTH}@ws-browser.thordata.com`;

async function main() {
    console.log('Connecting to Browser API...');
    const browser = await playwright.chromium.connectOverCDP(WS_URL);
    try {
        console.log('Connected! Navigating to target...');
        const page = await browser.newPage();
        await page.goto('https://example.com', { timeout: 120000 });
        
        // Screenshot
        console.log('Taking screenshot...');
        await page.screenshot({ path: './screenshot.png' });
        
        // Get HTML content
        console.log('Getting page content...');
        const html = await page.content();
        console.log(html.substring(0, 200));
        
    } finally {
        await browser.close();
    }
}

main().catch(console.error);
```

### Node.js - Puppeteer

```javascript
const puppeteer = require('puppeteer-core');

const AUTH = 'td-customer-username:password';
const WS_URL = `wss://${AUTH}@ws-browser.thordata.com`;

(async () => {
    console.log('Connecting to Browser API...');
    const browser = await puppeteer.connect({
        browserWSEndpoint: WS_URL,
        defaultViewport: { width: 1920, height: 1080 }
    });
    
    try {
        console.log('Connected! Navigating to target...');
        const page = await browser.newPage();
        await page.goto('https://example.com', { timeout: 120000 });
        
        // Screenshot
        console.log('Taking screenshot...');
        await page.screenshot({ path: './screenshot.png' });
        
        // Get HTML content
        console.log('Getting page content...');
        const html = await page.content();
        console.log(html.substring(0, 200));
        
    } finally {
        await browser.close();
    }
})();
```

## Important Notes

### Session Management

1. **Initial Navigation**: Each browser session allows only one **initial navigation** - the first page load. After that, you can navigate freely within the same website via clicks, scrolling, etc.

2. **New Sessions**: To start a new scraping task (same or different website), create a new browser session.

3. **Session Timeout**: All browser sessions automatically timeout after **30 minutes** if not explicitly closed.

4. **One Session Per Account**: In the Web Console environment, only one active session per account is allowed. Always close sessions explicitly in your scripts.

### Username Format

The SDK automatically prefixes usernames with `td-customer-` if not already present:

```python
# Input: "myuser"
# Output: "td-customer-myuser"

# Input: "td-customer-myuser"  
# Output: "td-customer-myuser" (unchanged)
```

### URL Encoding

The SDK automatically URL-encodes credentials to handle special characters:

```python
# Special characters in password are automatically encoded
ws_url = client.get_browser_connection_url(
    username="user@example.com",
    password="p@ssw0rd#123"
)
```

## Error Handling

```python
from thordata import ThordataClient, ThordataConfigError

client = ThordataClient()

try:
    ws_url = client.get_browser_connection_url()
except ThordataConfigError as e:
    print(f"Configuration error: {e}")
    print("Please set THORDATA_BROWSER_USERNAME and THORDATA_BROWSER_PASSWORD")
```

## Best Practices

1. **Always Close Sessions**: Explicitly close browser sessions to avoid resource conflicts
2. **Handle Timeouts**: Set appropriate timeouts for page navigation (default: 120 seconds)
3. **Error Handling**: Wrap browser operations in try/finally blocks
4. **Credential Management**: Use environment variables instead of hardcoding credentials

## Comparison with Other APIs

| Feature | Browser API | Universal API | Web Scraper Tasks |
|---------|-------------|---------------|-------------------|
| **Control Level** | Full browser control | Automated scraping | Pre-built tools |
| **Framework Support** | Playwright, Puppeteer, Selenium | SDK only | SDK only |
| **Use Case** | Complex interactions, custom logic | Simple scraping, JS rendering | Platform-specific scraping |
| **Session Management** | Manual (30min timeout) | Automatic | Task-based |

## Summary

The Browser API provides the most flexible scraping solution, allowing full control over browser automation through standard frameworks. Use it when you need:

- Complex user interactions (clicks, scrolling, form filling)
- Custom JavaScript execution
- Fine-grained control over page loading
- Integration with existing Playwright/Puppeteer/Selenium workflows

For simpler use cases, consider Universal API or Web Scraper Tasks for faster setup and execution.
