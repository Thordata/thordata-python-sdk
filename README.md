# thordata-python-sdk: The Official Python Client

<h4 align="center">
  A high-performance, asynchronous-ready Python library for integrating with the Thordata Proxy Network.
  Perfect for AI Agents and large-scale data collection.
</h4>

---

## 🛠 Installation (安装)

We recommend installing with `pip`:

```bash
pip install thordata-sdk
```

**Note**: Before official release to PyPI, you can install locally using `pip install .` for testing and development.

---

## ⚡ Quick Start (快速开始)

Use Thordata proxy to make requests in three simple steps. Make sure you have the `requests` library installed in your Python environment.

```python
from thordata_sdk import ThordataClient
import requests

# Replace with your Thordata authentication credentials
THORDATA_USER = "YOUR_USERNAME" 
THORDATA_PASS = "YOUR_PASSWORD" 
TARGET_URL = "http://httpbin.org/ip" # A public service for testing IP

# 1. Initialize the client
client = ThordataClient(auth_user=THORDATA_USER, auth_pass=THORDATA_PASS)

# 2. Send request
try:
    # Send request through proxy with 15 second timeout
    response = client.get(TARGET_URL, timeout=15) 

    # 3. Print results
    if response.status_code == 200:
        data = response.json()
        print("Success! Request made via Thordata Proxy.")
        # httpbin.org/ip returns the request source IP to verify proxy is working
        print(f"Origin IP: {data.get('origin')}") 
    else:
        print(f"Request failed with status code: {response.status_code}")

except requests.RequestException as e:
    print(f"An error occurred during request: {e}")
```

---

## ⚙️ Development Status (开发状态)

| Feature | Status | Notes |
|---------|--------|-------|
| Proxy Client (HTTP/S) | ✅ Done (MVP) | ThordataClient class for synchronous requests implemented |
| Setup & Packaging | ✅ Done | Project structure and setup.py configured |
| Async Support | 🚧 Planned | Future integration with aiohttp for high concurrency |

---

## 📄 License (授权)

This project is licensed under the Apache License 2.0.

---

## 📞 Support

Email us at [support@thordata.com](mailto:support@thordata.com) for technical assistance.