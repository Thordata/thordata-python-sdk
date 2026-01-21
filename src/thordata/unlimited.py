"""
Sync interface for Unlimited Residential Proxy management.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from ._utils import build_public_api_headers
from .exceptions import raise_for_code

if TYPE_CHECKING:
    from .client import ThordataClient


class UnlimitedNamespace:
    """
    Namespace for Unlimited Residential Proxy operations.
    """

    def __init__(self, client: ThordataClient):
        self._client = client
        # Base URL for unlimited endpoints (usually same as public API base)
        # We can reuse _locations_base_url logic to find the API root
        # locations_base: .../api/locations -> root: .../api
        self._api_base = client._locations_base_url.replace("/locations", "")

    def list_servers(self) -> list[dict[str, Any]]:
        """
        Get the list of unlimited proxy servers.

        Returns:
            List of server objects.
        """
        self._client._require_public_credentials()
        params = {
            "token": self._client.public_token,
            "key": self._client.public_key,
        }
        response = self._client._api_request_with_retry(
            "GET", f"{self._api_base}/unlimited/server-list", params=params
        )
        response.raise_for_status()
        data = response.json()
        if data.get("code") != 200:
            raise_for_code("List servers failed", code=data.get("code"), payload=data)

        # API returns { "data": [...] } OR { "data": { "list": [...] } } sometimes
        # Assuming standard list return
        return data.get("data") or []

    def restart_server(self, plan_name: str) -> dict[str, Any]:
        """Restart an unlimited proxy server."""
        return self._post_action("/unlimited/restart-server", {"plan_name": plan_name})

    def renew(self, plan_name: str, month: int) -> dict[str, Any]:
        """Renew an unlimited plan."""
        return self._post_action(
            "/unlimited/renew", {"plan_name": plan_name, "month": str(month)}
        )

    def upgrade(self, plan_name: str, target_plan: str) -> dict[str, Any]:
        """Upgrade an unlimited plan."""
        return self._post_action(
            "/unlimited/upgrade",
            {"plan_name": plan_name, "target_plan": target_plan},
        )

    def list_bound_users(self, ip: str) -> list[dict[str, Any]]:
        """List users bound to a specific unlimited server IP."""
        data = self._post_action("/get_unlimited_servers_bind_user", {"ip": ip})
        # Assuming data structure similar to other lists
        return data.get("list") or [] if isinstance(data, dict) else []

    def bind_user(self, ip: str, username: str) -> dict[str, Any]:
        """Bind a sub-user to an unlimited server IP."""
        return self._post_action(
            "/add_unlimited_servers_bind_user", {"ip": ip, "username": username}
        )

    def unbind_user(self, ip: str, username: str) -> dict[str, Any]:
        """Unbind a sub-user from an unlimited server IP."""
        return self._post_action(
            "/del_unlimited_servers_bind_user", {"ip": ip, "username": username}
        )

    def _post_action(self, endpoint: str, payload: dict[str, Any]) -> dict[str, Any]:
        """Helper for POST actions."""
        self._client._require_public_credentials()
        headers = build_public_api_headers(
            self._client.public_token or "", self._client.public_key or ""
        )
        response = self._client._api_request_with_retry(
            "POST", f"{self._api_base}{endpoint}", data=payload, headers=headers
        )
        response.raise_for_status()
        data = response.json()
        if data.get("code") != 200:
            raise_for_code(
                f"Action {endpoint} failed", code=data.get("code"), payload=data
            )
        return data.get("data", {})
