#!/usr/bin/env python
"""Whitelist acceptance (read-only).

Validates:
- list_whitelist_ips works for at least Residential proxy_type.

No add/delete operations are performed in read-only mode.
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


def main() -> bool:
    print_header("WHITELIST ACCEPTANCE (READ-ONLY)")

    if not is_integration_enabled():
        print("THORDATA_INTEGRATION not set, skipping.")
        return True

    out = ensure_output_dir("whitelist")

    public_token = require_env("THORDATA_PUBLIC_TOKEN")
    public_key = require_env("THORDATA_PUBLIC_KEY")

    client = ThordataClient(public_token=public_token, public_key=public_key)

    all_ok = True
    results = {}

    print("Listing whitelist IPs (Residential)...")
    ok, ips = safe_call(client.list_whitelist_ips, proxy_type=ProxyType.RESIDENTIAL)
    results["residential"] = ips if ok else str(ips)

    if not ok:
        print(f"  [FAIL] {ips}")
        all_ok = False
    else:
        print(f"  [OK] {len(ips)} items")
        write_json(out / "whitelist_residential.json", {"ips": ips})

    client.close()

    print("\n--- Whitelist Summary ---")
    if all_ok:
        print("Whitelist read-only check passed.")
    else:
        print("Whitelist read-only check failed.")

    return all_ok


if __name__ == "__main__":
    exit_with_result(main())
