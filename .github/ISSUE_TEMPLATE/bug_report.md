---
name: Bug report
about: Help us improve thordata-python-sdk by reporting a bug
title: "[BUG] "
labels: bug
assignees: ''
---

## Describe the bug

A clear and concise description of what the bug is.

> Example: `client.serp_search(...)` raises `KeyError` when using `engine="google_news"`.

---

## To Reproduce

Please provide a **minimal, self‑contained** code snippet that reproduces the issue:

```python
from thordata import ThordataClient, Engine

client = ThordataClient(
    scraper_token="...",
    public_token="...",
    public_key="...",
)

# minimal reproducer
...
```

### Code snippet / steps:
1. 
2. 
3. 

### What command you ran
(e.g. `python script.py`, `pytest`):

```
```

### What happened
Paste error message / stack trace below.

```text
<full error / stack trace here>
```

---

## Expected behavior

A clear description of what you expected to happen instead.

---

## Which API(s) are you using?

Please check all that apply:

- [ ] Proxy `client.get(...)`
- [ ] SERP API `client.serp_search(...)`
- [ ] Universal Scraping `client.universal_scrape(...)`
- [ ] Web Scraper API `create_scraper_task` / `get_task_status` / `get_task_result`
- [ ] Locations API `list_countries` / `list_states` / `list_cities` / `list_asn`
- [ ] Other: 

---

## Environment

- **OS:** (e.g. Windows 11 / macOS 14 / Ubuntu 22.04)
- **Python version:** (e.g. 3.10.12)
- **SDK version:** (e.g. 0.3.0)

### How did you install the SDK?

- [ ] `pip install thordata-sdk`
- [ ] `pip install -e .` (from source)
- [ ] Other: 

---

## Additional context

Any other context, screenshots or logs that might help us understand the problem.

> Please mask any real tokens / credentials before pasting logs or responses.