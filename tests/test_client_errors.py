"""
Tests for ThordataClient error handling.
"""

from typing import Any, Dict
from unittest.mock import MagicMock, patch

import pytest
import requests

from thordata import (
    ThordataAuthError,
    ThordataClient,
    ThordataRateLimitError,
)


class DummyResponse:
    """
    Minimal fake Response object for testing.
    """

    def __init__(self, json_data: Dict[str, Any], status_code: int = 200) -> None:
        self._json_data = json_data
        self.status_code = status_code

    def raise_for_status(self) -> None:
        if 400 <= self.status_code:
            raise requests.HTTPError(response=self)

    def json(self) -> Dict[str, Any]:
        return self._json_data

    @property
    def text(self) -> str:
        import json

        return json.dumps(self._json_data)

    @property
    def content(self) -> bytes:
        return b""


def _make_client() -> ThordataClient:
    """Create a test client with dummy tokens."""
    return ThordataClient(
        scraper_token="SCRAPER_TOKEN",
        public_token="PUBLIC_TOKEN",
        public_key="PUBLIC_KEY",
    )


def test_universal_scrape_rate_limit_error() -> None:
    """
    When Universal API returns JSON with code=402, the client should raise
    ThordataRateLimitError instead of a generic Exception.
    """
    client = _make_client()

    mock_response = DummyResponse({"code": 402, "msg": "Insufficient balance"})

    with patch.object(client, "_api_request_with_retry", return_value=mock_response):
        with pytest.raises(ThordataRateLimitError) as exc_info:
            client.universal_scrape("https://example.com")

    err = exc_info.value
    assert err.code == 402
    assert isinstance(err.payload, dict)
    assert err.payload.get("msg") == "Insufficient balance"


def test_create_scraper_task_auth_error() -> None:
    """
    When Web Scraper API returns JSON with code=401, the client should raise
    ThordataAuthError.
    """
    client = _make_client()

    mock_response = DummyResponse({"code": 401, "msg": "Unauthorized"})

    with patch.object(client, "_api_request_with_retry", return_value=mock_response):
        with pytest.raises(ThordataAuthError) as exc_info:
            client.create_scraper_task(
                file_name="test.json",
                spider_id="dummy-spider",
                spider_name="example.com",
                parameters={"foo": "bar"},
            )

    err = exc_info.value
    assert err.code == 401
    assert isinstance(err.payload, dict)
    assert err.payload.get("msg") == "Unauthorized"
