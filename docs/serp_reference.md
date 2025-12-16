# Thordata SERP API Reference (Python SDK)

> **SDK Version**: 0.4.0  
> **Last Updated**: 2025-12-16

This document explains how to call Thordata's SERP API via `thordata-python-sdk`, covering:

- **Google** sub-features  
  Search / Shopping / Local / Videos / News / Product / Flights / Images / Lens / Trends / Hotels / Play / Jobs / Scholar / Maps / Finance / Patents
- **Bing** sub-features  
  Search / News / Shopping / Maps / Images / Videos
- **Yandex** Search
- **DuckDuckGo** Search

All examples use the unified entry point:

```python
from thordata import ThordataClient, Engine

client = ThordataClient(scraper_token="YOUR_SCRAPER_TOKEN")
```

## Important

API parameter names in this document (e.g. gl, hl, shoprs, efirst) come directly from the SERP documentation and are the canonical reference.
The SDK exposes some convenience fields (e.g. query, country, language, num, start) and forwards all other parameters via **kwargs unchanged.
When in doubt, prefer the parameter names listed under "API param" in each section.

## 0. Common Calling Pattern

All SERP calls follow the same pattern:

```python
results = client.serp_search(
    query="your query",           # API param: q (if applicable)
    engine=Engine.GOOGLE,         # or Engine.BING / Engine.YANDEX / Engine.DUCKDUCKGO
    search_type="news",           # Google: maps to tbm or mode; Bing: maps to mode; others: ignored
    country="us",                 # API param: gl (where applicable)
    language="en",                # API param: hl (where applicable)
    num=10,                       # items per page (if supported by engine/mode)
    start=0,                      # result offset / page index (if supported)
    # Mode-specific parameters passed directly via kwargs:
    topic_token="...",
    shoprs="...",
    departure_id="CDG,ORY",
    # ...
)
```

### 0.1 SDK vs. API parameter mapping

Where applicable, the SDK provides the following convenience mappings:

| SDK argument | API param (Google example) | Description |
|-------------|---------------------------|-------------|
| query | q | Text search query. |
| country | gl | Country/region code. |
| language | hl | UI/result language code. |
| num | num | Number of results per page. |
| start | start | Result offset. |

All other parameters should be passed to serp_search using their documented API names as keyword arguments (e.g. shoprs, topic_token, departure_id, filters, within, etc.). The SDK forwards them unchanged to the SERP API.

## 1. Google Mode Overview

Supported Google sub-features:

1.1 Google Search  
1.2 Google Shopping  
1.3 Google Local  
1.4 Google Videos  
1.5 Google News  
1.6 Google Product  
1.7 Google Flights  
1.8 Google Images  
1.9 Google Lens  
1.10 Google Trends  
1.11 Google Hotels  
1.12 Google Play  
1.13 Google Jobs  
1.14 Google Scholar  
1.15 Google Maps  
1.16 Google Finance  
1.17 Google Patents

All are accessed through:

```python
results = client.serp_search(..., engine=Engine.GOOGLE, search_type="...") 
```

Unless explicitly stated, Google sub-features share the same basic localization and pagination behavior as 1.1 Google Search.

### 1.1 Google Search

#### Calling method

```python
results = client.serp_search(
    query="pizza",               # q
    engine=Engine.GOOGLE,
    google_domain="google.com",  # google_domain
    country="us",                # gl
    language="en",               # hl
    num=10,                      # num
    start=0,                     # start
    # Optional filters:
    countries_filter="countryFR|countryDE",  # cr
    languages_filter="lang_fr|lang_de",      # lr
    location="San Francisco",    # location
    uule="BASE64_ENCODED",       # uule
    search_type=None,            # tbm; e.g. 'isch','nws','shop','vid'
    safe_search=True,            # safe
    no_autocorrect=True,         # nfpr
    filter_duplicates=True,      # filter
    # Low-level parameters (kwargs):
    ibp="...", lsig="...", si="...", uds="...", tbs="qdr:m",
)

organic_results = results.get("organic_results", [])
```

#### Parameters

| API param | SDK argument | Required | Description |
|-----------|-------------|----------|-------------|
| q | query | Yes | Search query used for crawling. Any language is supported. |
| google_domain | google_domain | No | Google domain used for scraping. Default: google.com. |
| gl | country or gl (kwargs) | No | Country/region code for localized results (e.g. us, ru, uk). |
| hl | language or hl (kwargs) | No | UI language code for search results (e.g. en, es, zh-CN). |
| cr | countries_filter or cr | No | Restrict results to one or more specific countries. Use countryXX codes separated by \|, e.g. countryFR\|countryDE. Overrides gl. |
| lr | languages_filter or lr | No | Restrict results to one or more languages using lang_XX codes, e.g. lang_fr\|lang_de. Overrides hl. |

##### Geographical location

| API param | SDK argument | Required | Description |
|-----------|-------------|----------|-------------|
| location | location | No | Human-readable location string (e.g., San Francisco, California, United States). Often paired with uule. |
| uule | uule | No | Base64-encoded location used internally by Google. |

##### Search type

| API param | SDK argument | Required | Description |
|-----------|-------------|----------|-------------|
| tbm | search_type or tbm (kwargs) | No | Search vertical. Common values: isch (Images), shop (Shopping), nws (News), vid (Videos). SDK maps search_type="images", "shopping", "news", "videos" accordingly. |

##### Pagination

| API param | SDK argument | Required | Description |
|-----------|-------------|----------|-------------|
| start | start | No | Result offset. 0 (default) = first page, 10 = second, 20 = third, etc. |
| num | num | No | Number of results per page. |

