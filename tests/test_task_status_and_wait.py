import pytest
from pytest_httpserver import HTTPServer

from thordata import (
    AsyncThordataClient,
    ThordataAuthError,
    ThordataClient,
)


def test_wait_for_task_timeout_uses_monotonic(monkeypatch) -> None:
    client = ThordataClient(scraper_token="dummy", public_token="p", public_key="k")

    # Always "running" so it must time out quickly.
    monkeypatch.setattr(client, "get_task_status", lambda task_id: "running")

    with pytest.raises(TimeoutError):
        client.wait_for_task("t1", poll_interval=0.01, max_wait=0.05)


@pytest.mark.asyncio
async def test_async_wait_for_task_timeout_uses_monotonic(monkeypatch) -> None:
    async with AsyncThordataClient(
        scraper_token="dummy", public_token="p", public_key="k"
    ) as client:

        async def _always_running(task_id: str) -> str:
            return "running"

        monkeypatch.setattr(client, "get_task_status", _always_running)

        with pytest.raises(TimeoutError):
            await client.wait_for_task("t1", poll_interval=0.01, max_wait=0.05)


def test_get_task_status_raises_on_non_200_code(httpserver: HTTPServer) -> None:
    httpserver.expect_request("/tasks-status", method="POST").respond_with_json(
        {"code": 401, "msg": "Unauthorized"}
    )

    base_url = httpserver.url_for("/").rstrip("/").replace("localhost", "127.0.0.1")

    client = ThordataClient(
        scraper_token="dummy",
        public_token="p",
        public_key="k",
        web_scraper_api_base_url=base_url,
    )

    with pytest.raises(ThordataAuthError):
        client.get_task_status("t1")


@pytest.mark.asyncio
async def test_async_get_task_status_raises_on_non_200_code(
    httpserver: HTTPServer,
) -> None:
    httpserver.expect_request("/tasks-status", method="POST").respond_with_json(
        {"code": 401, "msg": "Unauthorized"}
    )

    base_url = httpserver.url_for("/").rstrip("/").replace("localhost", "127.0.0.1")

    async with AsyncThordataClient(
        scraper_token="dummy",
        public_token="p",
        public_key="k",
        web_scraper_api_base_url=base_url,
    ) as client:
        with pytest.raises(ThordataAuthError):
            await client.get_task_status("t1")
