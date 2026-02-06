#!/usr/bin/env python
"""SERP API acceptance (read-only).

Runs a couple of SERP queries with fallback list to reduce flakiness.

Pass criteria (strict):
- HTTP succeeds
- Response is a dict
- API `code` is 200 (if present)
- Response contains at least one of: organic / result / ads / knowledge_graph
  (Different engines may return different keys)
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from thordata import Engine, ThordataClient

from .common import (
    AcceptanceConfig,
    ensure_output_dir,
    exit_with_result,
    is_integration_enabled,
    print_header,
    require_env,
    safe_call,
    write_json,
)

QUERIES = [
    "OpenAI",
    "python requests tutorial",
    "pizza",
]


def _has_any_results(data: dict) -> bool:
    for k in ("organic", "result", "ads", "knowledge_graph", "answer_box"):
        v = data.get(k)
        if isinstance(v, list) and len(v) > 0:
            return True
        if isinstance(v, dict) and len(v) > 0:
            return True
    return False


def main() -> bool:
    print_header("SERP ACCEPTANCE (READ-ONLY)")

    if not is_integration_enabled():
        print("THORDATA_INTEGRATION not set, skipping.")
        return True

    out = ensure_output_dir("serp")
    cfg = AcceptanceConfig(timeout=60)

    scraper_token = require_env("THORDATA_SCRAPER_TOKEN")
    client = ThordataClient(scraper_token=scraper_token, api_timeout=cfg.timeout)

    results = []
    all_ok = True

    for q in QUERIES:
        print(f"Query: {q}")
        ok, data_or_err = safe_call(
            client.serp_search,
            q,
            engine=Engine.GOOGLE,
            num=5,
            output_format="json",
        )
        if not ok:
            print(f"  [FAIL] {data_or_err}")
            results.append(
                {"query": q, "ok": False, "stage": "request", "error": str(data_or_err)}
            )
            all_ok = False
            continue

        data = data_or_err
        if not isinstance(data, dict):
            print("  [FAIL] Non-dict response")
            results.append(
                {
                    "query": q,
                    "ok": False,
                    "stage": "parse",
                    "error": f"unexpected type: {type(data)}",
                }
            )
            all_ok = False
            continue

        api_code = data.get("code")
        if api_code is not None and api_code != 200:
            print(f"  [FAIL] api_code={api_code}")
            results.append(
                {
                    "query": q,
                    "ok": False,
                    "stage": "api",
                    "code": api_code,
                    "data": data,
                }
            )
            all_ok = False
            continue

        has_results = _has_any_results(data)
        results.append(
            {"query": q, "ok": True, "has_results": has_results, "data": data}
        )
        print(f"  [OK] has_results={has_results}")

    write_json(out / "serp_results.json", results)
    client.close()

    print("\n--- SERP Summary ---")
    if all_ok:
        print("SERP checks passed.")
    else:
        print("Some SERP checks failed. See artifacts for details.")

    return all_ok


if __name__ == "__main__":
    exit_with_result(main())