##### Advanced parameters

| API param | SDK argument | Required | Description |
|-----------|-------------|----------|-------------|
| ludocid | ludocid | No | Google Place ID (CID) of a Google My Business listing. |
| kgmid | kgmid | No | Google Knowledge Graph ID. Directly targets a specific entity. |
| ibp | ibp | No | Internal rendering / element parameter (e.g., to expand Knowledge Graph cards). |
| lsig | lsig | No | Internal signature parameter, often used to force map/Knowledge Graph views. |
| si | si | No | Cached-search parameter. Overrides all other parameters except start and num. Used for Knowledge Graph tabs. |
| uds | uds | No | Filter/search parameter. Similar to si, used to fetch certain cached or filtered views. |

##### Advanced filters

| API param | SDK argument | Required | Description |
|-----------|-------------|----------|-------------|
| tbs | tbs or time_filter (shortcut) | No | Advanced search parameters. Time examples: qdr:h (past hour), qdr:d (past day), qdr:w (past week), qdr:m (past month), qdr:y (past year). Also used for other filters (e.g., image rights). |
| safe | safe_search or safe | No | Adult content filter: active (strict; default) or off. |
| nfpr | no_autocorrect or nfpr | No | Disable automatic spelling correction when set to 1. |
| filter | filter_duplicates or filter | No | Duplicate/omitted result handling: 1 (default) to enable "Similar/Omitted Results" filters; 0 to disable. |

### 1.2 Google Shopping

#### Calling method

```python
results = client.serp_search(
    query="iPhone 15",           # q
    engine=Engine.GOOGLE,
    search_type="shopping",      # tbm=shop
    google_domain="google.com",
    country="us",                # gl
    language="en",               # hl
    start=0,
    num=20,
    # Shopping-specific filters:
    shoprs="FILTER_ID",
    min_price=500,
    max_price=1500,
    sort_by=1,                   # 1 = price low→high; 2 = price high→low
    free_shipping=True,
    on_sale=True,
    small_business=False,
    direct_link=True,
)

shopping_results = results.get("shopping_results", results.get("organic", []))
```

All Search localization and pagination parameters (Section 1.1) are supported.

#### Shopping-specific parameters

| API param | SDK argument | Required | Description |
|-----------|-------------|----------|-------------|
| shoprs | shoprs | No | Shopping filter ID. Typically copied from Google Shopping URL when specific filters are applied. |
| min_price | min_price | No | Minimum product price. Filters results to price ≥ this value. |
| max_price | max_price | No | Maximum product price. Filters results to price ≤ this value. |
| sort_by | sort_by | No | Sorting criterion: 1 – price low→high; 2 – price high→low. |
| free_shipping | free_shipping | No | Boolean (true / false). Show only products with free shipping. |
| on_sale | on_sale | No | Boolean. Show only products currently on sale. |
| small_business | small_business | No | Boolean. Filter for small-business sellers. |
| direct_link | direct_link | No | Boolean. Include direct merchant links (behavior depends on Google Shopping). |

### 1.3 Google Local

#### Calling method

```python
results = client.serp_search(
    query="pizza near me",       # q
    engine=Engine.GOOGLE,
    search_type="local",         # tbm="local"
    google_domain="google.com",
    country="us",                # gl
    language="en",               # hl
    location="San Francisco",
    uule="ENCODED_LOCATION",
    start=0,                     # 0, 20, 40, ...
    ludocid="OPTIONAL_CID",
)

local_results = results.get("local_results", results.get("organic", []))
```

Google Local reuses most Search parameters. The main differences are:

#### Local-specific behavior / parameters

| API param | SDK argument | Required | Description |
|-----------|-------------|----------|-------------|
| start | start | No | Local results only accept multiples of 20 (0, 20, 40, ...). |
| ludocid | ludocid | No | Google Place ID (CID) for a specific business. Can be used to focus on one POI. |

All other parameters (google_domain, gl, hl, location, uule, tbs, etc.) behave as in Search.

### 1.4 Google Videos

#### Calling method

```python
results = client.serp_search(
    query="python async tutorial",  # q
    engine=Engine.GOOGLE,
    search_type="videos",           # tbm=vid
    google_domain="google.com",
    country="us",                   # gl
    language="en",                  # hl
    lr="lang_en|lang_fr",
    location="United States",
    uule="ENCODED_LOCATION",
    start=0,
    num=10,
    tbs="qdr:m",                    # or time_filter="month"
    safe=True,
    nfpr=1,
    filter=1,
)

video_results = results.get("video_results", results.get("organic", []))
```

#### Parameters

Google Videos uses the same set of parameters as Search (Section 1.1):

- **Localization**: google_domain, gl, hl, lr
- **Geotargeting**: location, uule
- **Pagination**: start, num
- **Advanced filters**: tbs, safe, nfpr, filter

No additional video-exclusive parameters are required.

### 1.5 Google News

#### Calling method

```python
results = client.serp_search(
    query="AI regulation",       # q
    engine=Engine.GOOGLE,
    search_type="news",          # tbm=nws
    google_domain="google.com",
    country="us",                # gl
    language="en",               # hl
    topic_token="...",           # optional
    publication_token="...",     # optional
    section_token="...",         # optional
    story_token="...",           # optional
    so=1,                        # 0 = Relevance, 1 = Date
)

news_results = results.get("news_results", results.get("organic", []))
```

Basic localization (gl, hl) behaves as in Search.

#### News-specific parameters

