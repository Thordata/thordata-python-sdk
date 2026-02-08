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
        # Use new namespace API (recommended)
        stats = client.account.get_usage_statistics(
            start_time=int(week_ago.strftime("%Y%m%d")),
            end_time=int(today.strftime("%Y%m%d")),
        )
        print("\n[Usage Statistics - Last 7 days]")
        print("  total_usage_traffic:", stats.total_usage_traffic)
        print("  traffic_balance:    ", stats.traffic_balance)
        print("  query_days:         ", stats.query_days)
    except ThordataError as e:
        print(f"Failed to fetch usage statistics: {e}")

    try:
        # Use new namespace API (recommended)
        balance = client.account.get_balance()
        wallet_balance = client.get_wallet_balance()  # Keep old API for wallet
        print("\n[Balances]")
        print("  Traffic balance:", balance.get("traffic_balance", "N/A"))
        print("  Wallet balance: ", wallet_balance)
    except ThordataError as e:
        print(f"Failed to fetch balances: {e}")

    try:
        # Use new namespace API (recommended)
        users = client.proxy.list_users()
        print("\n[Proxy Users - Residential]")
        if isinstance(users, dict) and "users" in users:
            user_list = users["users"]
            print(f"  Total: {len(user_list)} users")
            for u in user_list[:5]:  # Show first 5
                if isinstance(u, dict):
                    print(f"  - {u.get('username', 'N/A')}")
                else:
                    print(f"  - {u}")
        else:
            print("  Users:", users)
    except ThordataError as e:
        print(f"Failed to list proxy users: {e}")

    try:
        # Use new namespace API (recommended)
        ips = client.proxy.list_whitelist_ips()
        print("\n[Whitelist IPs - Residential]")
        if not ips:
            print("  (no IPs)")
        else:
            for ip in ips[:10]:  # Show first 10
                print(f"  - {ip}")
    except ThordataError as e:
        print(f"Failed to list whitelist IPs: {e}")

    print("\nDone.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
