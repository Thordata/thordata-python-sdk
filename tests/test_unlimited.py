"""
Tests for unlimited namespace (sync and async).
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from thordata import AsyncThordataClient, ThordataClient
from thordata.exceptions import ThordataConfigError

# -----------------------------------------------------------------------------
# Sync UnlimitedNamespace
# -----------------------------------------------------------------------------


class TestUnlimitedNamespaceSync:
    @pytest.fixture
    def client(self):
        return ThordataClient(
            scraper_token="st",
            public_token="pt",
            public_key="pk",
        )

    def test_list_servers_success(self, client):
        mock_r = MagicMock()
        mock_r.status_code = 200
        mock_r.raise_for_status = MagicMock()
        mock_r.json.return_value = {
            "code": 200,
            "data": [{"ip": "1.2.3.4", "port": 9999}],
        }
        with patch.object(client, "_api_request_with_retry", return_value=mock_r):
            out = client.unlimited.list_servers()
        assert len(out) == 1
        assert out[0]["ip"] == "1.2.3.4"

    def test_list_servers_requires_public_credentials(self):
        client = ThordataClient(scraper_token="st")
        with pytest.raises(ThordataConfigError):
            client.unlimited.list_servers()

    def test_restart_server_success(self, client):
        mock_r = MagicMock()
        mock_r.status_code = 200
        mock_r.raise_for_status = MagicMock()
        mock_r.json.return_value = {"code": 200, "data": {"status": "ok"}}
        with patch.object(client, "_api_request_with_retry", return_value=mock_r):
            out = client.unlimited.restart_server("plan1")
        assert out["status"] == "ok"

    def test_renew_success(self, client):
        mock_r = MagicMock()
        mock_r.status_code = 200
        mock_r.raise_for_status = MagicMock()
        mock_r.json.return_value = {"code": 200, "data": {"plan_name": "plan1"}}
        with patch.object(client, "_api_request_with_retry", return_value=mock_r):
            out = client.unlimited.renew("plan1", month=1)
        assert out["plan_name"] == "plan1"

    def test_upgrade_success(self, client):
        mock_r = MagicMock()
        mock_r.status_code = 200
        mock_r.raise_for_status = MagicMock()
        mock_r.json.return_value = {"code": 200, "data": {}}
        with patch.object(client, "_api_request_with_retry", return_value=mock_r):
            out = client.unlimited.upgrade("plan1", "plan2")
        assert isinstance(out, dict)

    def test_list_bound_users_success(self, client):
        mock_r = MagicMock()
        mock_r.status_code = 200
        mock_r.raise_for_status = MagicMock()
        mock_r.json.return_value = {"code": 200, "data": {"list": [{"username": "u1"}]}}
        with patch.object(client, "_api_request_with_retry", return_value=mock_r):
            out = client.unlimited.list_bound_users("1.2.3.4")
        assert len(out) == 1
        assert out[0]["username"] == "u1"

    def test_bind_user_success(self, client):
        mock_r = MagicMock()
        mock_r.status_code = 200
        mock_r.raise_for_status = MagicMock()
        mock_r.json.return_value = {"code": 200, "data": {}}
        with patch.object(client, "_api_request_with_retry", return_value=mock_r):
            out = client.unlimited.bind_user("1.2.3.4", "user1")
        assert isinstance(out, dict)

    def test_unbind_user_success(self, client):
        mock_r = MagicMock()
        mock_r.status_code = 200
        mock_r.raise_for_status = MagicMock()
        mock_r.json.return_value = {"code": 200, "data": {}}
        with patch.object(client, "_api_request_with_retry", return_value=mock_r):
            out = client.unlimited.unbind_user("1.2.3.4", "user1")
        assert isinstance(out, dict)


# -----------------------------------------------------------------------------
# Async UnlimitedNamespace (uses _get_session().get/post, not _http.request)
# -----------------------------------------------------------------------------


def _make_async_session_for_get_post(get_json, post_json):
    """Build a mock aiohttp session whose get() and post() return async ctx mgrs."""

    def make_cm(json_data):
        resp = MagicMock()
        resp.json = AsyncMock(return_value=json_data)
        resp.raise_for_status = MagicMock()
        resp.status = 200
        cm = MagicMock()
        cm.__aenter__ = AsyncMock(return_value=resp)
        cm.__aexit__ = AsyncMock(return_value=None)
        return cm

    session = MagicMock()
    session.closed = False
    session.close = AsyncMock(return_value=None)
    session.get.return_value = make_cm(get_json)
    session.post.return_value = make_cm(post_json)
    return session


@pytest.mark.asyncio
async def test_async_unlimited_list_servers_success():
    client = AsyncThordataClient(
        scraper_token="st",
        public_token="pt",
        public_key="pk",
    )
    await client._http._ensure_session()
    try:
        session = _make_async_session_for_get_post(
            {"code": 200, "data": [{"ip": "5.6.7.8"}]},
            {},
        )
        client._http._session = session
        out = await client.unlimited.list_servers()
        assert len(out) == 1
        assert out[0]["ip"] == "5.6.7.8"
    finally:
        await client.close()


@pytest.mark.asyncio
async def test_async_unlimited_restart_server_success():
    client = AsyncThordataClient(
        scraper_token="st",
        public_token="pt",
        public_key="pk",
    )
    await client._http._ensure_session()
    try:
        session = _make_async_session_for_get_post(
            {},
            {"code": 200, "data": {"status": "restarted"}},
        )
        client._http._session = session
        out = await client.unlimited.restart_server("plan1")
        assert out["status"] == "restarted"
    finally:
        await client.close()


@pytest.mark.asyncio
async def test_async_unlimited_renew_success():
    client = AsyncThordataClient(
        scraper_token="st",
        public_token="pt",
        public_key="pk",
    )
    await client._http._ensure_session()
    try:
        session = _make_async_session_for_get_post(
            {},
            {"code": 200, "data": {"plan_name": "plan1"}},
        )
        client._http._session = session
        out = await client.unlimited.renew("plan1", month=2)
        assert out["plan_name"] == "plan1"
    finally:
        await client.close()