| API param | SDK argument | Required | Description |
|-----------|-------------|----------|-------------|
| topic_token | topic_token | No | Token for a Google News topic (e.g., World, Business, Technology). |
| publication_token | publication_token | No | Token for a specific publisher (e.g., CNN, BBC). |
| section_token | section_token | No | Token for a subsection of a topic (e.g., Business → Economy). |
| story_token | story_token | No | Token identifying a particular story cluster (full coverage). |
| so | so | No | Sort order: 0 – relevance (default); 1 – date (latest first). |

### 1.6 Google Product

#### Calling method

```python
results = client.serp_search(
    query="",                      # not required for Product mode
    engine=Engine.GOOGLE,
    search_type="product",
    product_id="PRODUCT_ID_HERE",
    google_domain="google.com",
    country="us",                  # gl
    language="en",                 # hl
    # One of the following (mutually exclusive with offer_id):
    offers=True,                   # API: offers=1
    # specs=True,                  # API: specs=1
    # reviews=True,                # API: reviews=1
    # Optional:
    # offer_id="OFFER_ID",         # mutually exclusive with offers/specs/reviews
    # page=1,                      # when offers enabled
    # filter="...",                # advanced filters
)

product_results = results.get("product_results", results.get("shopping_results", []))
```

#### Core product parameters

| API param | SDK argument | Required | Description |
|-----------|-------------|----------|-------------|
| product_id | product_id | Yes | Product ID from URLs like https://www.google.com/shopping/product/{product_id}. |

##### Views and mode selection

The following flags are mutually exclusive with each other and with offer_id.

| API param | SDK argument | Required | Description |
|-----------|-------------|----------|-------------|
| offers | offers | No | Enable offers results (online sellers). Accepts 1 or true. |
| specs | specs | No | Enable product specification results. Accepts 1 or true. |
| reviews | reviews | No | Enable review results. Accepts 1 or true. |

##### Pagination for offers

| API param | SDK argument | Required | Description |
|-----------|-------------|----------|-------------|
| start | start | No | Standard offset: start=30 skips first 30 results. |
| page | page | No | Page number for online sellers (10 results per page). Equivalent to start = page * 10. Only available when offers is enabled. |

##### Advanced filters

| API param | SDK argument | Required | Description |
|-----------|-------------|----------|-------------|
| filter | filter | No | Complex filter string for reviews and offers (sorting, pagination, etc.). |
| offer_id | offer_id | No | ID used to get multiple offers from online sellers (from sellers_results.online_sellers). Cannot be used with offers, specs, or reviews. |

Standard localization parameters (google_domain, gl, hl, location, uule) work as in Search.

### 1.7 Google Flights

#### Calling method

```python
results = client.serp_search(
    query="",                        # not used
    engine=Engine.GOOGLE,
    search_type="flights",
    departure_id="CDG,ORY",          # airport codes or kgmids
    arrival_id="AUS,/m/0vzm",
    outbound_date="2025-08-31",
    return_date="2025-09-06",
    travel_class=2,                  # 1=Economy, 2=Premium economy, 3=Business, 4=First
    adults=2,
    children=1,
    infants_in_seat=0,
    infants_on_lap=0,
)

flights_results = results.get("flights_results", results)
```

#### Parameters

| API param | SDK argument | Required | Description |
|-----------|-------------|----------|-------------|
| departure_id | departure_id | Yes | One or more departure airports or location kgmids, comma-separated. Airport codes are 3-letter uppercase (e.g., CDG). Location kgmids start with /m/ (e.g., /m/0vzm). |
| arrival_id | arrival_id | Yes | One or more arrival airports or location kgmids, comma-separated. |

##### Dates

| API param | SDK argument | Required | Description |
|-----------|-------------|----------|-------------|
| outbound_date | outbound_date | No | Outbound date in YYYY-MM-DD format (e.g., 2025-08-31). |
| return_date | return_date | No | Return date in YYYY-MM-DD format (e.g., 2025-09-06). Optional for one-way trips. |

##### Travel class

| API param | SDK argument | Required | Description |
|-----------|-------------|----------|-------------|
| travel_class | travel_class | No | Travel class: 1 – Economy (default), 2 – Premium economy, 3 – Business, 4 – First. |

##### Number of passengers

| API param | SDK argument | Required | Description |
|-----------|-------------|----------|-------------|
| adults | adults | No | Number of adults. Default: 1. |
| children | children | No | Number of children. Default: 0. |
| infants_in_seat | infants_in_seat | No | Number of infants in their own seats. Default: 0. |
| infants_on_lap | infants_on_lap | No | Number of lap infants. Default: 0. |

### 1.8 Google Images

#### Calling method

```python
results = client.serp_search(
    query="cute cats",             # q
    engine=Engine.GOOGLE,
    search_type="images",          # tbm=isch
    google_domain="google.com",
    g1="us",                       # country (API: g1)
    h1="en",                       # language (API: h1)
    cr="countryUS|countryCA",
    location="United States",
    uule="ENCODED_LOCATION",
    # Time period:
    period_unit="d",               # s/n/h/d/w/m/y
    period_value=7,                # default 1
    start_date="20240101",         # YYYYMMDD
    end_date="20241231",           # YYYYMMDD
    # Pagination:
    ijn=0,                         # image page index
    # Filters:
    chips="red apple",
    imgar="w",
    imgsz="large",
    image_color="red",
    image_type="photo",
    licenses="fc",
    safe="active",
    nfpr=1,
    filter=1,
)

images_results = results.get("images_results", results.get("organic", []))
```

#### Localization & geotargeting

