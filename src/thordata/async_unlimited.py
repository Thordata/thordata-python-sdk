"""
Async interface for Unlimited Residential Proxy management.
"""

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING, Any

import aiohttp

from ._utils import build_public_api_headers, extract_error_message
from .exceptions import (
    ThordataNetworkError,
    ThordataTimeoutError,
    raise_for_code,
)

if TYPE_CHECKING:
    from .async_client import AsyncThordataClient


class AsyncUnlimitedNamespace:
    """
    Async Namespace for Unlimited Residential Proxy operations.
    """

    def __init__(self, client: AsyncThordataClient):
        self._client = client
        self._api_base = client._locations_base_url.replace("/locations", "")

    async def list_servers(self) -> list[dict[str, Any]]:
        """Get the list of unlimited proxy servers."""
        self._client._require_public_credentials()
        params = {
            "token": self._client.public_token or "",
            "key": self._client.public_key or "",
        }

        try:
            async with self._client._get_session().get(
                f"{self._api_base}/unlimited/server-list",
                params=params,
                timeout=self._client._api_timeout,
            ) as response:
                response.raise_for_status()
                data = await response.json()

                if isinstance(data, dict):
                    if data.get("code") != 200:
                        msg = extract_error_message(data)
                        raise_for_code(
                            f"List servers failed: {msg}",
                            code=data.get("code"),
                            payload=data,
                        )
                    return data.get("data") or []
                return []

        except aiohttp.ClientError as e:
            raise ThordataNetworkError(
                f"List servers failed: {e}", original_error=e
            ) from e

    async def restart_server(self, plan_name: str) -> dict[str, Any]:
        return await self._post_action(
            "/unlimited/restart-server", {"plan_name": plan_name}
        )

    async def renew(self, plan_name: str, month: int) -> dict[str, Any]:
        return await self._post_action(
            "/unlimited/renew", {"plan_name": plan_name, "month": str(month)}
        )

    async def upgrade(self, plan_name: str, target_plan: str) -> dict[str, Any]:
        return await self._post_action(
            "/unlimited/upgrade",
            {"plan_name": plan_name, "target_plan": target_plan},
        )

    async def list_bound_users(self, ip: str) -> list[dict[str, Any]]:
        data = await self._post_action("/get_unlimited_servers_bind_user", {"ip": ip})
        return data.get("list") or [] if isinstance(data, dict) else []

    async def bind_user(self, ip: str, username: str) -> dict[str, Any]:
        return await self._post_action(
            "/add_unlimited_servers_bind_user", {"ip": ip, "username": username}
        )

    async def unbind_user(self, ip: str, username: str) -> dict[str, Any]:
        return await self._post_action(
            "/del_unlimited_servers_bind_user", {"ip": ip, "username": username}
        )

    async def _post_action(
        self, endpoint: str, payload: dict[str, Any]
    ) -> dict[str, Any]:
        self._client._require_public_credentials()
        headers = build_public_api_headers(
            self._client.public_token or "", self._client.public_key or ""
        )

        try:
            async with self._client._get_session().post(
                f"{self._api_base}{endpoint}",
                data=payload,
                headers=headers,
                timeout=self._client._api_timeout,
            ) as response:
                response.raise_for_status()
                data = await response.json()

                if data.get("code") != 200:
                    msg = extract_error_message(data)
                    raise_for_code(
                        f"Action {endpoint} failed: {msg}",
                        code=data.get("code"),
                        payload=data,
                    )

                return data.get("data", {})

        except asyncio.TimeoutError as e:
            raise ThordataTimeoutError(
                f"Action {endpoint} timed out: {e}", original_error=e
            ) from e
        except aiohttp.ClientError as e:
            raise ThordataNetworkError(
                f"Action {endpoint} failed: {e}", original_error=e
            ) from e
