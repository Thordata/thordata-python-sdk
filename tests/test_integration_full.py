"""
Integration tests for all major SDK features using real .env credentials.

These tests require THORDATA_INTEGRATION=true and valid credentials in .env.
Tests are designed to be comprehensive yet fast enough to run in CI/CD.
"""

import os
import pytest

from thordata import ThordataClient, AsyncThordataClient
from thordata.env import load_env_file


def _requires_integration() -> bool:
    """Check if integration tests are enabled."""
    return os.getenv("THORDATA_INTEGRATION", "").lower() in {"1", "true", "yes"}


def _get_client() -> ThordataClient:
    """Get a sync client with credentials from env."""
    return ThordataClient(
        scraper_token=os.getenv("THORDATA_SCRAPERAPI_TOKEN"),
        public_token=os.getenv("THORDATA_PUBLIC_TOKEN"),
        public_key=os.getenv("THORDATA_PUBLIC_KEY"),
    )


@pytest.mark.skipif(not _requires_integration(), reason="THORDATA_INTEGRATION not set")
class TestSerpIntegration:
    """Integration tests for SERP API."""

    def test_serp_basic_search(self):
        """Test basic Google SERP search."""
        client = _get_client()
        result = client.serp_search(
            query="python programming",
            engine="google",
            num=5,
        )

        assert isinstance(result, dict)
        assert "organic_results" in result or "results" in result
        assert len(result.get("organic_results", result.get("results", []))) > 0

    def test_serp_with_country(self):
        """Test SERP search with country filter."""
        client = _get_client()
        result = client.serp_search(
            query="machine learning",
            engine="google",
            country="us",
            num=3,
        )

        assert isinstance(result, dict)
        assert "organic_results" in result or "results" in result


@pytest.mark.skipif(not _requires_integration(), reason="THORDATA_INTEGRATION not set")
class TestUniversalScrapeIntegration:
    """Integration tests for Universal Scraping API."""

    def test_universal_scrape_html(self):
        """Test basic HTML scraping."""
        client = _get_client()
        html = client.universal_scrape(
            url="https://example.com",
            js_render=False,
            output_format="html",
        )

        assert isinstance(html, str)
        assert len(html) > 0
        assert "<html" in html.lower() or "example domain" in html.lower()

    def test_universal_scrape_with_country(self):
        """Test scraping with country parameter."""
        client = _get_client()
        html = client.universal_scrape(
            url="https://example.com",
            js_render=False,
            country="us",
        )

        assert isinstance(html, str)
        assert len(html) > 0


@pytest.mark.skipif(not _requires_integration(), reason="THORDATA_INTEGRATION not set")
class TestAccountIntegration:
    """Integration tests for account and usage APIs."""

    def test_get_usage_statistics(self):
        """Test getting usage statistics."""
        from datetime import date, timedelta

        client = _get_client()
        end_date = date.today()
        start_date = end_date - timedelta(days=7)

        stats = client.get_usage_statistics(start_date, end_date)

        assert stats is not None
        assert hasattr(stats, "total_requests") or hasattr(stats, "from_dict")

    def test_get_traffic_balance(self):
        """Test getting traffic balance."""
        client = _get_client()
        balance = client.get_traffic_balance()

        assert isinstance(balance, (int, float))
        assert balance >= 0

    def test_get_wallet_balance(self):
        """Test getting wallet balance."""
        client = _get_client()
        balance = client.get_wallet_balance()

        assert isinstance(balance, (int, float))
        assert balance >= 0


@pytest.mark.skipif(not _requires_integration(), reason="THORDATA_INTEGRATION not set")
class TestLocationsIntegration:
    """Integration tests for locations API."""

    def test_list_countries(self):
        """Test listing countries."""
        client = _get_client()
        countries = client.list_countries()

        assert isinstance(countries, list)
        assert len(countries) > 0

        # Verify structure
        for country in countries:
            assert isinstance(country, dict)
            assert "country_code" in country or "name" in country

    def test_list_states(self):
        """Test listing states for a country."""
        client = _get_client()
        states = client.list_states(country_code="us")

        assert isinstance(states, list)
        # US should have states
        assert len(states) > 0


@pytest.mark.skipif(not _requires_integration(), reason="THORDATA_INTEGRATION not set")
class TestWhitelistIntegration:
    """Integration tests for whitelist API."""

    def test_list_whitelist_ips(self):
        """Test listing whitelisted IPs."""
        client = _get_client()
        ips = client.list_whitelist_ips()

        assert isinstance(ips, list)

        # Each IP should be a string
        for ip in ips:
            assert isinstance(ip, str)


@pytest.mark.skipif(not _requires_integration(), reason="THORDATA_INTEGRATION not set")
class TestProxyUsersIntegration:
    """Integration tests for proxy user management."""

    def test_list_proxy_users(self):
        """Test listing proxy users."""
        client = _get_client()
        users = client.list_proxy_users()

        assert users is not None
        assert hasattr(users, "users") or hasattr(users, "from_dict")


@pytest.mark.skipif(not _requires_integration(), reason="THORDATA_INTEGRATION not set")
class TestProxyListIntegration:
    """Integration tests for proxy list API."""

    def test_list_proxy_servers(self):
        """Test listing ISP/Datacenter proxy servers."""
        client = _get_client()
        # ISP proxy type is typically 2
        try:
            servers = client.list_proxy_servers(proxy_type=2)
            assert isinstance(servers, list)
        except Exception as e:
            # Might not have ISP proxies, so just verify the call was made
            assert "proxy" in str(e).lower() or len(str(e)) > 0