| API param | SDK argument | Required | Description |
|-----------|-------------|----------|-------------|
| google_domain | google_domain | No | Google domain for image search. |
| g1 | g1 | No | Country for image search results. |
| h1 | h1 | No | Language for image results. |
| cr | cr | No | Multiple-country filter, same semantics as in Search. |
| location | location | No | Human-readable location string. |
| uule | uule | No | Encoded location. |

#### Time period

| API param | SDK argument | Required | Description |
|-----------|-------------|----------|-------------|
| period_unit | period_unit | No | Unit for recent-time image search: s (second), n (minute), h (hour), d (day), w (week), m (month), y (year). |
| period value | period_value | No | Time period multiplier, combined with period_unit (e.g., 42 hours, 178 days). Default: 1. Range: 1..2147483647. |
| start date | start_date | No | Start date of a custom time period, in YYYYMMDD format. |
| end date | end_date | No | End date of a custom time period, in YYYYMMDD format (e.g., 20241231). |

#### Pagination

| API param | SDK argument | Required | Description |
|-----------|-------------|----------|-------------|
| ijn | ijn | No | Page number for Google Images. Each page contains 100 images. Equivalent to start = ijn * 100. |

#### Advanced filters

| API param | SDK argument | Required | Description |
|-----------|-------------|----------|-------------|
| chips | chips | No | Alternative image search filter. String from suggested searches (e.g., red apple), available under suggested_searches when ijn=0. |
| tbs | tbs | No | Raw advanced search parameter string for options not exposed elsewhere. |
| imgar | imgar | No | Aspect ratio: s (square), t (tall), w (wide), xw (panoramic). |
| imgsz | imgsz | No | Image size: l (large), m (medium), i (icon), or thresholds like qsvga, vga, svga, xga, 2mp, 4mp, 6mp, 8mp, 10mp, 12mp, 15mp, 20mp, 40mp. |
| image_color | image_color | No | Color filter: bw, trans, red, orange, yellow, green, teal, blue, purple, pink, white, gray, black. |
| image_type | image_type | No | Type filter: face, photo, clipart, lineart, animated. |
| licenses | licenses | No | Usage rights: f (free to use/share), fc (free to use/share, even commercially), fm (free to use/share/modify), fmc (free to use/share/modify, even commercially), cl (Creative Commons), ol (commercial & other licenses). |
| safe | safe | No | Adult filter: active (strict; default), off. |
| nfpr | nfpr | No | Exclude results from auto-corrected queries when set to 1. |
| filter | filter | No | Turn Similar/Omitted results filters on (1, default) or off (0). |

### 1.9 Google Lens

#### Calling method

```python
results = client.serp_search(
    query="",                       # optional text query for some types
    engine=Engine.GOOGLE,
    search_type="lens",
    url="https://i.imgur.com/HBrB8p0.png",  # image URL
    country="us",                   # gl
    language="en",                  # hl
    type="products",                # all | products | exact_matches | visual_matches
    q="acting",                     # extra text query (optional)
    safe="active",
)

lens_results = results.get("lens_results", results)
```

#### Parameters

| API param | SDK argument | Required | Description |
|-----------|-------------|----------|-------------|
| url | url | Yes | Public URL of the image to use in the Lens search. |
| gl | country or gl | No | Country/region code. |
| hl | language or hl | No | UI language code. |

##### Search type

| API param | SDK argument | Required | Description |
|-----------|-------------|----------|-------------|
| type | type | No | Type of Lens search: all (default), products, exact_matches, visual_matches. |

##### Advanced parameters

| API param | SDK argument | Required | Description |
|-----------|-------------|----------|-------------|
| q | q or query | No | Additional search query text. Only applicable for all, products, and visual_matches. |
| safe | safe | No | Adult content filtering: active (strict; default) or off. |

### 1.10 Google Trends

#### Calling method

```python
results = client.serp_search(
    query="Python",              # q
    engine=Engine.GOOGLE,
    search_type="trends",
    language="en",               # hl
    geo="US",
    region="COUNTRY",            # COUNTRY / REGION / DMA / CITY
    data_type="TIMESERIES",
    tz=420,                      # minutes, e.g., 420 = PDT (UTC-7)
    cat=0,                       # category, 0 = all
    gprop="news",                # images | news | froogle | youtube
    date="today 12-m",           # time range
)

trends_results = results.get("trends_results", results)
```

#### Parameters

| API param | SDK argument | Required | Description |
|-----------|-------------|----------|-------------|
| q | query | Yes | Search query for Google Trends. |
| hl | language or hl | No | Language code. |

##### Geographical location

| API param | SDK argument | Required | Description |
|-----------|-------------|----------|-------------|
| geo | geo | No | Location code. Defaults to Worldwide when empty. See Google Trends Locations for full list. |
| region | region | No | Used only with GEO_MAP and related charts to refine geography. Options: COUNTRY, REGION, DMA, CITY. |

##### Search type

| API param | SDK argument | Required | Description |
|-----------|-------------|----------|-------------|
| data_type | data_type | No | Trend chart type: TIMESERIES (interest over time), GEO_MAP (compared breakdown by region; multiple queries), GEO_MAP_0 (interest by region; single query), RELATED_TOPICS, RELATED_QUERIES. |

##### Advanced parameters

| API param | SDK argument | Required | Description |
|-----------|-------------|----------|-------------|
| tz | tz | No | Time zone offset in minutes (default 420 = PDT). Range: -1439..1439. |
| cat | cat | No | Category ID. Default 0 for all categories. |
| gprop | gprop | No | Property: images, news, froogle (Shopping), youtube, or empty for Web Search. |
| date | date | No | Date/time range. Options include: now 1-H, now 4-H, now 1-d, now 7-d, today 1-m, today 3-m, today 12-m, today 5-y, all, or custom ranges like 2021-10-15 2022-05-25. |

