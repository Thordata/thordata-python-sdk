#!/usr/bin/env python
"""Account & balance acceptance (read-only).

Covers:
- get_traffic_balance
- get_wallet_balance
- get_usage_statistics (optional, requires date range)

This is based on examples/full_acceptance_test.py but kept strictly read-only.
"""

from __future__ import annotations

import sys
from datetime import date, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from thordata import ThordataClient

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
    print_header("ACCOUNT & BALANCE ACCEPTANCE (READ-ONLY)")

    if not is_integration_enabled():
        print("THORDATA_INTEGRATION not set, skipping.")
        return True

    out = ensure_output_dir("account")

    public_token = require_env("THORDATA_PUBLIC_TOKEN")
    public_key = require_env("THORDATA_PUBLIC_KEY")

    client = ThordataClient(public_token=public_token, public_key=public_key)

    results: dict[str, object] = {}
    all_ok = True

    print("Checking traffic balance...")
    ok, bal_or_err = safe_call(client.get_traffic_balance)
    results["traffic_balance"] = bal_or_err if ok else {"error": str(bal_or_err)}
    if ok:
        print(f"  [OK] traffic_balance={bal_or_err}")
    else:
        print(f"  [FAIL] {bal_or_err}")
        all_ok = False

    print("Checking wallet balance...")
    ok, wal_or_err = safe_call(client.get_wallet_balance)
    results["wallet_balance"] = wal_or_err if ok else {"error": str(wal_or_err)}
    if ok:
        print(f"  [OK] wallet_balance={wal_or_err}")
    else:
        print(f"  [FAIL] {wal_or_err}")
        all_ok = False

    # Optional: usage statistics for last 7 days
    print("Checking usage statistics (last 7 days)...")
    from_date = date.today() - timedelta(days=7)
    to_date = date.today()
    ok, usage_or_err = safe_call(client.get_usage_statistics, from_date, to_date)
    if ok:
        # UsageStatistics is a model; try to serialize
        try:
            results["usage_statistics"] = usage_or_err.to_dict()  # type: ignore[attr-defined]
        except Exception:
            results["usage_statistics"] = getattr(
                usage_or_err, "__dict__", str(usage_or_err)
            )
        print("  [OK] usage_statistics fetched")
    else:
        results["usage_statistics"] = {"error": str(usage_or_err)}
        print(f"  [WARN] usage_statistics failed: {usage_or_err}")
        # Do not fail suite for this; some accounts may not have usage enabled

    write_json(out / "account_readonly.json", results)
    client.close()

    print("\n--- Account Summary ---")
    if all_ok:
        print("✅ Account checks passed.")
    else:
        print("❌ Account checks failed. See artifacts for details.")

    return all_ok


if __name__ == "__main__":
    exit_with_result(main())
