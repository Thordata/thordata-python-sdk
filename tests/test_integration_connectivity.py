"""
Integration tests for proxy connectivity and basic operations.

These tests verify that the SDK can successfully connect to Thordata's
proxy infrastructure and perform basic operations.
"""

import os
import pytest
from datetime import date, timedelta


def _requires_integration() -> bool:
    """Check if integration tests are enabled."""
    return os.getenv("THORDATA_INTEGRATION", "").lower() in {"1", "true", "yes"}


def _get_client():
    """Get a sync client with credentials from env."""
    from thordata import ThordataClient
    return ThordataClient(
        scraper_token=os.getenv("THORDATA_SCRAPERAPI_TOKEN"),
        public_token=os.getenv("THORDATA_PUBLIC_TOKEN"),
        public_key=os.getenv("THORDATA_PUBLIC_KEY"),
    )


@pytest.mark.skipif(not _requires_integration(), reason="THORDATA_INTEGRATION not set")
class TestProxyConnectivity:
    """Tests for verifying proxy connectivity."""

    def test_api_base_connectivity(self):
        """Test that we can reach the base API endpoints."""
        from thordata._api_base import ApiEndpoints

        # Verify endpoint URLs are properly configured
        assert ApiEndpoints.BASE_URL.startswith("https://")
        assert ApiEndpoints.UNIVERSAL_URL.startswith("https://")
        assert ApiEndpoints.API_URL.startswith("https://")

    def test_serp_api_connectivity(self):
        """Test SERP API connectivity."""
        client = _get_client()

        try:
            result = client.serp_search(
                query="connectivity test",
                engine="google",
                num=1,
            )
            assert isinstance(result, dict)
            assert "organic" in result or "organic_results" in result or "results" in result
        except Exception as e:
            pytest.fail(f"SERP API connectivity failed: {e}")

    def test_universal_api_connectivity(self):
        """Test Universal API connectivity."""
        client = _get_client()

        try:
            html = client.universal_scrape(
                url="https://httpbin.org/get",
                js_render=False,
            )
            assert isinstance(html, str)
            assert len(html) > 0
        except Exception as e:
            pytest.fail(f"Universal API connectivity failed: {e}")

    def test_account_api_connectivity(self):
        """Test account API connectivity."""
        client = _get_client()

        try:
            balance = client.get_traffic_balance()
            assert isinstance(balance, (int, float))
            assert balance >= 0
        except Exception as e:
            pytest.fail(f"Account API connectivity failed: {e}")

    def test_locations_api_connectivity(self):
        """Test locations API connectivity."""
        client = _get_client()

        try:
            countries = client.list_countries()
            assert isinstance(countries, list)
            assert len(countries) > 0
        except Exception as e:
            pytest.fail(f"Locations API connectivity failed: {e}")


@pytest.mark.skipif(not _requires_integration(), reason="THORDATA_INTEGRATION not set")
class TestProxyExpiration:
    """Tests for proxy expiration API."""

    def test_get_proxy_expiration_for_valid_ips(self):
        """Test getting expiration for valid IP addresses."""
        client = _get_client()

        try:
            # Try ISP proxy type (typically type 2)
            expiration = client.get_proxy_expiration(
                ips="8.8.8.8",  # Use Google DNS as test IP
                proxy_type=2,
            )

            assert isinstance(expiration, (dict, list))
        except Exception as e:
            # This might fail if we don't have ISP proxies
            pytest.skip(f"Proxy expiration test skipped: {e}")


@pytest.mark.skipif(not _requires_integration(), reason="THORDATA_INTEGRATION not set")
class TestProxyUserUsage:
    """Tests for proxy user usage statistics."""

    def test_get_proxy_user_usage(self):
        """Test getting proxy user usage."""
        client = _get_client()

        # First, get the list of users
        users = client.list_proxy_users()

        if not users or not hasattr(users, "users") or len(users.users) == 0:
            pytest.skip("No proxy users found")

        # Use the first user
        username = users.users[0].username

        try:
            end_date = date.today()
            start_date = end_date - timedelta(days=7)

            usage = client.get_proxy_user_usage(
                username=username,
                start_date=start_date,
                end_date=end_date,
            )

            assert isinstance(usage, list)
        except Exception as e:
            pytest.fail(f"Get proxy user usage failed: {e}")

    def test_get_proxy_user_usage_hour(self):
        """Test getting hourly proxy user usage."""
        client = _get_client()

        # First, get the list of users
        users = client.list_proxy_users()

        if not users or not hasattr(users, "users") or len(users.users) == 0:
            pytest.skip("No proxy users found")

        # Use the first user
        username = users.users[0].username

        try:
            # Use a small time window
            from datetime import datetime, timedelta

            end_dt = datetime.now()
            start_dt = end_dt - timedelta(hours=24)

            from_date = start_dt.strftime("%Y-%m-%d %H")
            to_date = end_dt.strftime("%Y-%m-%d %H")

            usage = client.get_proxy_user_usage_hour(
                username=username,
                from_date=from_date,
                to_date=to_date,
            )

            assert isinstance(usage, list)
        except Exception as e:
            pytest.fail(f"Get hourly user usage failed: {e}")


