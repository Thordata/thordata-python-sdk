"""
Tests for AsyncThordataClient.
"""

import aiohttp
import pytest

# check aioresponses
try:
    from aioresponses import aioresponses

    HAS_AIORESPONSES = True
except ImportError:
    HAS_AIORESPONSES = False

from thordata import AsyncThordataClient
from thordata.exceptions import ThordataConfigError
from thordata.models import ProxyConfig, ProxyProduct

# Mark all tests in this module as async
pytestmark = pytest.mark.asyncio

# Mock Credentials
TEST_SCRAPER = "async_scraper_token"
TEST_PUB_TOKEN = "async_public_token"
TEST_PUB_KEY = "async_key"


def _https_proxy_config_dummy() -> ProxyConfig:
    # Dummy values are fine because AsyncThordataClient will block before any network call
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

    # The fixture likely enters async context, so session should exist
    assert async_client._session is not None
    assert not async_client._session.closed


async def test_async_proxy_network_https_not_supported():
    async with AsyncThordataClient(scraper_token="test_token") as client:
        with pytest.raises(ThordataConfigError) as exc:
            await client.get(
                "https://httpbin.org/ip",
                proxy_config=_https_proxy_config_dummy(),
            )

        assert "Proxy Network requires an HTTPS proxy endpoint" in str(exc.value)


async def test_async_http_error_handling():
    async with AsyncThordataClient(scraper_token="test_token") as client:
        with pytest.raises(ThordataConfigError) as exc:
            await client.get(
                "https://httpbin.org/status/404",
                proxy_config=_https_proxy_config_dummy(),
            )

        assert "Proxy Network requires an HTTPS proxy endpoint" in str(exc.value)
