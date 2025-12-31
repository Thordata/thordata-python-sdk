# examples/demo_universal.py
from __future__ import annotations

import os

from thordata import ThordataClient
from thordata._example_utils import load_env, skip_if_missing, write_text


def main() -> int:
    load_env()

    if skip_if_missing(
        ["THORDATA_SCRAPER_TOKEN"], tip="Universal requires THORDATA_SCRAPER_TOKEN."
    ):
        return 0

    client = ThordataClient(scraper_token=os.environ["THORDATA_SCRAPER_TOKEN"])

    print("Running Universal Scrape demo (live)...")
    html = client.universal_scrape(
        "https://httpbin.org/html",
        js_render=False,
        output_format="html",
    )

    s = html if isinstance(html, str) else str(html)
    path = write_text("universal_output.html", s)
    print("saved:", path.as_posix())
    print("length:", len(s))
    print("preview:", s[:300].replace("\n", " ") + ("..." if len(s) > 300 else ""))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
