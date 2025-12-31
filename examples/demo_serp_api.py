# examples/demo_serp_api.py
from __future__ import annotations

import os
from typing import Any

from thordata import ThordataClient
from thordata._example_utils import load_env, skip_if_missing, write_json


def main() -> int:
    load_env()

    if skip_if_missing(
        ["THORDATA_SCRAPER_TOKEN"], tip="SERP requires THORDATA_SCRAPER_TOKEN."
    ):
        return 0

    client = ThordataClient(scraper_token=os.environ["THORDATA_SCRAPER_TOKEN"])

    print("Running SERP demo (live)...")
    out: Any = client.serp_search(
        "pizza", engine="google", country="us", output_format="json"
    )

    path = write_json("serp_output.json", out)
    print("saved:", path.as_posix())

    if isinstance(out, dict):
        print("keys:", list(out.keys())[:12])
        meta = out.get("search_metadata")
        if isinstance(meta, dict):
            print("status:", meta.get("status"))
            print("total_time_taken:", meta.get("total_time_taken"))
    else:
        print("type:", type(out))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
