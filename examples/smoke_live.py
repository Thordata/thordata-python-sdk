# examples/smoke_live.py
from __future__ import annotations

import os
from typing import Any

from thordata import ScraperTaskConfig, ThordataClient
from thordata._example_utils import load_env, skip_if_missing, parse_json_env, normalize_task_parameters


def main() -> int:
    load_env()

    if skip_if_missing(["THORDATA_SCRAPER_TOKEN"], tip="SERP/Universal requires THORDATA_SCRAPER_TOKEN."):
        return 0

    client = ThordataClient(
        scraper_token=os.environ["THORDATA_SCRAPER_TOKEN"],
        public_token=os.getenv("THORDATA_PUBLIC_TOKEN"),
        public_key=os.getenv("THORDATA_PUBLIC_KEY"),
    )

    print("=" * 60)
    print("1) SERP live smoke")
    print("=" * 60)
    serp = client.serp_search("pizza", engine="google", country="us")
    # 避免刷屏：只打印关键字段存在性
    if isinstance(serp, dict):
        print("serp keys:", list(serp.keys())[:10])
    else:
        print("serp type:", type(serp))

    print("=" * 60)
    print("2) Universal live smoke")
    print("=" * 60)
    html = client.universal_scrape("https://httpbin.org/html", js_render=False, output_format="html")
    s = html if isinstance(html, str) else str(html)
    print("universal length:", len(s))
    print("universal preview:", s[:200].replace("\n", " ") + ("..." if len(s) > 200 else ""))

    print("=" * 60)
    print("3) Tasks live smoke (optional)")
    print("=" * 60)
    if skip_if_missing(
        ["THORDATA_PUBLIC_TOKEN", "THORDATA_PUBLIC_KEY", "THORDATA_TASK_SPIDER_ID", "THORDATA_TASK_SPIDER_NAME", "THORDATA_TASK_PARAMETERS_JSON"],
        tip="Tasks smoke requires public token/key + task template env from Dashboard -> Web Scraper Store -> API Builder.",
    ):
        return 0

    raw: Any = parse_json_env("THORDATA_TASK_PARAMETERS_JSON", default="{}")
    params = normalize_task_parameters(raw)

    config = ScraperTaskConfig(
        file_name=os.getenv("THORDATA_TASK_FILE_NAME") or "demo_task",
        spider_id=os.environ["THORDATA_TASK_SPIDER_ID"],
        spider_name=os.environ["THORDATA_TASK_SPIDER_NAME"],
        parameters=params,
        include_errors=True,
    )

    if hasattr(client, "create_scraper_task_advanced"):
        task_id = client.create_scraper_task_advanced(config)  # type: ignore[attr-defined]
    else:
        # Fallback: basic create_scraper_task() doesn't accept include_errors in this SDK version
        task_id = client.create_scraper_task(
            file_name=config.file_name,
            spider_id=config.spider_id,
            spider_name=config.spider_name,
            parameters=config.parameters,
        )
    print("task_id:", task_id)

    status = client.wait_for_task(task_id, poll_interval=5.0, max_wait=120.0)
    print("final status:", status)

    if str(status).lower() in ("ready", "success", "finished"):
        url = client.get_task_result(task_id, file_type="json")
        print("download url:", url)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())