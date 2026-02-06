#!/usr/bin/env python
"""Acceptance test for Locations API (read-only).

Verifies:
- Authentication with public token/key.
- `list_countries`, `list_states`, `list_cities`, `list_asn` endpoints.

Notes:
- Country list may not use `code=US` depending on backend; we fall back to the
  first available country code to ensure endpoint coverage.
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


def _pick_country_code(countries: list[dict]) -> str | None:
    # Prefer US, but fall back to any valid 2-letter code
    for item in countries:
        code = str(item.get("code") or item.get("country_code") or "").strip()
        if code.upper() == "US":
            return "US"
    for item in countries:
        code = str(item.get("code") or item.get("country_code") or "").strip()
        if len(code) == 2 and code.isalpha():
            return code.upper()
    return None


def main() -> bool:
    print_header("LOCATIONS API ACCEPTANCE (READ-ONLY)")
    if not is_integration_enabled():
        print("THORDATA_INTEGRATION not set, skipping.")
        return True

    output_dir = ensure_output_dir("locations")
    public_token = require_env("THORDATA_PUBLIC_TOKEN")
    public_key = require_env("THORDATA_PUBLIC_KEY")
    client = ThordataClient(public_token=public_token, public_key=public_key)

    all_ok = True

    print("\n1. Listing countries (Residential)...")
    ok, countries = safe_call(client.list_countries, proxy_type=ProxyType.RESIDENTIAL)
    if not ok or not countries:
        print(f"  [FAIL] Failed to list countries: {countries}")
        write_json(output_dir / "countries_error.json", {"error": str(countries)})
        client.close()
        return False

    assert isinstance(countries, list)
    print(f"  [OK] Found {len(countries)} countries.")
    write_json(output_dir / "countries.json", countries)

    country_code = _pick_country_code(countries)
    if not country_code:
        print(
            "  [WARN] Could not pick a valid country code; skipping states/cities/asn."
        )
        client.close()
        return True

    print(f"\nUsing country_code={country_code} for deeper checks")

    print(f"\n2. Listing states for {country_code}...")
    ok_states, states = safe_call(client.list_states, country_code=country_code)
    if not ok_states:
        print(f"  [FAIL] Failed to list states: {states}")
        write_json(
            output_dir / f"states_{country_code}_error.json", {"error": str(states)}
        )
        all_ok = False
    else:
        write_json(output_dir / f"states_{country_code}.json", states)
        print(
            f"  [OK] states_count={len(states) if isinstance(states, list) else 'n/a'}"
        )

    print(f"\n3. Listing cities for {country_code}...")
    ok_cities, cities = safe_call(client.list_cities, country_code=country_code)
    if not ok_cities:
        print(f"  [FAIL] Failed to list cities: {cities}")
        write_json(
            output_dir / f"cities_{country_code}_error.json", {"error": str(cities)}
        )
        all_ok = False
    else:
        write_json(output_dir / f"cities_{country_code}.json", cities)
        print(
            f"  [OK] cities_count={len(cities) if isinstance(cities, list) else 'n/a'}"
        )

    print(f"\n4. Listing ASN for {country_code}...")
    ok_asn, asn = safe_call(client.list_asn, country_code=country_code)
    if not ok_asn:
        print(f"  [FAIL] Failed to list ASN: {asn}")
        write_json(output_dir / f"asn_{country_code}_error.json", {"error": str(asn)})
        all_ok = False
    else:
        write_json(output_dir / f"asn_{country_code}.json", asn)
        print(f"  [OK] asn_count={len(asn) if isinstance(asn, list) else 'n/a'}")

    client.close()

    print("\n--- Locations Test Summary ---")
    if all_ok:
        print("Locations API checks passed.")
    else:
        print("Some locations API checks failed. See artifacts for details.")

    return all_ok


if __name__ == "__main__":
    exit_with_result(main())
