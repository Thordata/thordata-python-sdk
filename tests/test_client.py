"""
Tests for thordata.client module.
"""

from datetime import date
from unittest.mock import MagicMock, patch

import pytest

from thordata import ThordataClient
from thordata.exceptions import ThordataConfigError
from thordata.types import (
    CommonSettings,
    ProxyType,
    ScraperTaskConfig,
    SerpRequest,
    UniversalScrapeRequest,
    VideoTaskConfig,
)


def _mock_response(json_data, status_code=200, text="", content=None):
    r = MagicMock()
    r.status_code = status_code
    r.raise_for_status = MagicMock()
    r.json.return_value = json_data
    r.text = text or str(json_data)
    r.content = content or (text.encode() if text else b"")
    return r


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
        # 1. Init should succeed (Lazy validation)
        client = ThordataClient(scraper_token="")
        assert client is not None

        # 2. Method call should fail
        with pytest.raises(
            ThordataConfigError, match="scraper_token is required for SERP API"
        ):
            client.serp_search("test")

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


class TestClientInitEdgeCases:
    """Init validation and auth_mode."""

    def test_invalid_auth_mode_raises(self):
        with pytest.raises(ThordataConfigError, match="Invalid auth_mode"):
            ThordataClient(scraper_token="t", auth_mode="invalid")


class TestClientSERPAndUniversal:
    """SERP and Universal API success paths."""

    @pytest.fixture
    def client(self):
        return ThordataClient(
            scraper_token="st",
            public_token="pt",
            public_key="pk",
        )

    def test_serp_search_advanced_success(self, client):
        mock_r = _mock_response({"code": 200, "data": {"organic": []}})
        with patch.object(client, "_api_request_with_retry", return_value=mock_r):
            req = SerpRequest(query="test", engine="google")
            out = client.serp_search_advanced(req)
        assert "data" in out and "organic" in out["data"]
        assert out["data"]["organic"] == []

    def test_universal_scrape_advanced_success_html(self, client):
        mock_r = _mock_response({"code": 200, "html": "<body>ok</body>"})
        with patch.object(client, "_api_request_with_retry", return_value=mock_r):
            req = UniversalScrapeRequest(
                url="https://example.com", output_format="html"
            )
            out = client.universal_scrape_advanced(req)
        assert out == "<body>ok</body>"


class TestClientWebScraperTaskAPI:
    """Web Scraper task status, result, list, wait, run."""

    @pytest.fixture
    def client(self):
        return ThordataClient(
            scraper_token="st",
            public_token="pt",
            public_key="pk",
        )

    def test_get_task_status(self, client):
        mock_r = _mock_response(
            {
                "code": 200,
                "data": [{"task_id": "tid1", "status": "ready"}],
            }
        )
        with patch.object(client, "_api_request_with_retry", return_value=mock_r):
            status = client.get_task_status("tid1")
        assert status == "ready"

    def test_get_latest_task_status(self, client):
        mock_r = _mock_response(
            {"code": 200, "data": {"task_id": "t1", "status": "running"}}
        )
        with patch.object(client, "_api_request_with_retry", return_value=mock_r):
            data = client.get_latest_task_status()
        assert data["task_id"] == "t1" and data["status"] == "running"

    def test_safe_get_task_status_returns_error_on_failure(self, client):
        mock_r = _mock_response({"code": 401, "msg": "Unauthorized"})
        with patch.object(client, "_api_request_with_retry", return_value=mock_r):
            status = client.safe_get_task_status("tid1")
        assert status == "error"

    def test_get_task_result(self, client):
        mock_r = _mock_response(
            {"code": 200, "data": {"download": "https://cdn.example/out.json"}}
        )
        with patch.object(client, "_api_request_with_retry", return_value=mock_r):
            url = client.get_task_result("tid1", file_type="json")
        assert url == "https://cdn.example/out.json"

    def test_wait_for_task_returns_on_ready(self, client):
        with patch.object(client, "get_task_status", return_value="ready"):
            status = client.wait_for_task("tid1", poll_interval=0.1, max_wait=1.0)
        assert status == "ready"

    def test_run_task_success_path(self, client):
        with (
            patch.object(client, "create_scraper_task_advanced", return_value="tid1"),
            patch.object(client, "get_task_status", return_value="ready"),
            patch.object(client, "get_task_result", return_value="https://result.url"),
        ):
            result = client.run_task(
                "f.json",
                "spider_id",
                "spider_name",
                {"k": "v"},
                max_wait=2.0,
                initial_poll_interval=0.1,
            )
        assert result == "https://result.url"


