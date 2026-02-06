#!/usr/bin/env python
"""Proxy users acceptance (read-only).

Validates:
- list_proxy_users works (Residential by default).

No create/update/delete in read-only mode.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from thordata import ThordataClient
from thordata.types import ProxyType

from .common import (
    ensure_output_dir,
    exit_with_result,
    is_integration_enabled,
    print_header,
    require_env,
    safe_call,
    write_json,
)


def _proxy_user_list_to_dict(users) -> dict:
    return {
        "limit": getattr(users, "limit", None),
        "remaining_limit": getattr(users, "remaining_limit", None),
        "user_count": getattr(users, "user_count", None),
        "users": [
            {
                "username": u.username,
                "password": u.password,
                "status": u.status,
                "traffic_limit": u.traffic_limit,
                "usage_traffic": u.usage_traffic,
                "usage_gb": u.usage_gb(),
                "limit_gb": u.limit_gb(),
            }
            for u in getattr(users, "users", [])
        ],
    }


def main() -> bool:
    print_header("PROXY USERS ACCEPTANCE (READ-ONLY)")

    if not is_integration_enabled():
        print("THORDATA_INTEGRATION not set, skipping.")
        return True

    out = ensure_output_dir("proxy_users")

    public_token = require_env("THORDATA_PUBLIC_TOKEN")
    public_key = require_env("THORDATA_PUBLIC_KEY")

    client = ThordataClient(public_token=public_token, public_key=public_key)

    all_ok = True

    print("Listing proxy users (Residential)...")
    ok, users_or_err = safe_call(
        client.list_proxy_users, proxy_type=ProxyType.RESIDENTIAL
    )

    if not ok:
        print(f"  [FAIL] {users_or_err}")
        write_json(
            out / "proxy_users_residential_error.json", {"error": str(users_or_err)}
        )
        all_ok = False
    else:
        payload = _proxy_user_list_to_dict(users_or_err)
        write_json(out / "proxy_users_residential.json", payload)
        print(f"  [OK] Found {len(payload.get('users', []))} users")

    client.close()

    print("\n--- Proxy Users Summary ---")
    if all_ok:
        print("Proxy users read-only check passed.")
    else:
        print("Proxy users read-only check failed.")

    return all_ok


if __name__ == "__main__":
    exit_with_result(main())
