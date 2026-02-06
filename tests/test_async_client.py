"""
Tests for AsyncThordataClient.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from thordata import AsyncThordataClient
from thordata.exceptions import ThordataConfigError, ThordataNetworkError
from thordata.models import ProxyConfig, ProxyProduct
from thordata.types import (
    CommonSettings,
    ProxyType,
    ScraperTaskConfig,
    SerpRequest,
    UniversalScrapeRequest,
    VideoTaskConfig,
)

# Mark all tests in this module as async
pytestmark = pytest.mark.asyncio


def _async_response_with_json(json_data):
    """Build a mock aiohttp response that returns json_data from await .json()."""
    resp = MagicMock()
    resp.json = AsyncMock(return_value=json_data)
    resp.raise_for_status = MagicMock()
    resp.status = 200
    return resp


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
        with pytest.raises(
            ThordataConfigError, match="scraper_token is required for SERP API"
        ):
            await client.serp_search("test")


# ---------- Coverage: API methods via mocked _http.request ----------


async def test_async_invalid_auth_mode_raises():
    with pytest.raises(ThordataConfigError, match="Invalid auth_mode"):
        AsyncThordataClient(scraper_token="t", auth_mode="invalid")


@pytest.fixture
async def async_client_coverage():
    """Client with session for coverage tests; closed after test."""
    client = AsyncThordataClient(scraper_token="st", public_token="pt", public_key="pk")
    await client._http._ensure_session()
    yield client
    await client.close()


async def test_async_serp_search_advanced_success(async_client_coverage):
    client = async_client_coverage
    mock_resp = _async_response_with_json({"code": 200, "data": {"organic": []}})
    with patch.object(
        client._http, "request", new_callable=AsyncMock, return_value=mock_resp
    ):
        req = SerpRequest(query="test", engine="google")
        out = await client.serp_search_advanced(req)
    assert "data" in out and "organic" in out["data"]


async def test_async_universal_scrape_advanced_success(async_client_coverage):
    client = async_client_coverage
    mock_resp = _async_response_with_json({"code": 200, "html": "<body>ok</body>"})
    with patch.object(
        client._http, "request", new_callable=AsyncMock, return_value=mock_resp
    ):
        req = UniversalScrapeRequest(url="https://example.com", output_format="html")
        out = await client.universal_scrape_advanced(req)
    assert out == "<body>ok</body>"


async def test_async_get_task_status(async_client_coverage):
    client = async_client_coverage
    mock_resp = _async_response_with_json(
        {
            "code": 200,
            "data": [{"task_id": "tid1", "status": "ready"}],
        }
    )
    with patch.object(
        client._http, "request", new_callable=AsyncMock, return_value=mock_resp
    ):
        status = await client.get_task_status("tid1")
    assert status == "ready"


async def test_async_safe_get_task_status_returns_error_on_failure(
    async_client_coverage,
):
    client = async_client_coverage
    mock_resp = _async_response_with_json({"code": 401, "msg": "Unauthorized"})
    with patch.object(
        client._http, "request", new_callable=AsyncMock, return_value=mock_resp
    ):
        status = await client.safe_get_task_status("tid1")
    assert status == "error"


async def test_async_get_task_result(async_client_coverage):
    client = async_client_coverage
    mock_resp = _async_response_with_json(
        {
            "code": 200,
            "data": {"download": "https://cdn.example/out.json"},
        }
    )
    with patch.object(
        client._http, "request", new_callable=AsyncMock, return_value=mock_resp
    ):
        url = await client.get_task_result("tid1", file_type="json")
    assert url == "https://cdn.example/out.json"


async def test_async_list_tasks(async_client_coverage):
    client = async_client_coverage
    mock_resp = _async_response_with_json(
        {
            "code": 200,
            "data": {"count": 2, "list": [{"task_id": "t1"}, {"task_id": "t2"}]},
        }
    )
    with patch.object(
        client._http, "request", new_callable=AsyncMock, return_value=mock_resp
    ):
        out = await client.list_tasks(page=1, size=10)
    assert out["count"] == 2 and len(out["list"]) == 2


async def test_async_wait_for_task_returns_on_ready(async_client_coverage):
    client = async_client_coverage
    with patch.object(
        client, "get_task_status", new_callable=AsyncMock, return_value="ready"
    ):
        status = await client.wait_for_task("tid1", poll_interval=0.01, max_wait=1.0)
    assert status == "ready"


async def test_async_get_usage_statistics(async_client_coverage):
    client = async_client_coverage
    mock_resp = _async_response_with_json(
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
    with patch.object(
        client._http, "request", new_callable=AsyncMock, return_value=mock_resp
    ):
        stats = await client.get_usage_statistics("2024-01-01", "2024-01-07")
    assert stats.total_usage_traffic == 1000 and stats.traffic_balance == 2000


async def test_async_get_traffic_balance(async_client_coverage):
    client = async_client_coverage
    mock_resp = _async_response_with_json(
        {"code": 200, "data": {"traffic_balance": 123.45}}
    )
    with patch.object(
        client._http, "request", new_callable=AsyncMock, return_value=mock_resp
    ):
        bal = await client.get_traffic_balance()
    assert bal == 123.45


async def test_async_get_wallet_balance(async_client_coverage):
    client = async_client_coverage
    mock_resp = _async_response_with_json({"code": 200, "data": {"balance": 99.99}})
    with patch.object(
        client._http, "request", new_callable=AsyncMock, return_value=mock_resp
    ):
        bal = await client.get_wallet_balance()
    assert bal == 99.99


async def test_async_list_tools_and_groups(async_client_coverage):
    """Async tool discovery helpers should return structured metadata."""
    client = async_client_coverage
    out = await client.list_tools()
    assert "tools" in out and "meta" in out
    groups = await client.get_tool_groups()
    assert "groups" in groups and "total" in groups


async def test_async_run_tool_by_key_uses_underlying_run_tool(
    async_client_coverage, monkeypatch
):
    client = async_client_coverage
    calls: list[dict] = []

    async def _fake_run_tool(tool_request, file_name=None, universal_params=None):
        calls.append(
            {
                "cls": type(tool_request),
                "file_name": file_name,
                "universal_params": universal_params,
            }
        )
        return "task-id-async"

    monkeypatch.setattr(client, "run_tool", _fake_run_tool)

    task_id = await client.run_tool_by_key(
        "ecommerce.amazon_product_by-url",
        {"url": "https://example.com"},
        file_name="async.json",
        universal_params={"country": "us"},
    )
    assert task_id == "task-id-async"
    assert len(calls) == 1
    assert calls[0]["file_name"] == "async.json"
    assert calls[0]["universal_params"] == {"country": "us"}


async def test_async_run_tools_batch(async_client_coverage, monkeypatch):
    client = async_client_coverage
    created: list[str] = []

    async def _fake_run_tool_by_key(
        tool, params, file_name=None, universal_params=None
    ):
        created.append(tool)
        return f"atid-{len(created)}"

    monkeypatch.setattr(client, "run_tool_by_key", _fake_run_tool_by_key)

    requests = [
        {
            "tool": "ecommerce.amazon_product_by-url",
            "params": {"url": "https://example.com/1"},
        },
        {
            "tool": "ecommerce.amazon_product_by-url",
            "params": {"url": "https://example.com/2"},
        },
        {
            # Invalid params type
            "tool": "ecommerce.amazon_product_by-url",
            "params": "not-a-dict",
        },
    ]
    results = await client.run_tools_batch(requests, concurrency=2)
    assert len(results) == 3
    assert results[0]["ok"] is True and results[0]["task_id"] == "atid-1"
    assert results[1]["ok"] is True and results[1]["task_id"] == "atid-2"
    assert results[2]["ok"] is False
    assert results[2]["error"]["type"] == "validation_error"


async def test_async_universal_scrape_batch(async_client_coverage, monkeypatch):
    client = async_client_coverage

    async def _fake_universal_adv(req: UniversalScrapeRequest):
        return f"HTML for {req.url}"

    monkeypatch.setattr(client, "universal_scrape_advanced", _fake_universal_adv)

    req_obj = UniversalScrapeRequest(url="https://example.com/1")
    req_dict = {"url": "https://example.com/2", "js_render": True}
    results = await client.universal_scrape_batch([req_obj, req_dict], concurrency=2)
    assert len(results) == 2
    assert results[0]["ok"] and results[0]["output"].startswith("HTML for")
    assert results[1]["ok"] and results[1]["output"].startswith("HTML for")


async def test_async_list_proxy_users(async_client_coverage):
    client = async_client_coverage
    mock_resp = _async_response_with_json(
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
    with patch.object(
        client._http, "request", new_callable=AsyncMock, return_value=mock_resp
    ):
        out = await client.list_proxy_users()
    assert out.user_count == 1 and len(out.users) == 1


async def test_async_add_whitelist_ip(async_client_coverage):
    client = async_client_coverage
    mock_resp = _async_response_with_json({"code": 200, "data": {"ip": "1.2.3.4"}})
    with patch.object(
        client._http, "request", new_callable=AsyncMock, return_value=mock_resp
    ):
        out = await client.add_whitelist_ip("1.2.3.4", proxy_type=ProxyType.RESIDENTIAL)
    assert out["ip"] == "1.2.3.4"


async def test_async_list_whitelist_ips(async_client_coverage):
    client = async_client_coverage
    mock_resp = _async_response_with_json({"code": 200, "data": ["1.2.3.4", "5.6.7.8"]})
    with patch.object(
        client._http, "request", new_callable=AsyncMock, return_value=mock_resp
    ):
        out = await client.list_whitelist_ips()
    assert out == ["1.2.3.4", "5.6.7.8"]


async def test_async_list_countries(async_client_coverage):
    client = async_client_coverage
    mock_resp = _async_response_with_json(
        {
            "code": 200,
            "data": [{"country_code": "us", "country_name": "United States"}],
        }
    )
    with patch.object(
        client._http, "request", new_callable=AsyncMock, return_value=mock_resp
    ):
        out = await client.list_countries()
    assert len(out) == 1 and out[0]["country_code"] == "us"


async def test_async_list_states(async_client_coverage):
    client = async_client_coverage
    mock_resp = _async_response_with_json(
        {
            "code": 200,
            "data": [{"state_code": "wa", "state_name": "Washington"}],
        }
    )
    with patch.object(
        client._http, "request", new_callable=AsyncMock, return_value=mock_resp
    ):
        out = await client.list_states("us")
    assert len(out) == 1 and out[0]["state_code"] == "wa"


async def test_async_list_proxy_servers(async_client_coverage):
    client = async_client_coverage
    mock_resp = _async_response_with_json(
        {
            "code": 200,
            "data": [{"ip": "1.2.3.4", "port": 9999, "username": "u", "password": "p"}],
        }
    )
    with patch.object(
        client._http, "request", new_callable=AsyncMock, return_value=mock_resp
    ):
        out = await client.list_proxy_servers(ProxyType.RESIDENTIAL)
    assert len(out) == 1 and out[0].ip == "1.2.3.4"


async def test_async_get_proxy_expiration(async_client_coverage):
    client = async_client_coverage
    mock_resp = _async_response_with_json(
        {"code": 200, "data": {"1.2.3.4": 1735689600}}
    )
    with patch.object(
        client._http, "request", new_callable=AsyncMock, return_value=mock_resp
    ):
        out = await client.get_proxy_expiration("1.2.3.4", ProxyType.RESIDENTIAL)
    assert out["1.2.3.4"] == 1735689600


async def test_async_create_scraper_task_advanced(async_client_coverage):
    client = async_client_coverage
    mock_resp = _async_response_with_json({"code": 200, "data": {"task_id": "adv_tid"}})
    cfg = ScraperTaskConfig(
        file_name="f.json",
        spider_id="sid",
        spider_name="sname",
        parameters={"x": 1},
    )
    with patch.object(
        client._http, "request", new_callable=AsyncMock, return_value=mock_resp
    ):
        task_id = await client.create_scraper_task_advanced(cfg)
    assert task_id == "adv_tid"


async def test_async_create_video_task_advanced(async_client_coverage):
    client = async_client_coverage
    mock_resp = _async_response_with_json({"code": 200, "data": {"task_id": "vid_tid"}})
    cfg = VideoTaskConfig(
        file_name="v.json",
        spider_id="vid",
        spider_name="vname",
        parameters={},
        common_settings=CommonSettings(),
    )
    with patch.object(
        client._http, "request", new_callable=AsyncMock, return_value=mock_resp
    ):
        task_id = await client.create_video_task_advanced(cfg)
    assert task_id == "vid_tid"


async def test_async_close():
    client = AsyncThordataClient(scraper_token="t")
    await client._http._ensure_session()
    await client.close()
    assert client._http._session is None or client._http._session.closed