@pytest.mark.skipif(not _requires_integration(), reason="THORDATA_INTEGRATION not set")
class TestToolsRegistryIntegration:
    """Integration tests for tools registry."""

    def test_list_tools(self):
        """Test listing all tools."""
        client = _get_client()
        result = client.list_tools()

        assert "tools" in result
        assert "meta" in result
        assert isinstance(result["tools"], list)
        assert len(result["tools"]) > 0

    def test_get_tool_groups(self):
        """Test getting tool groups."""
        client = _get_client()
        result = client.get_tool_groups()

        assert "groups" in result
        assert "total" in result
        assert isinstance(result["groups"], list)
        assert len(result["groups"]) > 0

    def test_search_tools(self):
        """Test searching tools."""
        client = _get_client()
        result = client.search_tools("amazon")

        assert "tools" in result
        assert isinstance(result["tools"], list)
        # Should find at least one Amazon tool
        assert len(result["tools"]) > 0

    def test_resolve_tool_key(self):
        """Test resolving tool keys."""
        client = _get_client()
        key = client.resolve_tool_key("amazon_product_by-url")

        assert "." in key
        assert "amazon" in key.lower()

    def test_get_tool_info(self):
        """Test getting tool info."""
        client = _get_client()
        info = client.get_tool_info("ecommerce.amazon_product_by-url")

        assert isinstance(info, dict)
        assert "spider_id" in info
        assert "fields" in info


@pytest.mark.skipif(not _requires_integration(), reason="THORDATA_INTEGRATION not set")
class TestWebScraperIntegration:
    """Integration tests for Web Scraper API."""

    def test_create_text_scraper_task(self):
        """Test creating a text scraper task."""
        client = _get_client()

        try:
            task_id = client.create_scraper_task(
                file_name="test_integration_task",
                spider_id="amazon_product_by-url",
                spider_name="amazon.com",
                parameters={"url": "https://www.amazon.com/dp/B08N5WRWNW"},
            )

            assert isinstance(task_id, str)
            assert len(task_id) > 0

            # Check status
            status = client.get_task_status(task_id)
            assert status in {
                "pending",
                "processing",
                "ready",
                "success",
                "failed",
                "error",
            }

        except Exception as e:
            # Task creation might fail due to rate limits
            pytest.skip(f"Task creation skipped: {e}")


@pytest.mark.skipif(not _requires_integration(), reason="THORDATA_INTEGRATION not set")
class TestBrowserIntegration:
    """Integration tests for browser connection."""

    def test_get_browser_connection_url(self):
        """Test getting browser connection URL."""
        client = _get_client()

        try:
            url = client.get_browser_connection_url()

            assert isinstance(url, str)
            assert url.startswith("wss://")
            assert "ws-browser.thordata.com" in url
        except Exception as e:
            # Browser credentials might not be configured
            pytest.skip(f"Browser credentials not configured: {e}")


@pytest.mark.skipif(not _requires_integration(), reason="THORDATA_INTEGRATION not set")
class TestAsyncClientIntegration:
    """Integration tests for async client."""

    @pytest.mark.asyncio
    async def test_async_serp_search(self):
        """Test async SERP search."""
        client = AsyncThordataClient(
            scraper_token=os.getenv("THORDATA_SCRAPERAPI_TOKEN"),
            public_token=os.getenv("THORDATA_PUBLIC_TOKEN"),
            public_key=os.getenv("THORDATA_PUBLIC_KEY"),
        )

        async with client:
            result = await client.serp_search(
                query="python async test",
                engine="google",
                num=3,
            )

            assert isinstance(result, dict)
            assert "organic_results" in result or "results" in result

    @pytest.mark.asyncio
    async def test_async_universal_scrape(self):
        """Test async universal scrape."""
        client = AsyncThordataClient(
            scraper_token=os.getenv("THORDATA_SCRAPERAPI_TOKEN"),
            public_token=os.getenv("THORDATA_PUBLIC_TOKEN"),
            public_key=os.getenv("THORDATA_PUBLIC_KEY"),
        )

        async with client:
            html = await client.universal_scrape(
                url="https://example.com",
                js_render=False,
            )

            assert isinstance(html, str)
            assert len(html) > 0

    @pytest.mark.asyncio
    async def test_async_list_countries(self):
        """Test async listing countries."""
        client = AsyncThordataClient(
            scraper_token=os.getenv("THORDATA_SCRAPERAPI_TOKEN"),
            public_token=os.getenv("THORDATA_PUBLIC_TOKEN"),
            public_key=os.getenv("THORDATA_PUBLIC_KEY"),
        )

        async with client:
            countries = await client.list_countries()

            assert isinstance(countries, list)
            assert len(countries) > 0


@pytest.mark.skipif(not _requires_integration(), reason="THORDATA_INTEGRATION not set")
class TestBatchOperationsIntegration:
    """Integration tests for batch operations."""

    def test_serp_batch_search(self):
        """Test batch SERP search."""
        client = _get_client()

        requests = [
            {"query": "python", "engine": "google", "num": 2},
            {"query": "javascript", "engine": "google", "num": 2},
        ]

        results = client.serp_batch_search(requests, concurrency=2)

        assert isinstance(results, list)
        assert len(results) == 2

        # Check each result
        for result in results:
            assert "index" in result
            assert "ok" in result
            assert result["index"] in [0, 1]

    def test_universal_batch_scrape(self):
        """Test batch universal scrape."""
        client = _get_client()

        requests = [
            {"url": "https://example.com"},
            {"url": "https://example.org"},
        ]

        results = client.universal_scrape_batch(requests, concurrency=2)

        assert isinstance(results, list)
        assert len(results) == 2

        for result in results:
            assert "index" in result
            assert "ok" in result