class TestClientWebScraperTools:
    """Discovery and convenience helpers for Web Scraper tools."""

    @pytest.fixture
    def client(self):
        return ThordataClient(
            scraper_token="st",
            public_token="pt",
            public_key="pk",
        )

    def test_list_tools_and_groups_basic(self, client):
        out = client.list_tools()
        assert "tools" in out and "meta" in out
        assert isinstance(out["tools"], list)
        groups = client.get_tool_groups()
        assert "groups" in groups and "total" in groups

    def test_search_tools_keyword(self, client):
        out = client.search_tools("google")
        assert "tools" in out and "meta" in out
        # We don't assert specific tools here, just that it returns a list
        assert isinstance(out["tools"], list)

    def test_run_tool_by_key_uses_underlying_run_tool(self, client, monkeypatch):
        calls: list[dict] = []

        def _fake_run_tool(tool_request, file_name=None, universal_params=None):
            calls.append(
                {
                    "cls": type(tool_request),
                    "file_name": file_name,
                    "universal_params": universal_params,
                }
            )
            return "task-id-123"

        monkeypatch.setattr(client, "run_tool", _fake_run_tool)

        task_id = client.run_tool_by_key(
            "ecommerce.amazon_product_by-url",
            {"url": "https://example.com"},
            file_name="f.json",
            universal_params={"country": "us"},
        )
        assert task_id == "task-id-123"
        assert len(calls) == 1
        assert calls[0]["file_name"] == "f.json"
        assert calls[0]["universal_params"] == {"country": "us"}

    def test_run_tools_batch_validation_and_ok(self, client, monkeypatch):
        created: list[str] = []

        def _fake_run_tool_by_key(tool, params, file_name=None, universal_params=None):
            created.append(tool)
            return f"tid-{len(created)}"

        monkeypatch.setattr(client, "run_tool_by_key", _fake_run_tool_by_key)

        requests = [
            {
                "tool": "ecommerce.amazon_product_by-url",
                "params": {"url": "https://example.com/1"},
            },
            {
                "tool": "ecommerce.amazon_product_by-url",
                "params": {"url": "https://example.com/2"},
                "file_name": "f2.json",
            },
            {
                # Missing tool key should yield validation error
                "params": {"url": "https://example.com/3"},
            },
        ]
        results = client.run_tools_batch(requests, concurrency=2)
        assert len(results) == 3
        # First two should be ok
        assert results[0]["ok"] is True and results[0]["task_id"] == "tid-1"
        assert results[1]["ok"] is True and results[1]["task_id"] == "tid-2"
        # Third should be validation error
        assert results[2]["ok"] is False
        assert results[2]["error"]["type"] == "validation_error"


class TestClientUniversalBatch:
    """Universal Scrape batch helper."""

    @pytest.fixture
    def client(self):
        return ThordataClient(scraper_token="st")

    def test_universal_scrape_batch_mixed_requests(self, client, monkeypatch):
        # Patch advanced call to avoid real HTTP
        def _fake_universal_adv(req: UniversalScrapeRequest):
            return f"HTML for {req.url}"

        monkeypatch.setattr(client, "universal_scrape_advanced", _fake_universal_adv)

        req_obj = UniversalScrapeRequest(url="https://example.com/1")
        req_dict = {"url": "https://example.com/2", "js_render": True}
        results = client.universal_scrape_batch([req_obj, req_dict], concurrency=2)
        assert len(results) == 2
        assert results[0]["ok"] and results[0]["output"].startswith("HTML for")
        assert results[1]["ok"] and results[1]["output"].startswith("HTML for")


