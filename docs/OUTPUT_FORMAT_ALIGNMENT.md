# Dashboard Output Format Alignment

This document explains how SDK output formats align with the Dashboard, supporting three formats: JSON, CSV, and Dictionary.

## Output Format Overview

### 1. JSON Format

The SDK's `get_task_result` method returns a download URL. The downloaded file format matches the Dashboard:

```python
result = client.get_task_result(task_id)
# result is a download URL string, e.g.:
# "https://www.thordata.com/scrapers/thordata/2025/06/03/task_id.json"
```

**JSON Structure Example** (aligned with Dashboard):
```json
{
  "spider_parameter": {
    "spider_id": "amazon_product_by-url",
    "spider_name": "amazon.com",
    "parameters": [{"url": "https://www.amazon.com/dp/B000000000"}]
  },
  "data": [
    {
      "title": "Product Title",
      "price": "$99.99",
      ...
    }
  ],
  "metadata": {
    "task_id": "xxx",
    "created_at": "2025-01-01T00:00:00Z",
    "status": "Ready"
  }
}
```

### 2. CSV Format

Export CSV format through acceptance scripts (aligned with Dashboard CSV export):

```python
# Acceptance scripts automatically generate CSV files
# all_tools_coverage_results.csv
```

**CSV Column Structure:**
- name: Test case name
- ok: Success status (True/False)
- task_id: Task ID
- status: Task status (Ready/Success/Failed, etc.)
- spider_id: Spider ID
- spider_name: Spider name
- tool_type: Tool type (text/video)
- error: Error message (if any)
- download_url: Download URL

### 3. Dictionary Format

SDK methods return Python dictionary format for programmatic processing:

```python
# Task status
status_response = client.get_task_status(task_id)
# Returns: {"task_id": "xxx", "status": "Ready"}

# Task list
tasks = client.list_tasks(page=1, size=10)
# Returns: {"count": 100, "list": [...]}

# Usage statistics
stats = client.get_usage_statistics(from_date="2025-01-01", to_date="2025-01-31")
# Returns: {"total_usage_traffic": 1000000, "data": [...]}
```

## Format Conversion Tools

The SDK provides utility functions for format conversion:

```python
from thordata.utils import json_to_csv, json_to_dict

# JSON to CSV
json_to_csv(json_data, output_path="output.csv")

# JSON to Dictionary
dict_data = json_to_dict(json_data)
```

## Dashboard Alignment Checklist

- [x] JSON output structure matches Dashboard
- [x] CSV export format matches Dashboard
- [x] Dictionary format enables programmatic processing
- [x] Error message format unified
- [x] Timestamp format unified (ISO 8601)
- [x] Status value enums match Dashboard

## Example Code

### Get JSON Results

```python
from thordata import ThordataClient
import requests

client = ThordataClient(scraper_token="...")
task_id = client.create_scraper_task_advanced(...)
client.wait_for_task(task_id)
download_url = client.get_task_result(task_id)

# Download JSON file
response = requests.get(download_url)
json_data = response.json()
```

### Export CSV

```python
from thordata.tools import Amazon
from thordata.utils import export_results_to_csv

tool = Amazon.ProductByAsin(asin="B000000000")
results = [...]  # Task results list
export_results_to_csv(results, "output.csv")
```

### Use Dictionary

```python
# Directly use SDK-returned dictionary
status = client.get_task_status(task_id)
if status["status"] == "Ready":
    download_url = client.get_task_result(task_id)
```