### 1.11 Google Hotels

#### Calling method

```python
results = client.serp_search(
    query="hotels in New York",   # q
    engine=Engine.GOOGLE,
    search_type="hotels",
    google_domain="google.com",
    country="us",                 # gl
    language="en",                # hl
    check_in_date="2025-08-22",
    check_out_date="2025-08-23",
    adults=2,
)

hotels_results = results.get("hotels_results", results)
```

#### Parameters

| API param | SDK argument | Required | Description |
|-----------|-------------|----------|-------------|
| q | query | Yes | Hotel search query. |
| google_domain | google_domain | No | Google domain. |
| gl | country or gl | No | Country/region code. |
| hl | language or hl | No | Language code. |

##### Advanced parameters

| API param | SDK argument | Required | Description |
|-----------|-------------|----------|-------------|
| check_in_date | check_in_date | No | Check-in date in YYYY-MM-DD format (e.g., 2025-08-22). |
| check_out_date | check_out_date | No | Check-out date in YYYY-MM-DD format (e.g., 2025-08-23). |
| adults | adults | No | Number of adults. Default: 2. |

### 1.12 Google Play

#### Calling method

```python
results = client.serp_search(
    query="todo list",            # q
    engine=Engine.GOOGLE,
    search_type="play",
    g1="us",                      # country
    h1="en",                      # language
    apps_category="PRODUCTIVITY",
    next_page_token="...",
    section_page_token="...",
    chart="top_free",
    see_more_token="...",
    store_device="phone",
    age="9plus",
)

play_results = results.get("play_results", results)
```

#### Parameters

| API param | SDK argument | Required | Description |
|-----------|-------------|----------|-------------|
| q | query | Yes | Search query for Google Play. |

##### Localization

| API param | SDK argument | Required | Description |
|-----------|-------------|----------|-------------|
| g1 | g1 | No | Country code for Play content. |
| h1 | h1 | No | Language code for Play content. |

##### Search type / filters

| API param | SDK argument | Required | Description |
|-----------|-------------|----------|-------------|
| apps_category | apps_category | No | App category filter (e.g., Productivity, Games, etc.). |

##### Pagination / navigation

| API param | SDK argument | Required | Description |
|-----------|-------------|----------|-------------|
| next_page_token | next_page_token | No | Token for retrieving the next page of results. |
| section_page_token | section_page_token | No | Token for navigating sections within Play results. |
| chart | chart | No | Chart selection (e.g., top free, top grossing). |
| see_more_token | see_more_token | No | Token for "see more" sections. |

##### Advanced parameters

| API param | SDK argument | Required | Description |
|-----------|-------------|----------|-------------|
| store_device | store_device | No | Device type (e.g., phone, tablet). |
| age | age | No | Age filter for content (e.g., age ratings). |

### 1.13 Google Jobs

#### Calling method

```python
results = client.serp_search(
    query="data scientist",       # q
    engine=Engine.GOOGLE,
    search_type="jobs",
    google_domain="google.com",
    country="us",                 # gl
    language="en",                # hl
    location="San Francisco",
    uule="ENCODED_LOCATION",
    start=0,
    page=0,
    next_page_token="1",
    lrad=50,                      # search radius (km)
    ltype=1,                      # work from home filter
    uds="FILTER_STRING",
)

jobs_results = results.get("jobs_results", results)
```

#### Parameters

| API param | SDK argument | Required | Description |
|-----------|-------------|----------|-------------|
| q | query | Yes | Job search query. |
| google_domain | google_domain | No | Google domain. |
| gl | country or gl | No | Country/region code. |
| hl | language or hl | No | Language code. |

##### Geographical location

| API param | SDK argument | Required | Description |
|-----------|-------------|----------|-------------|
| location | location | No | Location string (e.g., city name). |
| uule | uule | No | Encoded location. |

##### Pagination

| API param | SDK argument | Required | Description |
|-----------|-------------|----------|-------------|
| start | start | No | Result offset. |
| page | page | No | Page index (number of results per page depends on Google Jobs behavior). |

##### Advanced parameters

| API param | SDK argument | Required | Description |
|-----------|-------------|----------|-------------|
| next_page_token | next_page_token | No | Token for retrieving the next page of results (e.g., 1). |
| lrad | lrad | No | Search radius in kilometers. Radius is not strictly limited. |
| ltype | ltype | No | Work-from-home filter (e.g., 1 to filter for WFH jobs). |
| uds | uds | No | Filter search string provided by Google. Values appear under filters with uds, q, and serpapi_link. |

### 1.14 Google Scholar

#### Calling method

```python
results = client.serp_search(
    query="graph neural networks", # q
    engine=Engine.GOOGLE,
    search_type="scholar",
    language="en",                 # hl
    lr="lang_en",
    location="United States",
    uule="ENCODED_LOCATION",
    start=0,
    num=10,
    as_sdt=0,
    cites="1275980731835430123",
    as_ylo=2018,
    as_yhi=2024,
    scisbd=1,
    cluster=None,
    safe="active",
    nfpr=1,
    filter=1,
    as_vis=0,
    as_rr=0,
)

scholar_results = results.get("scholar_results", results)
```

#### Basic parameters