class TestClientAccountAndUsage:
    """Account, usage stats, traffic and wallet balance, proxy user usage."""

    @pytest.fixture
    def client(self):
        return ThordataClient(
            scraper_token="st",
            public_token="pt",
            public_key="pk",
        )

    def test_get_usage_statistics(self, client):
        mock_r = _mock_response(
            {
                "code": 200,
                "data": {
                    "total_usage_traffic": 1000,
                    "traffic_balance": 2000,
                    "query_days": 7,
                    "range_usage_traffic": 500,
                    "data": [],
                },
            }
        )
        with patch.object(client, "_api_request_with_retry", return_value=mock_r):
            stats = client.get_usage_statistics("2024-01-01", "2024-01-07")
        assert stats.total_usage_traffic == 1000
        assert stats.traffic_balance == 2000
        assert stats.query_days == 7

    def test_get_usage_statistics_with_date_objects(self, client):
        mock_r = _mock_response(
            {
                "code": 200,
                "data": {
                    "total_usage_traffic": 0,
                    "traffic_balance": 0,
                    "query_days": 0,
                    "range_usage_traffic": 0,
                    "data": [],
                },
            }
        )
        with patch.object(client, "_api_request_with_retry", return_value=mock_r):
            stats = client.get_usage_statistics(date(2024, 1, 1), date(2024, 1, 7))
        assert stats.query_days == 0

    def test_get_traffic_balance(self, client):
        mock_r = _mock_response({"code": 200, "data": {"traffic_balance": 123.45}})
        with patch.object(client, "_api_request_with_retry", return_value=mock_r):
            bal = client.get_traffic_balance()
        assert bal == 123.45

    def test_get_wallet_balance(self, client):
        mock_r = _mock_response({"code": 200, "data": {"balance": 99.99}})
        with patch.object(client, "_api_request_with_retry", return_value=mock_r):
            bal = client.get_wallet_balance()
        assert bal == 99.99

    def test_get_proxy_user_usage(self, client):
        mock_r = _mock_response(
            {"code": 200, "data": [{"date": "2024-01-01", "usage": 100}]}
        )
        with patch.object(client, "_api_request_with_retry", return_value=mock_r):
            out = client.get_proxy_user_usage("u1", "2024-01-01", "2024-01-07")
        assert len(out) == 1
        assert out[0]["date"] == "2024-01-01"

    def test_get_proxy_user_usage_hour(self, client):
        mock_r = _mock_response(
            {"code": 200, "data": {"data": [{"hour": "2024-01-01 12", "usage": 10}]}}
        )
        with patch.object(client, "_api_request_with_retry", return_value=mock_r):
            out = client.get_proxy_user_usage_hour(
                "u1", "2024-01-01 00", "2024-01-01 23"
            )
        assert len(out) == 1
        assert out[0]["hour"] == "2024-01-01 12"


class TestClientLocationsAndASN:
    """list_states, list_cities, list_asn (via _get_locations)."""

    @pytest.fixture
    def client(self):
        return ThordataClient(
            scraper_token="st",
            public_token="pt",
            public_key="pk",
        )

    def test_list_states(self, client):
        with patch.object(
            client,
            "_get_locations",
            return_value=[{"state_code": "wa", "state_name": "Washington"}],
        ):
            out = client.list_states("us")
        assert len(out) == 1
        assert out[0]["state_code"] == "wa"

    def test_list_cities(self, client):
        with patch.object(client, "_get_locations", return_value=[{"city": "Seattle"}]):
            out = client.list_cities("us", state_code="wa")
        assert len(out) == 1
        assert out[0]["city"] == "Seattle"

    def test_list_asn(self, client):
        with patch.object(
            client, "_get_locations", return_value=[{"asn": "12345", "name": "ASN1"}]
        ):
            out = client.list_asn("us")
        assert len(out) == 1
        assert out[0]["asn"] == "12345"


