"""
Integration tests for example scripts.

These tests run example scripts against a local mock server to verify
they execute without errors. They don't require real API credentials.
"""

import base64
import json
import os
import subprocess
import sys
from urllib.parse import parse_qs

import pytest
from pytest_httpserver import HTTPServer
from werkzeug.wrappers import Request, Response

# 1x1 transparent PNG for testing
PNG_1X1_BASE64 = (
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMB/"
    "6Xn2mQAAAAASUVORK5CYII="
)


class TestExampleScripts:
    """Test that example scripts run without errors."""

    @pytest.fixture
    def base_env(self):
        """Base environment variables."""
        env = os.environ.copy()
        env.update(
            {
                "THORDATA_SCRAPER_TOKEN": "test_token",
                "THORDATA_PUBLIC_TOKEN": "test_public",
                "THORDATA_PUBLIC_KEY": "test_key",
                "PYTHONIOENCODING": "utf-8",
                "PYTHONUTF8": "1",
                "NO_PROXY": "127.0.0.1,localhost",
                "no_proxy": "127.0.0.1,localhost",
            }
        )
        return env

    def _run_script(
        self, script_path: str, env: dict, timeout: int = 60
    ) -> subprocess.CompletedProcess:
        """Run a Python script and return the result."""
        return subprocess.run(
            [sys.executable, script_path],
            env=env,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout,
        )

    def test_demo_serp_api(self, base_env, httpserver: HTTPServer):
        """Test demo_serp_api.py runs without errors."""

        def serp_handler(request: Request) -> Response:
            body = request.get_data(as_text=True) or ""
            form = parse_qs(body)
            engine = (form.get("engine") or [""])[0]

            if "shopping" in engine:
                payload = {
                    "code": 200,
                    "shopping": [{"title": "Test Laptop", "price": "$999"}],
                }
            elif "news" in engine:
                payload = {
                    "code": 200,
                    "news_results": [{"title": "Test News", "source": "Test"}],
                }
            else:
                payload = {
                    "code": 200,
                    "organic": [
                        {"title": "Test Result", "link": "https://example.com"}
                    ],
                }

            return Response(
                json.dumps(payload), status=200, content_type="application/json"
            )

        httpserver.expect_request("/request", method="POST").respond_with_handler(
            serp_handler
        )

        base_url = httpserver.url_for("/").rstrip("/").replace("localhost", "127.0.0.1")
        env = base_env.copy()
        env["THORDATA_SCRAPERAPI_BASE_URL"] = base_url

        result = self._run_script("examples/demo_serp_api.py", env)
        assert result.returncode == 0, f"{result.stdout}\n{result.stderr}"

    def test_demo_universal(self, base_env, httpserver: HTTPServer):
        """Test demo_universal.py runs without errors."""

        def universal_handler(request: Request) -> Response:
            body = request.get_data(as_text=True) or ""
            form = parse_qs(body)

            # Check if PNG format requested
            req_type = (form.get("type") or ["html"])[0].lower()

            if req_type == "png":
                payload = {"code": 200, "png": PNG_1X1_BASE64}
            else:
                payload = {"code": 200, "html": "<html><body>Test</body></html>"}

            return Response(
                json.dumps(payload), status=200, content_type="application/json"
            )

        httpserver.expect_request("/request", method="POST").respond_with_handler(
            universal_handler
        )

        base_url = httpserver.url_for("/").rstrip("/").replace("localhost", "127.0.0.1")
        env = base_env.copy()
        env["THORDATA_UNIVERSALAPI_BASE_URL"] = base_url

        result = self._run_script("examples/demo_universal.py", env)
        assert result.returncode == 0, f"{result.stdout}\n{result.stderr}"

    def test_demo_web_scraper_api(self, base_env, httpserver: HTTPServer):
        """Test demo_web_scraper_api.py runs without errors."""
        # Builder endpoint
        httpserver.expect_request("/builder", method="POST").respond_with_json(
            {"code": 200, "data": {"task_id": "test_task_123"}}
        )

        # Status endpoint
        httpserver.expect_request("/tasks-status", method="POST").respond_with_json(
            {"code": 200, "data": [{"task_id": "test_task_123", "status": "ready"}]}
        )

        # Download endpoint
        httpserver.expect_request("/tasks-download", method="POST").respond_with_json(
            {"code": 200, "data": {"download": "https://example.com/result.json"}}
        )

        base_url = httpserver.url_for("/").rstrip("/").replace("localhost", "127.0.0.1")
        env = base_env.copy()
        env["THORDATA_SCRAPERAPI_BASE_URL"] = base_url
        env["THORDATA_WEB_SCRAPER_API_BASE_URL"] = base_url

        result = self._run_script("examples/demo_web_scraper_api.py", env)
        assert result.returncode == 0, f"{result.stdout}\n{result.stderr}"

    def test_async_high_concurrency(self, base_env, httpserver: HTTPServer):
        """Test async_high_concurrency.py runs without errors."""
        httpserver.expect_request("/request", method="POST").respond_with_json(
            {"code": 200, "organic": [{"title": "Test", "link": "https://example.com"}]}
        )

        base_url = httpserver.url_for("/").rstrip("/").replace("localhost", "127.0.0.1")
        env = base_env.copy()
        env["THORDATA_SCRAPERAPI_BASE_URL"] = base_url
        env["THORDATA_CONCURRENCY"] = "3"  # Keep small for tests

        result = self._run_script("examples/async_high_concurrency.py", env)
        assert result.returncode == 0, f"{result.stdout}\n{result.stderr}"
