"""
Pytest configuration and fixtures for Thordata SDK tests.
"""

from unittest.mock import MagicMock

import pytest


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
