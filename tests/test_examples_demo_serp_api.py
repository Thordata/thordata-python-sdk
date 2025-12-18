import json
import os
import subprocess
import sys
from urllib.parse import parse_qs

from pytest_httpserver import HTTPServer
from werkzeug.wrappers import Request, Response


def test_demo_serp_api_runs_offline(httpserver: HTTPServer) -> None:
    engines_seen: list[str] = []

    def handler(request: Request) -> Response:
        body = request.get_data(as_text=True) or ""
        form = parse_qs(body)
        engine = (form.get("engine") or [""])[0]
        engines_seen.append(engine)

        # Minimal responses per engine
        if engine == "google_shopping":
            payload = {
                "code": 200,
                "shopping_results": [{"title": "Example Laptop", "price": "$999"}],
            }
        elif engine == "google_news":
            payload = {
                "code": 200,
                "news_results": [
                    {"title": "Example News", "link": "https://news.example.com"}
                ],
            }
        else:
            payload = {
                "code": 200,
                "organic": [{"title": "Example Result", "link": "https://example.com"}],
            }

        return Response(
            json.dumps(payload), status=200, content_type="application/json"
        )

    httpserver.expect_request("/request", method="POST").respond_with_handler(handler)

    base_url = httpserver.url_for("/").rstrip("/").replace("localhost", "127.0.0.1")

    env = os.environ.copy()
    env["THORDATA_SCRAPER_TOKEN"] = "dummy"
    env["THORDATA_SCRAPERAPI_BASE_URL"] = base_url
    env["PYTHONIOENCODING"] = "utf-8"
    env["PYTHONUTF8"] = "1"
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

    # Hard assertions: ensure demo uses dedicated engines
    assert "google_shopping" in engines_seen
    assert "google_news" in engines_seen
