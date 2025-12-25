"""
Tests for AsyncThordataClient error handling.
"""

from typing import Any, Dict
from unittest.mock import AsyncMock, MagicMock, PropertyMock, patch

import pytest

from thordata import (
    AsyncThordataClient,
    ThordataAuthError,
    ThordataRateLimitError,
)


class DummyAsyncResponse:
    """
    Minimal async fake response object for aiohttp.
    """

    def __init__(self, json_data: Dict[str, Any], status: int = 200) -> None:
        self._json_data = json_data
        self.status = status

    async def __aenter__(self) -> "DummyAsyncResponse":
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:
        return None

    def raise_for_status(self) -> None:
        pass

    async def json(self) -> Dict[str, Any]:
        return self._json_data

    async def read(self) -> bytes:
        return b""

    async def text(self) -> str:
        import json

        return json.dumps(self._json_data)


@pytest.mark.asyncio
async def test_async_universal_scrape_rate_limit_error() -> None:
    """
    When Universal API returns JSON with code=402, the async client should raise
    ThordataRateLimitError.
    """
    client = AsyncThordataClient(
        scraper_token="SCRAPER_TOKEN",
        public_token="PUBLIC_TOKEN",
        public_key="PUBLIC_KEY",
    )

    # Create a mock session with closed=False
    mock_session = MagicMock()
    mock_session.closed = False  # Explicitly set closed to False
    mock_response = DummyAsyncResponse({"code": 402, "msg": "Insufficient balance"})
    mock_session.post.return_value = mock_response

    # Manually set the session
    client._session = mock_session

    with pytest.raises(ThordataRateLimitError) as exc_info:
        await client.universal_scrape("https://example.com")

    err = exc_info.value
    assert err.code == 402
    assert isinstance(err.payload, dict)
    assert err.payload.get("msg") == "Insufficient balance"


@pytest.mark.asyncio
async def test_async_create_scraper_task_auth_error() -> None:
    """
    When Web Scraper API returns JSON with code=401, the async client should raise
    ThordataAuthError.
    """
    client = AsyncThordataClient(
        scraper_token="SCRAPER_TOKEN",
        public_token="PUBLIC_TOKEN",
        public_key="PUBLIC_KEY",
    )

    # Create a mock session with closed=False
    mock_session = MagicMock()
    mock_session.closed = False  # Explicitly set closed to False
    mock_response = DummyAsyncResponse({"code": 401, "msg": "Unauthorized"})
    mock_session.post.return_value = mock_response

    # Manually set the session
    client._session = mock_session

    with pytest.raises(ThordataAuthError) as exc_info:
        await client.create_scraper_task(
            file_name="test.json",
            spider_id="dummy-spider",
            spider_name="example.com",
            parameters={"foo": "bar"},
        )

    err = exc_info.value
    assert err.code == 401
    assert isinstance(err.payload, dict)
    assert err.payload.get("msg") == "Unauthorized"
