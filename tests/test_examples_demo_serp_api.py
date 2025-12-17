import os
import subprocess
import sys

from pytest_httpserver import HTTPServer


def test_demo_serp_api_runs_offline(httpserver: HTTPServer) -> None:
    # Mock SERP endpoint
    httpserver.expect_request("/request", method="POST").respond_with_json(
        {
            "code": 200,
            "organic": [
                {"title": "Example Result", "link": "https://example.com"},
                {"title": "Another Result", "link": "https://example.org"},
            ],
            "shopping_results": [
                {"title": "Example Laptop", "price": "$999"},
            ],
            "news_results": [
                {"title": "Example News", "link": "https://news.example.com"},
            ],
        }
    )

    base_url = httpserver.url_for("/").rstrip("/").replace("localhost", "127.0.0.1")

    env = os.environ.copy()
    env["THORDATA_SCRAPER_TOKEN"] = "dummy"
    env["THORDATA_SCRAPERAPI_BASE_URL"] = base_url
    env["PYTHONIOENCODING"] = "utf-8"
    env["PYTHONUTF8"] = "1"

    # Avoid proxying localhost in environments that have HTTP(S)_PROXY set
    env["NO_PROXY"] = "127.0.0.1,localhost"
    env["no_proxy"] = env["NO_PROXY"]

    result = subprocess.run(
        [sys.executable, "examples/demo_serp_api.py"],
        env=env,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=60,
    )

    assert result.returncode == 0, (result.stdout or "") + "\n" + (result.stderr or "")
    out = (result.stdout or "").lower()
    assert "demo" in out and "complete" in out