| API param | SDK argument | Required | Description |
|-----------|-------------|----------|-------------|
| q | query | Yes | Scholar search query. |
| hl | language or hl | No | UI language. |
| lr | lr | No | Language filter (lang_XX codes). |

##### Geographical location

| API param | SDK argument | Required | Description |
|-----------|-------------|----------|-------------|
| location | location | No | Location string. |
| uule | uule | No | Encoded location. |

##### Search type

| API param | SDK argument | Required | Description |
|-----------|-------------|----------|-------------|
| as_sdt | as_sdt | No | Search type / filter. As filter (articles only): 0 – exclude patents (default); 7 – include patents. As search type: 4 – case law (US courts only; selects all state and federal courts). |

##### Pagination

| API param | SDK argument | Required | Description |
|-----------|-------------|----------|-------------|
| start | start | No | Result offset. |
| num | num | No | Number of results per page. |

##### Advanced parameters

| API param | SDK argument | Required | Description |
|-----------|-------------|----------|-------------|
| cites | cites | No | ID for "Cited by" searches. Example: cites=1275980731835430123. Using cites with q triggers search within citing articles. |
| as_ylo | as_ylo | No | From year. Can be combined with as_yhi. |
| as_yhi | as_yhi | No | To year. Can be combined with as_ylo. |
| scisbd | scisbd | No | Sort by date: 1 – last year, abstracts only; 2 – last year, all content; 0 (default) – sort by relevance. |
| cluster | cluster | No | ID for "All versions" searches. Example: cluster=1275980731835430123. Must not be used together with q and cites. |

##### Advanced filters

| API param | SDK argument | Required | Description |
|-----------|-------------|----------|-------------|
| safe | safe | No | Adult content filter. |
| nfpr | nfpr | No | Exclude auto-corrected results when set to 1. |
| filter | filter | No | Similar/Omitted results filter: 1 (default) enabled, 0 disabled. |
| as_vis | as_vis | No | Show citations: 1 – exclude citation-only items; 0 (default) – include them. |
| as_rr | as_rr | No | Show only review/comment articles: 1 – review-only; 0 (default) – all results. |

### 1.15 Google Maps

#### Calling method

```python
results = client.serp_search(
    query="coffee near me",       # q
    engine=Engine.GOOGLE,
    search_type="maps",
    google_domain="google.com",
    country="us",                 # gl
    language="en",                # hl
    ll="@40.7455096,-74.0083012,14z",
    type="search",                # search | place
    start=0,
    data="DATA_STRING",
    place_id=None,
    data_cid=None,
)

maps_results = results.get("maps_results", results.get("local_results", []))
```

#### Parameters

| API param | SDK argument | Required | Description |
|-----------|-------------|----------|-------------|
| q | query | Yes | Query text for Maps search. |
| google_domain | google_domain | No | Google domain. |
| gl | country or gl | No | Country code. |
| hl | language or hl | No | Language code. |

##### Geographical location

| API param | SDK argument | Required | Description |
|-----------|-------------|----------|-------------|
| ll | ll | No | GPS coordinates of origin in the format: @<latitude>,<longitude>,<scale>, e.g. @40.7455096,-74.0083012,14z. |

##### Search type

| API param | SDK argument | Required | Description |
|-----------|-------------|----------|-------------|
| type | type | No | Type of search: search – list of results when q is set; place – details for a specific location when data is set. No type is required when using place_id or data_cid directly. |

##### Pagination

| API param | SDK argument | Required | Description |
|-----------|-------------|----------|-------------|
| start | start | No | Result offset for Maps results. (For Local results, only multiples of 20 may be valid.) |

##### Advanced parameters

| API param | SDK argument | Required | Description |
|-----------|-------------|----------|-------------|
| data | data | No | Complex filter string copied from the Google Maps URL after setting filters on the website. |
| place_id | place_id | No | Unique reference to a place in Google Maps. Works for businesses, landmarks, parks, intersections. Can be used without any other parameter. |
| data_cid | data_cid | No | Google CID (customer identifier) for a place. Often labeled as place_id in other APIs. |

### 1.16 Google Finance

#### Calling method

```python
results = client.serp_search(
    query="GOOGL",                # q
    engine=Engine.GOOGLE,
    search_type="finance",
    language="en",                # hl
    window="1M",
)

finance_results = results.get("finance_results", results)
```

#### Parameters

| API param | SDK argument | Required | Description |
|-----------|-------------|----------|-------------|
| q | query | Yes | Finance search query (ticker, company name, etc.). |
| hl | language or hl | No | UI language. |

##### Advanced parameters

| API param | SDK argument | Required | Description |
|-----------|-------------|----------|-------------|
| window | window | No | Time range for graph: 1D (default, 1 day), 5D, 1M, 6M, YTD, 1Y, 5Y, MAX. |

### 1.17 Google Patents

#### Calling method

```python
results = client.serp_search(
    query="machine learning optimization",  # q
    engine=Engine.GOOGLE,
    search_type="patents",
    before="priority:20241231",
    after="filing:20200101",
    inventor="John Doe,Jane Smith",
    assignee="Google LLC",
    page=0,
    num=10,
    sort="new",
    clustered="true",
    dups="language",
    patents=True,
    scholar=False,
)

patent_results = results.get("patent_results", results)
```

#### Query

| API param | SDK argument | Required | Description |
|-----------|-------------|----------|-------------|
| q | query | Yes | Patent search query. |

#### Date range

| API param | SDK argument | Required | Description |
|-----------|-------------|----------|-------------|
| before | before | No | Limit results to dates on or before a specified date. Format: "type:YYYYMMDD", where type is priority, filing, or publication. Example: priority:20241231. |
| after | after | No | Limit results to dates on or after a specified date, same "type:YYYYMMDD" format. |

