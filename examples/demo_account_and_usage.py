"""
Thordata Account & Usage Demo
------------------------------

Goal: Quick one-click inspection of account management interfaces:
- Usage statistics for the last 7 days
- Traffic balance & wallet balance
- Current Residential proxy sub-user list
- Current whitelist IP list

Setup:
- Fill in .env with at least:
    THORDATA_PUBLIC_TOKEN=...
    THORDATA_PUBLIC_KEY=...
"""

from __future__ import annotations

import os
from datetime import date, timedelta

from thordata import ThordataClient, ThordataError, load_env_file


def main() -> int:
    # Load .env from repo root
    repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    load_env_file(os.path.join(repo_root, ".env"))

    p_token = os.getenv("THORDATA_PUBLIC_TOKEN")
    p_key = os.getenv("THORDATA_PUBLIC_KEY")
    if not p_token or not p_key:
        print("Missing THORDATA_PUBLIC_TOKEN / THORDATA_PUBLIC_KEY in env/.env")
        return 1

    client = ThordataClient(
        scraper_token=None,
        public_token=p_token,
        public_key=p_key,
    )

    print("=" * 60)
    print("Thordata Account & Usage Overview")
    print("=" * 60)

    try:
        today = date.today()
        week_ago = today - timedelta(days=7)
        stats = client.get_usage_statistics(week_ago, today)
        print("\n[Usage Statistics - Last 7 days]")
        print("  total_usage_traffic:", stats.total_usage_traffic)
        print("  traffic_balance:    ", stats.traffic_balance)
        print("  query_days:         ", stats.query_days)
    except ThordataError as e:
        print(f"Failed to fetch usage statistics: {e}")

    try:
        traffic_balance = client.get_traffic_balance()
        wallet_balance = client.get_wallet_balance()
        print("\n[Balances]")
        print("  Traffic balance:", traffic_balance)
        print("  Wallet balance: ", wallet_balance)
    except ThordataError as e:
        print(f"Failed to fetch balances: {e}")

    try:
        users = client.list_proxy_users()
        print("\n[Proxy Users - Residential]")
        print("  Limit:", users.limit, "Remaining:", users.remaining_limit)
        for u in users.users:
            print(
                f"  - {u.username} (status={u.status}, "
                f"traffic_limit={u.traffic_limit}, usage={u.usage_traffic})"
            )
    except ThordataError as e:
        print(f"Failed to list proxy users: {e}")

    try:
        ips = client.list_whitelist_ips()
        print("\n[Whitelist IPs - Residential]")
        if not ips:
            print("  (no IPs)")
        else:
            for ip in ips:
                print(f"  - {ip}")
    except ThordataError as e:
        print(f"Failed to list whitelist IPs: {e}")

    print("\nDone.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
