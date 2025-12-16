# Thordata SERP API Reference (Python SDK)

This document explains how to call Thordata's SERP API in `thordata-python-sdk`, covering:

- Google sub-features (Search / Shopping / Local / Videos / News / Product / Flights / Images / Lens / Trends / Hotels / Play / Jobs / Scholar / Maps / Finance / Patents)
- Bing sub-features (Search / News / Shopping / Maps / Images / Videos)
- Yandex / DuckDuckGo basic search

All examples use the unified entry point:

```python
from thordata import ThordataClient, Engine

client = ThordataClient(scraper_token="YOUR_SCRAPER_TOKEN")
```

**Note:**
- Common parameters are explicitly supported by SerpRequest and ThordataClient.serp_search
- Additional parameters for specific modes are passed directly through **kwargs (e.g., topic_token, shoprs, etc.)

## 0. Common Calling Pattern

All SERP calls follow the same pattern:

```python
results = client.serp_search(
    query="your query",
    engine=Engine.GOOGLE,        # or Engine.BING/YANDEX/DUCKDUCKGO
    search_type="news",          # corresponds to tbm/news, depending on mode
    country="us",                # gl
    language="en",               # hl
    num=10,
    start=0,
    # Mode-specific parameters passed through kwargs
    topic_token="...",
    publication_token="...",
    # ...
)
```

The underlying SerpRequest is responsible for converting these parameters into SERP API HTTP form parameters.

## 1. Google Mode Overview

Supported Google sub-features (may be called "Google XXX API" in documentation):

- Google Search
- Google Shopping
- Google Local
- Google Videos
- Google News
- Google Product
- Google Flights
- Google Images
- Google Lens
- Google Trends
- Google Hotels
- Google Play
- Google Jobs
- Google Scholar
- Google Maps
- Google Finance
- Google Patents

### 1.1 Google Search

**Calling Method:**

```python
results = client.serp_search(
    query="pizza",
    engine=Engine.GOOGLE,
    # Optional:
    country="us",
    language="en",
    num=10,
    start=0,
    search_type=None,      # or "search"
    # Other parameters mentioned in documentation can be passed through kwargs:
    # cr, lr, location, uule, ibp, lsig, si, uds, tbs, safe, nfpr, filter ...
)
```

**Common Parameter Mapping:**

| Document Parameter | SDK Field |
|-------------------|-----------|
| q | query |
| google_domain | google_domain |
| gl | country |
| hl | language |
| cr | countries_filter |
| lr | languages_filter |
| location | location |
| uule | uule |
| tbm | search_type ("images"/"shopping"/"news"/"videos" auto-mapped, others passed as-is) |
| start | start |
| num | num |
| ludocid | ludocid |
| kgmid | kgmid |
| ibp/lsig/si/uds | passed through ibp="...", lsig="..." etc. kwargs |
| tbs | time_filter (shortcut) or direct tbs="qdr:h" |
| safe | safe_search |
| nfpr | no_autocorrect |
| filter | filter_duplicates |

Detailed examples are already provided in README and not repeated here.

### 1.2 Google Shopping

**Calling Method:**

```python
results = client.serp_search(
    query="iPhone 15",
    engine=Engine.GOOGLE,
    search_type="shopping",   # tbm=shop
    country="us",
    language="en",
    num=20,
    # Shopping-specific parameters (kwargs):
    min_price=500,
    max_price=1500,
    sort_by=1,                # 1=price low to high, 2=high to low
    free_shipping=True,
    on_sale=True,
    small_business=True,
    direct_link=True,
    shoprs="FILTER_ID_HERE",
)
shopping_results = results.get("shopping_results", [])
```

**Additional Parameters:**

| Parameter | Usage |
|-----------|-------|
| shoprs | shoprs="..." (filter ID) |
| min_price / max_price | min_price=... / max_price=... |
| sort_by | sort_by=1/2 |
| free_shipping / on_sale / small_business / direct_link | corresponding True/False |

Briefly mentioned in README.

### 1.3 Google Local

**Calling Method:**