#### Participants

| API param | SDK argument | Required | Description |
|-----------|-------------|----------|-------------|
| inventor | inventor | No | Inventor name(s), separated by commas. |
| assignee | assignee | No | Assignee name(s), separated by commas. |

#### Pagination

| API param | SDK argument | Required | Description |
|-----------|-------------|----------|-------------|
| page | page | No | Page number (used to compute result offset). |
| num | num | No | Maximum number of results per page (e.g., 10). |

#### Advanced parameters

| API param | SDK argument | Required | Description |
|-----------|-------------|----------|-------------|
| sort | sort | No | Sort order. Default: relevance. Examples: new (newest), old (oldest). |
| clustered | clustered | No | Grouping mode. Example value: true – group by classification. |
| dups | dups | No | Deduplication method. Supported: language – deduplicate by publication (language). Default behavior may be family-level deduplication. |
| patents | patents | No | Include Google Patents results. Default true. |
| scholar | scholar | No | Include Google Scholar results. Default false. |

## 2. Bing Mode

Thordata's SERP API supports:

- Bing Search
- Bing News
- Bing Shopping
- Bing Maps
- Bing Images
- Bing Videos

Use:

```python
engine=Engine.BING
search_type="search" | "news" | "shopping" | "maps" | "images" | "videos"
```

All Bing-specific parameters are passed via kwargs using the exact names from this section.

### 2.1 Bing Search

#### Calling method

```python
results = client.serp_search(
    query="Thordata proxy network",  # q
    engine=Engine.BING,
    cc="us",
    mkt="en-US",
    location="New York",
    lat=40.7128,
    lon=-74.0060,
    first=1,
    count=10,
    adlt="strict",
)
```

#### Parameters

| API param | SDK argument | Required | Description |
|-----------|-------------|----------|-------------|
| q | query | Yes | Search query. |

##### Localization & geolocation

| API param | SDK argument | Required | Description |
|-----------|-------------|----------|-------------|
| cc | cc | No | Country/region code (e.g., us, fr). Influences result localization. |
| mkt | mkt | No | Market/language in the format <language>-<country>, e.g. en-US, zh-CN. |
| location | location | No | Starting geographical location name. Should be used with lat and lon. |
| lat | lat | No | Latitude (-90.0 to 90.0). Use with lon. |
| lon | lon | No | Longitude (-180.0 to 180.0). Use with lat. |

##### Pagination

| API param | SDK argument | Required | Description |
|-----------|-------------|----------|-------------|
| first | first | No | Result offset (1-based). Default 1. first=10 promotes the 10th result to the top. |
| count | count | No | Number of results per page. Range: 1–50. |

##### Advanced filters

| API param | SDK argument | Required | Description |
|-----------|-------------|----------|-------------|
| adlt | adlt | No | Adult content filter: strict (default, blocks adult content) or off (allows adult content). |

### 2.2 Bing News

#### Calling method

```python
results = client.serp_search(
    query="AI regulation",         # q
    engine=Engine.BING,
    search_type="news",
    cc="us",
    setlang="en",
    mkt="en-US",
    first=1,
    count=10,
    qft="sortbydate=1",            # example filter
)
```

#### Parameters

| API param | SDK argument | Required | Description |
|-----------|-------------|----------|-------------|
| q | query | Yes | News search query. |

##### Localization

| API param | SDK argument | Required | Description |
|-----------|-------------|----------|-------------|
| cc | cc | No | Country/region code. |
| setlang | setlang | No | UI language. |
| mkt | mkt | No | Market/locale (e.g., en-US). |

##### Pagination

| API param | SDK argument | Required | Description |
|-----------|-------------|----------|-------------|
| first | first | No | Result offset (1-based). |
| count | count | No | Results per page. |

##### Advanced filters

| API param | SDK argument | Required | Description |
|-----------|-------------|----------|-------------|
| qft | qft | No | Query filter text for sorting, date range, etc. Example: qft="sortbydate=1" to sort by date. |

### 2.3 Bing Shopping

#### Calling method

```python
results = client.serp_search(
    query="laptop",                # q
    engine=Engine.BING,
    search_type="shopping",
    cc="us",
    mkt="en-US",
    efirst=1,
    filters='ex1:"ez5_18169_18230"',
)

shopping_results = results.get("shopping_results", results.get("organic", []))
```

#### Parameters

| API param | SDK argument | Required | Description |
|-----------|-------------|----------|-------------|
| q | query | Yes | Shopping search query. |

##### Localization

| API param | SDK argument | Required | Description |
|-----------|-------------|----------|-------------|
| cc | cc | No | Country/region code. |
| mkt | mkt | No | Market/locale. |

##### Pagination

| API param | SDK argument | Required | Description |
|-----------|-------------|----------|-------------|
| efirst | efirst | No | Shopping offset (default: 1). Works similarly to first, e.g. efirst=10 promotes the 10th result. |

##### Advanced filters

| API param | SDK argument | Required | Description |
|-----------|-------------|----------|-------------|
| filters | filters | No | Complex filtering string, e.g. ex1:"ez5_18169_18230" or longer strings like ufn:"Wunderman+Thompson"+sid:"..."+catguid:"..."+segment:"generic.carousel"+entitysegment:"Organization". Copy from Bing Shopping URLs. |

### 2.4 Bing Maps

#### Calling method

