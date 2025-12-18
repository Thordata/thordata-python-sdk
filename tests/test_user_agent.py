import os

import pytest
from pytest_httpserver import HTTPServer
from werkzeug.wrappers import Request, Response

from thordata import AsyncThordataClient, ThordataClient


def test_sync_user_agent_is_sent(httpserver: HTTPServer) -> None:
    def handler(request: Request) -> Response:
        ua = request.headers.get("User-Agent", "")
        assert "thordata-python-sdk/" in ua
        return Response(
            '{"code":200,"organic":[]}', status=200, content_type="application/json"
        )

    httpserver.expect_request("/request", method="POST").respond_with_handler(handler)
    base_url = httpserver.url_for("/").rstrip("/").replace("localhost", "127.0.0.1")

    client = ThordataClient(scraper_token="dummy", scraperapi_base_url=base_url)
    client.serp_search("python", num=1)


@pytest.mark.asyncio
async def test_async_user_agent_is_sent(httpserver: HTTPServer) -> None:
    def handler(request: Request) -> Response:
        ua = request.headers.get("User-Agent", "")
        assert "thordata-python-sdk/" in ua
        return Response(
            '{"code":200,"organic":[]}', status=200, content_type="application/json"
        )

    httpserver.expect_request("/request", method="POST").respond_with_handler(handler)
    base_url = httpserver.url_for("/").rstrip("/").replace("localhost", "127.0.0.1")

    async with AsyncThordataClient(
        scraper_token="dummy", scraperapi_base_url=base_url
    ) as client:
        await client.serp_search("python", num=1)
