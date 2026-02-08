"""
Unit tests for namespace system.
"""

import pytest

from thordata import AsyncThordataClient, ThordataClient
from thordata.namespaces import (
    AccountNamespace,
    ProxyNamespace,
    UniversalNamespace,
    WebScraperNamespace,
)


class TestNamespaces:
    """Test namespace initialization."""

    def test_sync_client_namespaces(self):
        client = ThordataClient()
        assert hasattr(client, "universal")
        assert hasattr(client, "scraper")
        assert hasattr(client, "account")
        assert hasattr(client, "proxy")
        assert isinstance(client.universal, UniversalNamespace)
        assert isinstance(client.scraper, WebScraperNamespace)
        assert isinstance(client.account, AccountNamespace)
        assert isinstance(client.proxy, ProxyNamespace)

    @pytest.mark.asyncio
    async def test_async_client_namespaces(self):
        async with AsyncThordataClient() as client:
            assert hasattr(client, "universal")
            assert hasattr(client, "scraper")
            assert hasattr(client, "account")
            assert hasattr(client, "proxy")
            assert isinstance(client.universal, UniversalNamespace)
            assert isinstance(client.scraper, WebScraperNamespace)
            assert isinstance(client.account, AccountNamespace)
            assert isinstance(client.proxy, ProxyNamespace)

    def test_namespace_async_detection(self):
        sync_client = ThordataClient()
        assert not sync_client.universal._is_async

        # Note: We can't easily test async client without async context
        # But the namespace should detect it correctly


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
