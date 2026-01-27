#!/usr/bin/env python
"""Universal Scrape (Web Unlocker) acceptance (read-only).

Uses URL fallback list to mitigate target instability.
Validates HTML result is non-empty.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from thordata import ThordataClient

from .common import (
    AcceptanceConfig,
    ensure_output_dir,
    exit_with_result,
    is_integration_enabled,
    now_ts,
    print_header,
    require_env,
    safe_call,
    write_text,
)

URLS = [
    "https://example.com/",
    "https://httpbin.org/html",
    "https://www.wikipedia.org/",
]


def main() -> bool:
    print_header("UNIVERSAL ACCEPTANCE (READ-ONLY)")

    if not is_integration_enabled():
        print("THORDATA_INTEGRATION not set, skipping.")
        return True

    out = ensure_output_dir("universal")
    cfg = AcceptanceConfig(timeout=90)

    scraper_token = require_env("THORDATA_SCRAPER_TOKEN")
    client = ThordataClient(scraper_token=scraper_token, api_timeout=cfg.timeout)

    all_ok = False
    last_err = None

    for url in URLS:
        print(f"Scrape: {url}")
        ok, res_or_err = safe_call(
            client.universal_scrape,
            url,
            js_render=False,
            output_format="html",
        )
        if not ok:
            print(f"  [FAIL] {res_or_err}")
            last_err = res_or_err
            continue

        html = res_or_err
        if isinstance(html, bytes):
            try:
                html = html.decode("utf-8", errors="replace")
            except Exception:
                html = str(html)

        if not str(html).strip():
            print("  [FAIL] Empty response")
            last_err = RuntimeError("Empty response")
            continue

        out_file = out / f"universal_{now_ts()}.html"
        write_text(out_file, str(html))
        print(f"  [OK] Saved to {out_file}")
        all_ok = True
        break

    client.close()

    print("\n--- Universal Summary ---")
    if all_ok:
        print("✅ Universal scrape passed.")
    else:
        print(f"❌ Universal scrape failed. Last error: {last_err}")

    return all_ok


if __name__ == "__main__":
    exit_with_result(main())