class TestClientWhitelist:
    """Whitelist IP add, delete, list."""

    @pytest.fixture
    def client(self):
        return ThordataClient(
            scraper_token="st",
            public_token="pt",
            public_key="pk",
        )

    def test_add_whitelist_ip(self, client):
        mock_r = _mock_response({"code": 200, "data": {"ip": "1.2.3.4"}})
        with patch.object(client, "_api_request_with_retry", return_value=mock_r):
            out = client.add_whitelist_ip("1.2.3.4", proxy_type=ProxyType.RESIDENTIAL)
        assert out["ip"] == "1.2.3.4"

    def test_delete_whitelist_ip(self, client):
        mock_r = _mock_response({"code": 200, "data": {}})
        with patch.object(client, "_api_request_with_retry", return_value=mock_r):
            out = client.delete_whitelist_ip("1.2.3.4")
        assert isinstance(out, dict)

    def test_list_whitelist_ips(self, client):
        mock_r = _mock_response({"code": 200, "data": ["1.2.3.4", "5.6.7.8"]})
        with patch.object(client, "_api_request_with_retry", return_value=mock_r):
            out = client.list_whitelist_ips()
        assert out == ["1.2.3.4", "5.6.7.8"]

    def test_list_whitelist_ips_dict_items(self, client):
        mock_r = _mock_response({"code": 200, "data": [{"ip": "1.2.3.4"}]})
        with patch.object(client, "_api_request_with_retry", return_value=mock_r):
            out = client.list_whitelist_ips()
        assert out == ["1.2.3.4"]


class TestClientProxyUsers:
    """Proxy user list, create, update, delete."""

    @pytest.fixture
    def client(self):
        return ThordataClient(
            scraper_token="st",
            public_token="pt",
            public_key="pk",
        )

    def test_list_proxy_users(self, client):
        mock_r = _mock_response(
            {
                "code": 200,
                "data": {
                    "limit": 10,
                    "remaining_limit": 5,
                    "user_count": 1,
                    "list": [
                        {
                            "username": "u1",
                            "password": "p1",
                            "status": "true",
                            "traffic_limit": 0,
                            "usage_traffic": 0,
                        }
                    ],
                },
            }
        )
        with patch.object(client, "_api_request_with_retry", return_value=mock_r):
            out = client.list_proxy_users()
        assert out.user_count == 1
        assert len(out.users) == 1
        assert out.users[0].username == "u1"

    def test_create_proxy_user(self, client):
        mock_r = _mock_response({"code": 200, "data": {"username": "newuser"}})
        with patch.object(client, "_api_request_with_retry", return_value=mock_r):
            out = client.create_proxy_user("newuser", "pass")
        assert out["username"] == "newuser"

    def test_update_proxy_user(self, client):
        mock_r = _mock_response({"code": 200, "data": {}})
        with patch.object(client, "_api_request_with_retry", return_value=mock_r):
            out = client.update_proxy_user("u1", "newpass")
        assert isinstance(out, dict)

    def test_delete_proxy_user(self, client):
        mock_r = _mock_response({"code": 200, "data": {}})
        with patch.object(client, "_api_request_with_retry", return_value=mock_r):
            out = client.delete_proxy_user("u1")
        assert isinstance(out, dict)


class TestClientProxyServersAndExpiration:
    """list_proxy_servers, get_proxy_expiration."""

    @pytest.fixture
    def client(self):
        return ThordataClient(
            scraper_token="st",
            public_token="pt",
            public_key="pk",
        )

    def test_list_proxy_servers(self, client):
        mock_r = _mock_response(
            {
                "code": 200,
                "data": [
                    {"ip": "1.2.3.4", "port": 9999, "username": "u", "password": "p"}
                ],
            }
        )
        with patch.object(client, "_api_request_with_retry", return_value=mock_r):
            out = client.list_proxy_servers(ProxyType.RESIDENTIAL)
        assert len(out) == 1
        assert out[0].ip == "1.2.3.4" and out[0].port == 9999

    def test_get_proxy_expiration(self, client):
        mock_r = _mock_response({"code": 200, "data": {"1.2.3.4": 1735689600}})
        with patch.object(client, "_api_request_with_retry", return_value=mock_r):
            out = client.get_proxy_expiration("1.2.3.4", ProxyType.RESIDENTIAL)
        assert out["1.2.3.4"] == 1735689600


