"""
Tests for thordata.client module.
"""

from unittest.mock import MagicMock, patch

import pytest

from thordata import ThordataClient
from thordata.exceptions import ThordataConfigError


class TestClientInitialization:
    """Tests for ThordataClient initialization."""

    def test_basic_init(self):
        """Test basic client initialization."""
        client = ThordataClient(scraper_token="test_token")
        assert client.scraper_token == "test_token"
        assert client.public_token is None
        assert client.public_key is None

    def test_full_init(self):
        """Test client initialization with all parameters."""
        client = ThordataClient(
            scraper_token="scraper",
            public_token="public",
            public_key="key",
            timeout=60,
        )
        assert client.scraper_token == "scraper"
        assert client.public_token == "public"
        assert client.public_key == "key"

    def test_missing_scraper_token(self):
        """Test that missing scraper_token raises error."""
        with pytest.raises(ThordataConfigError, match="scraper_token is required"):
            ThordataClient(scraper_token="")

    def test_context_manager(self):
        """Test client as context manager."""
        with ThordataClient(scraper_token="test") as client:
            assert client is not None


class TestClientMethods:
    """Tests for ThordataClient methods."""

    @pytest.fixture
    def client(self):
        """Create a client for testing."""
        return ThordataClient(
            scraper_token="test_token",
            public_token="pub_token",
            public_key="pub_key",
        )

    def test_build_proxy_url(self, client):
        """Test build_proxy_url method."""
        url = client.build_proxy_url(
            username="testuser",
            password="testpass",
            country="us",
            city="seattle",
        )
        assert "td-customer-testuser" in url
        assert "country-us" in url
        assert "city-seattle" in url
        assert "testpass" in url

    @patch.object(ThordataClient, "_get_locations")
    def test_list_countries(self, mock_get_locations, client):
        """Test list_countries method."""
        mock_get_locations.return_value = [
            {"country_code": "us", "country_name": "United States"},
        ]

        result = client.list_countries()

        mock_get_locations.assert_called_once()
        assert len(result) == 1
        assert result[0]["country_code"] == "us"

    def test_require_public_credentials(self):
        """Test that methods requiring public credentials raise error."""
        client = ThordataClient(scraper_token="test")

        with pytest.raises(ThordataConfigError, match="public_token and public_key"):
            client.get_task_status("some_task_id")

    def test_list_tasks(self, client):
        """Test list_tasks method."""
        # Mock the _api_request_with_retry method directly
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.raise_for_status = MagicMock()
        mock_response.json.return_value = {
            "code": 200,
            "data": {
                "count": 5,
                "list": [
                    {"task_id": "task_1", "status": "ready"},
                    {"task_id": "task_2", "status": "running"},
                ],
            },
        }

        with patch.object(
            client, "_api_request_with_retry", return_value=mock_response
        ):
            result = client.list_tasks(page=1, size=10)

        assert result["count"] == 5
        assert len(result["list"]) == 2
