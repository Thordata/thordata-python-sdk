import json
import os
import subprocess
import sys
from urllib.parse import parse_qs

from pytest_httpserver import HTTPServer
from werkzeug.wrappers import Request, Response

PNG_1X1_BASE64 = (
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMB/"
    "6Xn2mQAAAAASUVORK5CYII="
)


def test_demo_universal_runs_offline(httpserver: HTTPServer) -> None:
    def handler(request: Request) -> Response:
        body = request.get_data(as_text=True) or ""
        form = parse_qs(body)

        req_type = (form.get("type") or ["html"])[0].lower()

        if req_type == "png":
            payload = {"code": 200, "png": PNG_1X1_BASE64}
        else:
            payload = {"code": 200, "html": "<html><body>OK</body></html>"}

        return Response(
            json.dumps(payload),
            status=200,
            content_type="application/json",
        )

    # Universal API endpoint is /request
    httpserver.expect_request("/request", method="POST").respond_with_handler(handler)

    base_url = httpserver.url_for("/").rstrip("/").replace("localhost", "127.0.0.1")

    env = os.environ.copy()
    env["THORDATA_SCRAPER_TOKEN"] = "dummy"
    env["THORDATA_UNIVERSALAPI_BASE_URL"] = base_url

    # Make subprocess output stable on Windows + avoid proxying localhost.
    env["PYTHONIOENCODING"] = "utf-8"
    env["PYTHONUTF8"] = "1"
    env["NO_PROXY"] = "127.0.0.1,localhost"
    env["no_proxy"] = env["NO_PROXY"]

    result = subprocess.run(
        [sys.executable, "examples/demo_universal.py"],
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
