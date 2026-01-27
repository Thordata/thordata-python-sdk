"""
Pytest configuration and fixtures for Thordata SDK tests.

Unit tests use mocks and do not require .env or network/proxy.
Integration tests are gated by THORDATA_INTEGRATION=true and require real credentials;
see CONTRIBUTING.md and .env.example (Testing section).
"""

from unittest.mock import MagicMock

import pytest

from thordata import ThordataClient


@pytest.fixture
def mock_credentials():
    """Provide test credentials."""
    return {
        "scraper_token": "test_scraper_token",
        "public_token": "test_public_token",
        "public_key": "test_public_key",
    }


@pytest.fixture
def mock_response():
    """Create a mock requests.Response object."""
    response = MagicMock()
    response.status_code = 200
    response.raise_for_status = MagicMock()
    response.json.return_value = {"code": 200, "data": {}}
    response.text = "<html></html>"
    response.content = b"<html></html>"
    return response


@pytest.fixture
def mock_session(mock_response):
    """Create a mock requests.Session object."""
    session = MagicMock()
    session.get.return_value = mock_response
    session.post.return_value = mock_response
    session.request.return_value = mock_response
    return session


@pytest.fixture
def client(mock_credentials):
    """Create a ThordataClient for testing."""
    return ThordataClient(
        scraper_token=mock_credentials["scraper_token"],
        public_token=mock_credentials["public_token"],
        public_key=mock_credentials["public_key"],
    )