class TestClientBrowserAndExtractIP:
    """get_browser_connection_url, extract_ip_list."""

    def test_get_browser_connection_url_from_args(self):
        client = ThordataClient(scraper_token="t")
        url = client.get_browser_connection_url(username="buser", password="bpass")
        assert "wss://" in url
        assert "td-customer" in url
        assert "buser" in url

    def test_get_browser_connection_url_missing_raises(self):
        client = ThordataClient(scraper_token="t")
        with (
            patch("thordata.client.os.getenv", return_value=None),
            pytest.raises(ThordataConfigError, match="Browser credentials missing"),
        ):
            client.get_browser_connection_url()

    def test_extract_ip_list_txt(self):
        client = ThordataClient(
            scraper_token="st",
            public_token="pt",
            public_key="pk",
        )
        mock_r = _mock_response({}, text="1.2.3.4:8080\r\n5.6.7.8:8080")
        mock_r.json.side_effect = ValueError("not json")
        with patch.object(client, "_api_request_with_retry", return_value=mock_r):
            out = client.extract_ip_list(num=2, return_type="txt", sep="\r\n")
        assert len(out) == 2
        assert "1.2.3.4:8080" in out and "5.6.7.8:8080" in out

    def test_extract_ip_list_json(self):
        client = ThordataClient(
            scraper_token="st",
            public_token="pt",
            public_key="pk",
        )
        mock_r = _mock_response(
            {
                "code": 200,
                "data": [
                    {"ip": "1.2.3.4", "port": 8080},
                    {"ip": "5.6.7.8", "port": 8080},
                ],
            }
        )
        with patch.object(client, "_api_request_with_retry", return_value=mock_r):
            out = client.extract_ip_list(num=2, return_type="json")
        assert len(out) == 2
        assert any("1.2.3.4" in s for s in out)
        assert any("5.6.7.8" in s for s in out)

    def test_extract_ip_list_unlimited_uses_unlimited_api_and_username(self):
        client = ThordataClient(
            scraper_token="st",
            public_token="pt",
            public_key="pk",
        )
        mock_r = _mock_response(
            {"code": 200, "data": [{"ip": "1.2.3.4", "port": 9999}]}
        )
        with (
            patch.object(client, "_api_request_with_retry", return_value=mock_r) as m,
            patch(
                "thordata.client.os.getenv",
                side_effect=lambda k, d=None: {
                    "THORDATA_UNLIMITED_USERNAME": "unlimited_user"
                }.get(k, d),
            ),
        ):
            out = client.extract_ip_list(num=1, return_type="json", product="unlimited")
        assert len(out) == 1
        call_args = m.call_args
        assert "unlimited_api" in str(call_args[0][1])
        if call_args[1].get("params"):
            assert call_args[1]["params"].get("td-customer") == "unlimited_user"


class TestClientCreateTask:
    """create_scraper_task, create_scraper_task_advanced, create_video_task."""

    @pytest.fixture
    def client(self):
        return ThordataClient(
            scraper_token="st",
            public_token="pt",
            public_key="pk",
        )

    def test_create_scraper_task(self, client):
        mock_r = _mock_response({"code": 200, "data": {"task_id": "tid123"}})
        with patch.object(client, "_api_request_with_retry", return_value=mock_r):
            task_id = client.create_scraper_task(
                "f.json", "spider_id", "spider_name", {"k": "v"}
            )
        assert task_id == "tid123"

    def test_create_scraper_task_advanced(self, client):
        mock_r = _mock_response({"code": 200, "data": {"task_id": "adv_tid"}})
        cfg = ScraperTaskConfig(
            file_name="f.json",
            spider_id="sid",
            spider_name="sname",
            parameters={"x": 1},
        )
        with patch.object(client, "_api_request_with_retry", return_value=mock_r):
            task_id = client.create_scraper_task_advanced(cfg)
        assert task_id == "adv_tid"

    def test_create_video_task_advanced(self, client):
        mock_r = _mock_response({"code": 200, "data": {"task_id": "vid_tid"}})
        cfg = VideoTaskConfig(
            file_name="v.json",
            spider_id="vid",
            spider_name="vname",
            parameters={},
            common_settings=CommonSettings(),
        )
        with patch.object(client, "_api_request_with_retry", return_value=mock_r):
            task_id = client.create_video_task_advanced(cfg)
        assert task_id == "vid_tid"
