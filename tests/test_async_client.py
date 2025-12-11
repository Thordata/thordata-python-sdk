"""
Tests for AsyncThordataClient.
"""

import aiohttp
import pytest

# 检查是否安装了 aioresponses
try:
    from aioresponses import aioresponses

    HAS_AIORESPONSES = True
except ImportError:
    HAS_AIORESPONSES = False

from thordata import AsyncThordataClient

# Mark all tests in this module as async
pytestmark = pytest.mark.asyncio

# Mock Credentials
TEST_SCRAPER = "async_scraper_token"
TEST_PUB_TOKEN = "async_public_token"
TEST_PUB_KEY = "async_key"


@pytest.fixture
async def async_client():
    """Fixture for AsyncThordataClient with context management."""
    client = AsyncThordataClient(
        scraper_token=TEST_SCRAPER,
        public_token=TEST_PUB_TOKEN,
        public_key=TEST_PUB_KEY,
    )
    async with client:
        yield client


async def test_async_client_initialization(async_client):
    """Test async client properties."""
    assert async_client.scraper_token == TEST_SCRAPER
    assert async_client.public_token == TEST_PUB_TOKEN
    assert async_client.public_key == TEST_PUB_KEY
    assert async_client._proxy_auth is not None
    assert isinstance(async_client._proxy_auth, aiohttp.BasicAuth)


@pytest.mark.skipif(not HAS_AIORESPONSES, reason="aioresponses not installed")
async def test_async_successful_request(async_client):
    """Test successful async proxy request."""
    mock_url = "http://example.com/async_test"
    mock_data = {"status": "async_ok"}

    with aioresponses() as m:
        m.get(mock_url, status=200, payload=mock_data)

        response = await async_client.get(mock_url)

        assert response.status == 200
        data = await response.json()
        assert data == mock_data


@pytest.mark.skipif(not HAS_AIORESPONSES, reason="aioresponses not installed")
async def test_async_http_error_handling(async_client):
    """Test async HTTP error."""
    error_url = "http://example.com/async_error"

    with aioresponses() as m:
        m.get(error_url, status=401)

        response = await async_client.get(error_url)
        assert response.status == 401
