"""
Tests for AsyncThordataClient.
"""

import pytest

from thordata import AsyncThordataClient
from thordata.exceptions import ThordataConfigError, ThordataNetworkError
from thordata.models import ProxyConfig, ProxyProduct

# Mark all tests in this module as async
pytestmark = pytest.mark.asyncio

# Mock Credentials
TEST_SCRAPER = "async_scraper_token"
TEST_PUB_TOKEN = "async_public_token"
TEST_PUB_KEY = "async_key"


def _https_proxy_config_dummy() -> ProxyConfig:
    return ProxyConfig(
        username="dummy",
        password="dummy",
        product=ProxyProduct.RESIDENTIAL,
        protocol="https",
        host="vpn_dummy.pr.thordata.net",
        port=9999,
    )


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

    # Fix: Access session via _http wrapper
    assert async_client._http._session is not None
    assert not async_client._http._session.closed


async def test_async_proxy_network_https_not_supported():
    """Test that we raise ConfigError for HTTPS proxies in aiohttp."""
    # Ensure strict check is hit before network
    async with AsyncThordataClient(scraper_token="test_token") as client:
        with pytest.raises(ThordataConfigError) as exc:
            await client.get(
                "https://httpbin.org/ip",
                proxy_config=_https_proxy_config_dummy(),
            )

        # Check for the specific error message about aiohttp limitation
        assert "aiohttp support for 'https://' proxies is limited" in str(exc.value)


async def test_async_http_error_handling():
    """
    Test that connection errors are wrapped in ThordataNetworkError.

    This test attempts to connect to an invalid local proxy port to force a connection error.
    """
    # Create a config that points to localhost on a closed port
    bad_proxy = ProxyConfig(
        username="user",
        password="pass",
        host="127.0.0.1",
        port=1,  # Port 1 is likely closed/unreachable
        protocol="http",
    )

    async with AsyncThordataClient(
        scraper_token="test_token",
        timeout=1,
        # Disable retries to speed up test failure
        retry_config=None,
    ) as client:
        # Override retry config to 0 for this specific instance to fail fast
        client._retry_config.max_retries = 0

        with pytest.raises(ThordataNetworkError) as exc:
            await client.get(
                "http://example.com",
                proxy_config=bad_proxy,
            )

        assert "Async request failed" in str(exc.value)


async def test_async_missing_scraper_token():
    """Test that missing scraper_token allows init but fails on API call."""
    # 1. Init should succeed
    client = AsyncThordataClient(scraper_token="")

    # 2. Use async context manager to init session
    async with client:
        # 3. Method call should fail
        # Updated match string to match actual code in async_client.py
        with pytest.raises(ThordataConfigError, match="scraper_token required"):
            await client.serp_search("test")