```python
results = client.serp_search(
    query="coffee near me",       # q
    engine=Engine.BING,
    search_type="maps",
    setlang="en",
    cp="40.7455096~-74.0083012",
    first=1,
    count=20,
    place_id="PLACE_ID_HERE",
)

maps_results = results.get("maps_results", results.get("local_results", []))
```

#### Parameters

| API param | SDK argument | Required | Description |
|-----------|-------------|----------|-------------|
| q | query | Yes | Maps search query. |

##### Localization & coordinates

| API param | SDK argument | Required | Description |
|-----------|-------------|----------|-------------|
| setlang | setlang | No | UI language. |
| cp | cp | No | GPS coordinates as latitude~longitude, e.g. 40.7455096~-74.0083012. |

##### Pagination

| API param | SDK argument | Required | Description |
|-----------|-------------|----------|-------------|
| first | first | No | Result offset. |
| count | count | No | Results per page. |

##### Advanced filters

| API param | SDK argument | Required | Description |
|-----------|-------------|----------|-------------|
| place_id | place_id | No | Unique reference to a place on Bing Maps. Can be used without q to retrieve a specific POI. |

### 2.5 Bing Images

#### Calling method

```python
results = client.serp_search(
    query="sunset",               # q
    engine=Engine.BING,
    search_type="images",
    cc="us",
    mkt="en-US",
    first=1,
    count=50,
    adlt="strict",
)

image_results = results.get("image_results", results)
```

#### Parameters

| API param | SDK argument | Required | Description |
|-----------|-------------|----------|-------------|
| q | query | Yes | Image search query. |
| cc | cc | No | Country/region. |
| mkt | mkt | No | Market/locale. |
| first | first | No | Offset of first result. |
| count | count | No | Number of images per page. |
| adlt | adlt | No | Adult content filter: strict or off. |

### 2.6 Bing Videos

#### Calling method

```python
results = client.serp_search(
    query="python tutorial",      # q
    engine=Engine.BING,
    search_type="videos",
    cc="us",
    mkt="en-US",
    first=1,
    count=20,
    adlt="off",
)

video_results = results.get("video_results", results)
```

#### Parameters

Same as Bing Images:

q, cc, mkt, first, count, adlt.

## 3. Yandex

Yandex mode focuses on web search, accessed with:

```python
results = client.serp_search(
    query="python tutorial",      # q
    engine=Engine.YANDEX,
    num=10,
    yandex_domain="yandex.com",
    lang="en",
    lr="Moscow,Russia",
    rstr="family",
    p=2,
    within="7d",
)
```

Internally, query is converted to the Yandex search parameter (text), but you only need to set query.

### 3.1 Parameters

#### Query

| API param | SDK argument | Required | Description |
|-----------|-------------|----------|-------------|
| q | query | Yes | Yandex search query. |

##### Localization

| API param | SDK argument | Required | Description |
|-----------|-------------|----------|-------------|
| yandex_domain | yandex_domain | No | Yandex domain used for crawling. Default: yandex.com. Common: yandex.com, yandex.ru, yandex.com.tr. |
| lang | lang | No | Language used for search results. Default: en. Two-letter codes (e.g., en, ru, es). |

##### Geographical location

| API param | SDK argument | Required | Description |
|-----------|-------------|----------|-------------|
| lr | lr | No | Region for search results, e.g. Moscow,Russia. Has priority over IP-based geolocation. |
| rstr | rstr | No | Location strictness and safe search. Example: family enforces family-safe results and region lock. |

##### Pagination & advanced

| API param | SDK argument | Required | Description |
|-----------|-------------|----------|-------------|
| p | p | No | Page number (0-based). Use together with SDK num to define page size. Example: p=2 → third page. |
| within | within | No | Time/domain restriction. E.g., within="7d" for past 7 days; within="example.com" to restrict to a specific domain. |

## 4. DuckDuckGo

DuckDuckGo mode supports basic web search with localization, pagination, and filters:

```python
results = client.serp_search(
    query="python web scraping",  # q
    engine=Engine.DUCKDUCKGO,
    num=10,
    start=0,
    kl="zh-cn",
    df="d",
    kp=-1,
)
```

### 4.1 Parameters

#### Query

| API param | SDK argument | Required | Description |
|-----------|-------------|----------|-------------|
| q | query | Yes | DuckDuckGo search query. |

##### Localization

| API param | SDK argument | Required | Description |
|-----------|-------------|----------|-------------|
| kl | kl | No | Interface language and region. Example: kl="zh-cn" for Simplified Chinese UI and China-region results. |

##### Pagination

| API param | SDK argument | Required | Description |
|-----------|-------------|----------|-------------|
| start | start | No | Offset of first result. Example: start=30 skips first 30 results (page 2). Max recommended: 500 (quality drops after ~16 pages). |
| num | num | No | Number of results per page (SDK convenience field). |

##### Advanced filters

| API param | SDK argument | Required | Description |
|-----------|-------------|----------|-------------|
| df | df | No | Date filter. Specific values depend on DuckDuckGo's config (e.g., d for day). |
| kp | kp | No | Safe search level (e.g., -1, 1, 2). Semantics follow DuckDuckGo's safe-search configuration. |

## Summary

All SERP engines and modes are accessed via a single SDK method:

```
ThordataClient.serp_search(query=..., engine=..., search_type=..., **kwargs).
```

Common fields (query, engine, country, language, num, start) are explicit SDK arguments; all documented API parameters in this file can be passed directly as keyword arguments with their exact API names.

This reference follows the canonical parameter names from the SERP documentation (e.g. g1, h1, shoprs, efirst, within); use these names in **kwargs to match the underlying API.