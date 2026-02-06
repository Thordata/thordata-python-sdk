"""
Environment Validation Script
-----------------------------

Validates .env configuration and provides helpful error messages.
This script helps users quickly identify configuration issues.
"""

from __future__ import annotations

import os
from pathlib import Path

from thordata import load_env_file


def check_env_var(name: str, required: bool = False) -> tuple[bool, str | None]:
    """Check if environment variable is set."""
    value = os.getenv(name)
    if required and not value:
        return False, None
    return True, value


def validate_credentials() -> tuple[bool, list[str]]:
    """Validate all credential configurations."""
    issues: list[str] = []

    # API Tokens
    scraper_token_ok, scraper_token = check_env_var(
        "THORDATA_SCRAPER_TOKEN", required=False
    )
    public_token_ok, public_token = check_env_var(
        "THORDATA_PUBLIC_TOKEN", required=False
    )
    public_key_ok, public_key = check_env_var("THORDATA_PUBLIC_KEY", required=False)

    if not scraper_token:
        issues.append(
            "  [WARN] THORDATA_SCRAPER_TOKEN not set (required for SERP/Universal/Web Scraper APIs)"
        )
    else:
        print(f"  [OK] THORDATA_SCRAPER_TOKEN: {scraper_token[:10]}...")

    if not public_token or not public_key:
        issues.append(
            "  [WARN] THORDATA_PUBLIC_TOKEN or THORDATA_PUBLIC_KEY not set (required for Management APIs)"
        )
    else:
        print(f"  [OK] THORDATA_PUBLIC_TOKEN: {public_token[:10]}...")
        print(f"  [OK] THORDATA_PUBLIC_KEY: {public_key[:10]}...")

    # Proxy Credentials
    residential_user, residential_pass = (
        os.getenv("THORDATA_RESIDENTIAL_USERNAME"),
        os.getenv("THORDATA_RESIDENTIAL_PASSWORD"),
    )
    if not residential_user or not residential_pass:
        issues.append(
            "  [WARN] THORDATA_RESIDENTIAL_USERNAME/PASSWORD not set (required for Proxy Network)"
        )
    else:
        print(f"  [OK] THORDATA_RESIDENTIAL_USERNAME: {residential_user[:10]}...")

    # Browser Credentials
    browser_user = os.getenv("THORDATA_BROWSER_USERNAME") or os.getenv(
        "THORDATA_RESIDENTIAL_USERNAME"
    )
    browser_pass = os.getenv("THORDATA_BROWSER_PASSWORD") or os.getenv(
        "THORDATA_RESIDENTIAL_PASSWORD"
    )
    if not browser_user or not browser_pass:
        issues.append("  [WARN] Browser credentials not set (required for Browser API)")
    else:
        print("  [OK] Browser credentials available")

    # Upstream Proxy (optional)
    upstream = os.getenv("THORDATA_UPSTREAM_PROXY")
    if upstream:
        print(f"  [OK] THORDATA_UPSTREAM_PROXY: {upstream}")
    else:
        print("  [INFO] THORDATA_UPSTREAM_PROXY not set (optional, for Clash/V2Ray)")

    return len(issues) == 0, issues


def main() -> int:
    """Main validation function."""
    print("=" * 80)
    print("Thordata SDK - Environment Validation")
    print("=" * 80)

    # Load .env
    repo_root = Path(__file__).parent.parent
    env_path = repo_root / ".env"

    if env_path.exists():
        print(f"\n[INFO] Loading .env from: {env_path}")
        load_env_file(str(env_path))
    else:
        print(f"\n[WARN] .env file not found at: {env_path}")
        print("  Using environment variables only")

    print("\n[CHECK] Validating credentials...")
    is_valid, issues = validate_credentials()

    if issues:
        print("\n[ISSUES] Found configuration issues:")
        for issue in issues:
            print(issue)
        print("\n[TIP] Fix suggestions:")
        print("  1. Copy .env.example to .env")
        print("  2. Fill in your credentials from Thordata Dashboard")
        print("  3. Run this script again to verify")
        return 1
    else:
        print("\n[OK] All required credentials are configured!")
        print("\n[READY] You can now run acceptance scripts:")
        print("  python examples/demo_proxy_network.py")
        print("  python examples/demo_serp_api.py")
        print("  python examples/demo_web_scraper_api.py")
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