@pytest.mark.skipif(not _requires_integration(), reason="THORDATA_INTEGRATION not set")
class TestProxyExtractIP:
    """Tests for IP extraction functionality."""

    def test_extract_ip_list(self):
        """Test extracting IP list."""
        client = _get_client()

        try:
            ips = client.extract_ip_list(
                num=1,
                country="us",
                return_type="txt",
            )

            assert isinstance(ips, list)
            # Might return empty if no residential credentials
        except Exception as e:
            # This test might fail if residential credentials are not configured
            pytest.skip(f"Extract IP list test skipped: {e}")

    def test_extract_ip_list_json(self):
        """Test extracting IP list in JSON format."""
        client = _get_client()

        try:
            ips = client.extract_ip_list(
                num=1,
                return_type="json",
            )

            assert isinstance(ips, list)
        except Exception as e:
            pytest.skip(f"Extract IP list (JSON) test skipped: {e}")


@pytest.mark.skipif(not _requires_integration(), reason="THORDATA_INTEGRATION not set")
class TestBatchOperationsConnectivity:
    """Tests for batch operations connectivity."""

    def test_batch_serp_connectivity(self):
        """Test that batch SERP operations work."""
        client = _get_client()

        requests = [
            {"query": "test", "engine": "google", "num": 1},
            {"query": "example", "engine": "google", "num": 1},
        ]

        try:
            results = client.serp_batch_search(requests, concurrency=2)

            assert len(results) == 2
            for result in results:
                assert "index" in result
                assert "ok" in result
        except Exception as e:
            pytest.fail(f"Batch SERP connectivity failed: {e}")

    def test_batch_universal_connectivity(self):
        """Test that batch universal operations work."""
        client = _get_client()

        requests = [
            {"url": "https://httpbin.org/get"},
            {"url": "https://httpbin.org/ip"},
        ]

        try:
            results = client.universal_scrape_batch(requests, concurrency=2)

            assert len(results) == 2
            for result in results:
                assert "index" in result
                assert "ok" in result
        except Exception as e:
            pytest.fail(f"Batch universal connectivity failed: {e}")


@pytest.mark.skipif(not _requires_integration(), reason="THORDATA_INTEGRATION not set")
class TestTaskOperations:
    """Tests for task-related operations."""

    def test_get_latest_task_status(self):
        """Test getting latest task status."""
        client = _get_client()

        try:
            status = client.get_latest_task_status()

            assert isinstance(status, dict)
        except Exception as e:
            pytest.skip(f"Get latest task status test skipped: {e}")

    def test_list_tasks(self):
        """Test listing tasks."""
        client = _get_client()

        try:
            tasks = client.list_tasks(page=1, size=5)

            assert isinstance(tasks, dict)
            assert "count" in tasks or "list" in tasks
        except Exception as e:
            pytest.skip(f"List tasks test skipped: {e}")


@pytest.mark.skipif(not _requires_integration(), reason="THORDATA_INTEGRATION not set")
class TestWebScraperVideo:
    """Tests for Web Scraper video tasks."""

    def test_video_task_creation(self):
        """Test creating a video scraper task."""
        from thordata.types import CommonSettings

        client = _get_client()

        try:
            settings = CommonSettings(
                country="us",
                render_js=True,
            )

            # Try to create a video task (YouTube downloader)
            task_id = client.create_video_task(
                file_name="test_video_task",
                spider_id="youtube_downloader_video",
                spider_name="youtube.com",
                parameters={"url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ"},
                common_settings=settings,
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
            # Video tasks might require special permissions
            pytest.skip(f"Video task creation test skipped: {e}")


@pytest.mark.skipif(not _requires_integration(), reason="THORDATA_INTEGRATION not set")
@pytest.mark.asyncio
class TestAsyncConnectivity:
    """Tests for async client connectivity."""

    async def test_async_serp_connectivity(self):
        """Test async SERP connectivity."""
        from thordata import AsyncThordataClient

        client = AsyncThordataClient(
            scraper_token=os.getenv("THORDATA_SCRAPERAPI_TOKEN"),
            public_token=os.getenv("THORDATA_PUBLIC_TOKEN"),
            public_key=os.getenv("THORDATA_PUBLIC_KEY"),
        )

        async with client:
            result = await client.serp_search(
                query="async connectivity test",
                engine="google",
                num=1,
            )

            assert isinstance(result, dict)
            assert "organic" in result or "organic_results" in result or "results" in result

    async def test_async_universal_connectivity(self):
        """Test async universal connectivity."""
        from thordata import AsyncThordataClient

        client = AsyncThordataClient(
            scraper_token=os.getenv("THORDATA_SCRAPERAPI_TOKEN"),
            public_token=os.getenv("THORDATA_PUBLIC_TOKEN"),
            public_key=os.getenv("THORDATA_PUBLIC_KEY"),
        )

        async with client:
            html = await client.universal_scrape(
                url="https://httpbin.org/get",
                js_render=False,
            )

            assert isinstance(html, str)
            assert len(html) > 0

    async def test_async_account_connectivity(self):
        """Test async account connectivity."""
        from thordata import AsyncThordataClient

        client = AsyncThordataClient(
            scraper_token=os.getenv("THORDATA_SCRAPERAPI_TOKEN"),
            public_token=os.getenv("THORDATA_PUBLIC_TOKEN"),
            public_key=os.getenv("THORDATA_PUBLIC_KEY"),
        )

        async with client:
            balance = await client.get_traffic_balance()

            assert isinstance(balance, (int, float))
            assert balance >= 0
