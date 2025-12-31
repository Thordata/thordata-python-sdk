# examples/demo_serp_google_news.py
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

    print("Running Google News SERP demo (live)...")
    out: Any = client.serp_search(
        "AI regulation",
        engine="google_news",
        country="us",
        output_format="json",
    )

    path = write_json("serp_google_news_output.json", out)
    print("saved:", path.as_posix())

    if isinstance(out, dict):
        print("keys:", list(out.keys())[:12])
    else:
        print("type:", type(out))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