```python
results = client.serp_search(
    query="pizza near me",
    engine=Engine.GOOGLE,
    search_type="local",    # tbm="local" (passed as-is)
    google_domain="google.com",
    country="us",
    language="en",
    location="San Francisco",
    uule="ENCODED_LOCATION_HERE",
    start=0,  # Local only accepts 0, 20, 40...
    ludocid="OPTIONAL_PLACE_ID",
)
local_results = results.get("local_results", results.get("organic", []))
```

Google Local documentation mainly reuses Search parameters (q, google_domain, gl, hl, location, uule, start, ludocid). All are supported by SDK with no additional fields needed.

### 1.4 Google Videos

**Calling Method:**

```python
results = client.serp_search(
    query="python async tutorial",
    engine=Engine.GOOGLE,
    search_type="videos",  # tbm=vid
    google_domain="google.com",
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

Parameters in documentation (google_domain/gl/hl/lr/location/uule/start/num/tbs/safe/nfpr/filter) are all covered by previous fields or kwargs.

### 1.5 Google News

Complete examples are provided in README and examples/demo_serp_google_news.py. Only parameter mapping is summarized here.

**Calling Method:**

```python
results = client.serp_search(
    query="AI regulation",
    engine=Engine.GOOGLE,
    search_type="news",    # tbm=nws
    country="us",
    language="en",
    topic_token="...",
    publication_token="...",
    section_token="...",
    story_token="...",
    so=1,                  # 0=Relevance, 1=Date
)
news_results = results.get("news_results", results.get("organic", []))
```

**Exclusive Parameters (all passed through kwargs):**

- topic_token
- publication_token
- section_token
- story_token
- so

### 1.6 Google Product

**Calling Method:**

```python
results = client.serp_search(
    query="",                 # Usually doesn't need q
    engine=Engine.GOOGLE,
    search_type="product",    # Convention usage, passed as tbm="product"
    product_id="1234567890",  # Key parameter
    google_domain="google.com",
    country="us",
    language="en",
)
product_results = results.get("product_results", results.get("shopping_results", []))
```

**Document Parameter Mapping:**

| Parameter | Usage |
|-----------|-------|
| product_id | product_id="..." (kwargs) |
| google_domain/gl/hl/location/uule/start | Same as above |
| offers/specs/reviews | passed through offers=True / specs=True / reviews=True (kwargs) |

**Example:**

```python
results = client.serp_search(
    query="",
    engine=Engine.GOOGLE,
    search_type="product",
    product_id="1234567890",
    offers=True,
    # or specs=True, or reviews=True, these are mutually exclusive
)
```

### 1.7 Google Flights

**Calling Method:**

```python
results = client.serp_search(
    query="",                  # Flights uses departure_id/arrival_id
    engine=Engine.GOOGLE,
    search_type="flights",
    departure_id="CDG,ORY",    # Departure airport or kgmid, multiple values comma-separated
    arrival_id="AUS,/m/0vzm",  # Arrival airport or kgmid
    outbound_date="2025-08-31",
    return_date="2025-09-06",
    travel_class=2,            # 1=Economy, 2=Premium economy, 3=Business, 4=First
    adults=2,
    children=1,
    infants_in_seat=0,
    infants_on_lap=0,
)
flights = results.get("flights_results", results)
```

All parameters are passed through kwargs, no SDK modification needed:

- departure_id
- arrival_id
- outbound_date
- return_date
- travel_class
- adults
- children
- infants_in_seat
- infants_on_lap

### 1.8 Google Images

**Calling Method:**

```python
results = client.serp_search(
    query="cute cats",
    engine=Engine.GOOGLE,
    search_type="images",          # tbm=isch
    google_domain="google.com",
    country="us",
    language="en",
    location="United States",
    uule="...",
    # Image-specific filters:
    period_unit="d",               # day
    period_value=7,                # last 7 days
    start_date="20240101",
    end_date="20241231",
    ijn=0,                         # page number
    chips="red apple",             # suggested search filter
    imgsz="large",
    image_color="red",
    image_type="photo",
    licenses="fc",                 # Free to use commercially
    safe_search=True,
    no_autocorrect=True,
    filter_duplicates=True,
)
images = results.get("images_results", results.get("organic", []))
```

All image-specific parameters (period_unit/period_value/start_date/end_date/ijn/chips/tbs/imgar/imgsz/image_color/image_type/licenses) can be passed through kwargs.

### 1.9 Google Lens

**Calling Method:**

```python
results = client.serp_search(
    query="",                   # Optional
    engine=Engine.GOOGLE,
    search_type="lens",
    url="https://i.imgur.com/HBrB8p0.png",  # Image URL
    country="us",
    language="en",
    type="products",            # all/products/exact_matches/visual_matches
    q="acting",                 # Optional additional query
    safe_search=True,
)
lens_results = results.get("lens_results", results)
```

**Parameter Mapping:**

| Parameter | Usage |
|-----------|-------|
| url | url="..." (kwargs) |
| type | type="products" etc. |
| q | optional auxiliary query |
| safe | safe_search |

### 1.10 Google Trends

**Calling Method:**

```python
results = client.serp_search(
    query="Python",
    engine=Engine.GOOGLE,
    search_type="trends",
    language="en",
    geo="US",                # Geographic location
    region="COUNTRY",        # COUNTRY/REGION/DMA/CITY
    data_type="TIMESERIES",  # TIMESERIES/GEO_MAP/RELATED_TOPICS/...
    tz=420,                  # Timezone (minutes)
    cat=0,                   # Category
    gprop="news",            # images/news/froogle/youtube
    date="today 12-m",       # Time range
)
trends = results.get("trends_results", results)
```

All Trends-specific parameters (geo/region/data_type/tz/cat/gprop/date) are passed through kwargs.

### Google Hotels / Play / Jobs / Scholar / Maps / Finance / Patents

These modes are mostly combinations or special filters of basic Search/Shopping modes. Since SDK already supports complete kwargs passthrough, you can directly write parameters in serp_search(..., parameter_name=value) as found in documentation, without additional code support.

## 2. Bing Mode

Thordata's SERP API provides multiple modes for Bing, following the same principles as Google:

- engine="bing" or Engine.BING
- search_type distinguishes Search / News / Shopping / Maps / Images / Videos
- Additional parameters are passed through kwargs (see official documentation for details)

### 2.1 Bing Search

```python
results = client.serp_search(
    query="Thordata proxy network",
    engine=Engine.BING,
    num=10,
    # Other parameters from Bing documentation can be directly passed through kwargs
    # e.g., cc (country), setLang (language), etc.
)
```

### 2.2 Bing News

```python
results = client.serp_search(
    query="AI regulation",
    engine=Engine.BING,
    search_type="news",
    num=10,
    # Other Bing News-specific parameters also passed through kwargs
)
```

### 2.3 Bing Images / Videos / Shopping / Maps

Similar:

```python
results = client.serp_search(
    query="cute cats",
    engine=Engine.BING,
    search_type="images",   # "videos" / "shopping" / "maps"
    num=20,
    # Other parameters passed through kwargs as documented
)
```

## 3. Yandex / DuckDuckGo

Yandex and DuckDuckGo functionality is relatively simple, mainly Search:

```python
# Yandex
results = client.serp_search(
    query="python tutorial",
    engine=Engine.YANDEX,
    num=10,
)

# DuckDuckGo
results = client.serp_search(
    query="python tutorial",
    engine=Engine.DUCKDUCKGO,
    num=10,
)
```

Parameter names are mostly similar to Google (e.g., country/language). Please refer to Thordata documentation for details and pass through kwargs.

---

## Summary

**Core Design:** All SERP modes are managed through a unified entry point `serp_search` / `SerpRequest`;

**Common Parameters:** Explicit fields for common parameters (`q`/`engine`/`gl`/`hl`/`num`/`start`/...), IDE-friendly;

**Mode-Specific Parameters:** Mode-specific parameters (`topic_token` / `product_id` / `departure_id` / `period_unit` / `geo` / `data_type` ...) are passed through `kwargs` without blocking any parameters in Thordata documentation;

**Future-Proof:** If new parameters are added to the documentation, the SDK doesn't need to be updated immediately - users can use `kwargs` first.