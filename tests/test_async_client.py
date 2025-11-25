import pytest
import aiohttp
from aioresponses import aioresponses
from thordata_sdk import AsyncThordataClient

# Mark all tests in this module as async
pytestmark = pytest.mark.asyncio

# Mock Credentials
TEST_SCRAPER = "async_scraper_token"
TEST_PUB_TOKEN = "async_public_token"
TEST_PUB_KEY = "async_key"
TEST_HOST = "gate.thordata.com"
TEST_PORT = 22225

@pytest.fixture
async def async_client():
    """Fixture for AsyncThordataClient with context management."""
    client = AsyncThordataClient(
        scraper_token=TEST_SCRAPER,
        public_token=TEST_PUB_TOKEN,
        public_key=TEST_PUB_KEY,
        proxy_host=TEST_HOST,
        proxy_port=TEST_PORT
    )
    async with client: 
        yield client

async def test_async_client_initialization(async_client):
    """Test async client properties."""
    expected_url = f"http://{TEST_HOST}:{TEST_PORT}"

    assert async_client.proxy_url == expected_url
    assert isinstance(async_client.proxy_auth, aiohttp.BasicAuth)
    assert async_client.proxy_auth.login == TEST_SCRAPER

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

async def test_async_http_error_handling(async_client):
    """Test async HTTP error."""
    error_url = "http://example.com/async_error"

    with aioresponses() as m:
        m.get(error_url, status=401)

        response = await async_client.get(error_url)
        assert response.status == 401