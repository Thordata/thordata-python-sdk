import os
import subprocess
import sys

from pytest_httpserver import HTTPServer


def test_demo_web_scraper_api_runs_offline(httpserver: HTTPServer) -> None:
    # Mock endpoints:
    # - Builder API: POST /builder  -> returns task_id
    # - Status API:  POST /tasks-status -> returns status ready
    # - Download API: POST /tasks-download -> returns download URL
    httpserver.expect_request("/builder", method="POST").respond_with_json(
        {"code": 200, "data": {"task_id": "t_demo_1"}}
    )

    httpserver.expect_request("/tasks-status", method="POST").respond_with_json(
        {"code": 200, "data": [{"task_id": "t_demo_1", "status": "ready"}]}
    )

    httpserver.expect_request("/tasks-download", method="POST").respond_with_json(
        {"code": 200, "data": {"download": "https://example.com/result.json"}}
    )

    base_url = httpserver.url_for("/").rstrip("/").replace("localhost", "127.0.0.1")

    env = os.environ.copy()
    env["THORDATA_SCRAPER_TOKEN"] = "dummy"
    env["THORDATA_PUBLIC_TOKEN"] = "dummy_public"
    env["THORDATA_PUBLIC_KEY"] = "dummy_key"

    # Route SDK requests to our mock server
    env["THORDATA_SCRAPERAPI_BASE_URL"] = base_url
    env["THORDATA_WEB_SCRAPER_API_BASE_URL"] = base_url

    # Make subprocess output stable on Windows and avoid proxying localhost
    env["PYTHONIOENCODING"] = "utf-8"
    env["PYTHONUTF8"] = "1"
    env["NO_PROXY"] = "127.0.0.1,localhost"
    env["no_proxy"] = env["NO_PROXY"]

    result = subprocess.run(
        [sys.executable, "examples/demo_web_scraper_api.py"],
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
