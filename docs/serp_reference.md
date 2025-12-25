# Thordata SERP API Reference (SDK-aligned)

> For a comprehensive parameter reference, see [serp_reference_legacy.md](./serp_reference_legacy.md).
This document is an **SDK-aligned reference** for Thordata SERP API usage.
For the authoritative and up-to-date parameter list, always refer to the official docs:
- Google Search parameters: doc.thordata.com (Google Search)
- Google News parameters: doc.thordata.com (Google News)
- Google Shopping parameters: doc.thordata.com (Google Shopping)
- Yandex parameters: doc.thordata.com (Yandex)

## Endpoint & Authentication

- Endpoint: `POST https://scraperapi.thordata.com/request`
- Headers:
  - `Authorization: Bearer <THORDATA_SCRAPER_TOKEN>`
  - `Content-Type: application/x-www-form-urlencoded`

## Billing & Response Codes

Billing applies **only** when API response `code == 200`.
Other codes are **not billed**.

Common codes include:
- `200`: Success (billed)
- `300`: Not collected (not billed)
- `400`: Bad Request (not billed)
- `401`: Unauthorized (not billed)
- `403`: Forbidden (not billed)
- `404`: Not Found (not billed)
- `429`: Too Many Requests (not billed)
- `500`: Internal Server Error (not billed)
- `504`: Timeout Error (not billed)

## SDK Quick Start

```python
from thordata import ThordataClient

client = ThordataClient(scraper_token="YOUR_TOKEN")

data = client.serp_search(
    query="pizza",
    engine="google",
    country="us",
    language="en",
    num=10,
)

print(len(data.get("organic", [])))
```

## Engine Selection (Recommended)

Use dedicated engines for verticals when available:

- Web search: google, bing, duckduckgo, yandex
- Google News: google_news
- Google Shopping: google_shopping
- Google Product: google_product

Why: dedicated engines typically have clearer parameter contracts and reduce ambiguity.

## Parameter Mapping (SDK -> API)

The SDK sends URL-encoded form fields.

Common fields:

- `engine`: search engine identifier (e.g., google, google_news)
- `q`: query (Google/Bing/DuckDuckGo)
- `text`: query (Yandex)
- `gl`: country (Google)
- `hl`: language (Google)
- `num`: results per page
- `start`: result offset (Google)
- `json`: output format (commonly json=1)

Notes:

- Yandex uses `text` (not `q`) for the query field.
- For Google web search types, `tbm` may be used (images/news/videos/shopping) but using dedicated engines like `google_news` / `google_shopping` is recommended.

## Examples

### Google Search (web)

```bash
curl -X POST https://scraperapi.thordata.com/request \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -H "Authorization: Bearer token" \
  -d "engine=google" \
  -d "q=pizza" \
  -d "json=1"
```

### Google News

```bash
curl -X POST https://scraperapi.thordata.com/request \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -H "Authorization: Bearer token" \
  -d "engine=google_news" \
  -d "q=pizza" \
  -d "json=1"
```

### Google Shopping

```bash
curl -X POST https://scraperapi.thordata.com/request \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -H "Authorization: Bearer token" \
  -d "engine=google_shopping" \
  -d "q=pizza" \
  -d "json=1"
```

### Yandex

```bash
curl -X POST https://scraperapi.thordata.com/request \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -H "Authorization: Bearer token" \
  -d "engine=yandex" \
  -d "text=pizza" \
  -d "json=1"
```

---

> The engines and request examples involved in this document can all be found on the corresponding pages of the official website: Google Search / Google News / Google Shopping / Yandex. <!--citation:3-->  
> Billing and code tables come from SERP API Billing Instructions. <!--citation:4-->