#!/usr/bin/env python
"""Comprehensive Web Scraper Tools Coverage Test.

This script tests ALL available tools in the SDK to ensure 100% coverage.
It runs a representative test case for each tool and validates the full lifecycle:
- create_scraper_task_advanced or create_video_task
- wait_for_task
- get_task_result

Output formats: JSON/CSV/Dictionary aligned with Dashboard.
"""

from __future__ import annotations

import csv
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from scripts.acceptance.common import (
    AcceptanceConfig,
    ensure_output_dir,
    exit_with_result,
    is_integration_enabled,
    now_ts,
    print_header,
    require_env,
    safe_call,
    safe_call_with_timeout,
    write_json,
)
from thordata import CommonSettings, ThordataClient
from thordata.tools import (
    Airbnb,
    Amazon,
    Booking,
    Crunchbase,
    Facebook,
    GitHub,
    Glassdoor,
    GoogleMaps,
    GooglePlay,
    GoogleShopping,
    Indeed,
    Instagram,
    LinkedIn,
    Reddit,
    TikTok,
    Twitter,
    Walmart,
    YouTube,
    Zillow,
    eBay,
)
from thordata.types import ScraperTaskConfig

_SUCCESS_STATUSES = {"ready", "success", "finished"}
_FAILURE_STATUSES = {"failed", "error", "cancelled"}


def _run_text_tool(
    client: ThordataClient,
    *,
    name: str,
    tool,
    cfg: AcceptanceConfig,
) -> dict[str, Any]:
    """Run a standard text scraping tool."""
    spider_id = tool.get_spider_id()
    spider_name = tool.get_spider_name()
    file_name = f"accept_{name}_{now_ts()}"

    config = ScraperTaskConfig(
        file_name=file_name,
        spider_id=spider_id,
        spider_name=spider_name,
        parameters=tool.to_task_parameters(),
        include_errors=True,
    )

    ok, task_or_err = safe_call(client.create_scraper_task_advanced, config)
    if not ok:
        return {
            "name": name,
            "ok": False,
            "stage": "create",
            "error": str(task_or_err),
            "spider_id": spider_id,
            "spider_name": spider_name,
            "tool_type": "text",
        }

    task_id = str(task_or_err)

    # Use timeout wrapper to prevent hanging
    ok, status_or_err = safe_call_with_timeout(
        client.wait_for_task,
        task_id,
        poll_interval=cfg.poll_interval,
        max_wait=cfg.max_wait,
        hard_timeout=float(cfg.max_wait) + 30.0,
    )
    if not ok:
        return {
            "name": name,
            "ok": False,
            "task_id": task_id,
            "stage": "wait",
            "error": str(status_or_err),
            "spider_id": spider_id,
            "spider_name": spider_name,
            "tool_type": "text",
        }

    status = str(status_or_err).strip().lower()
    ok_dl, dl_or_err = safe_call(client.get_task_result, task_id)
    download_url = dl_or_err if ok_dl else None

    ok_final = status in _SUCCESS_STATUSES

    return {
        "name": name,
        "ok": ok_final,
        "task_id": task_id,
        "status": status,
        "download_url": download_url,
        "spider_id": spider_id,
        "spider_name": spider_name,
        "tool_type": "text",
        "error": None if ok_final else f"Status: {status}",
    }


def _run_video_tool(
    client: ThordataClient,
    *,
    name: str,
    tool,
    cfg: AcceptanceConfig,
) -> dict[str, Any]:
    """Run a video scraping tool."""
    spider_id = tool.get_spider_id()
    spider_name = tool.get_spider_name()
    file_name = f"accept_{name}_{now_ts()}"

    params = tool.to_task_parameters()
    common_settings = getattr(tool, "common_settings", CommonSettings())

    ok, task_or_err = safe_call(
        client.create_video_task,
        file_name,
        spider_id,
        spider_name,
        params,
        common_settings,
    )
    if not ok:
        return {
            "name": name,
            "ok": False,
            "stage": "create",
            "error": str(task_or_err),
            "spider_id": spider_id,
            "spider_name": spider_name,
            "tool_type": "video",
        }

    task_id = str(task_or_err)

    # Use timeout wrapper to prevent hanging
    ok, status_or_err = safe_call_with_timeout(
        client.wait_for_task,
        task_id,
        poll_interval=cfg.poll_interval,
        max_wait=cfg.max_wait,
        hard_timeout=float(cfg.max_wait) + 30.0,
    )
    if not ok:
        return {
            "name": name,
            "ok": False,
            "task_id": task_id,
            "stage": "wait",
            "error": str(status_or_err),
            "spider_id": spider_id,
            "spider_name": spider_name,
            "tool_type": "video",
        }

    status = str(status_or_err).strip().lower()
    ok_dl, dl_or_err = safe_call(client.get_task_result, task_id)
    download_url = dl_or_err if ok_dl else None

    ok_final = status in _SUCCESS_STATUSES

    return {
        "name": name,
        "ok": ok_final,
        "task_id": task_id,
        "status": status,
        "download_url": download_url,
        "spider_id": spider_id,
        "spider_name": spider_name,
        "tool_type": "video",
        "error": None if ok_final else f"Status: {status}",
    }


def _get_all_test_cases() -> list[tuple[str, Any, str]]:
    """Get all test cases: (name, tool_instance, tool_type).

    Uses realistic test data from documentation examples.
    """
    cases = []

    # Amazon - Using real product examples
    cases.append(
        ("amazon_product_by_asin", Amazon.ProductByAsin(asin="B0BZYCJK89"), "text")
    )
    cases.append(
        (
            "amazon_product_by_url",
            Amazon.ProductByUrl(
                url="https://www.amazon.com/HISDERN-Checkered-Handkerchief-Classic-Necktie/dp/B0BRXPR726"
            ),
            "text",
        )
    )
    cases.append(
        (
            "amazon_product_by_keywords",
            Amazon.ProductByKeywords(keyword="Apple Watch", page_turning=1),
            "text",
        )
    )
    cases.append(
        (
            "amazon_global_product_by_url",
            Amazon.GlobalProductByUrl(url="https://www.amazon.com/dp/B0CHHSFMRL/"),
            "text",
        )
    )

    # YouTube (Video)
    video_url = "https://www.youtube.com/watch?v=jNQXAC9IVRw"
    video_id = "jNQXAC9IVRw"
    settings = CommonSettings(
        resolution="<=360p",
        video_codec="vp9",
        audio_format="opus",
        bitrate="<=320",
        selected_only=False,
    )
    cases.append(
        (
            "youtube_video_download",
            YouTube.VideoDownload(url=video_url, common_settings=settings),
            "video",
        )
    )
    cases.append(
        (
            "youtube_audio_download",
            YouTube.AudioDownload(url=video_url, common_settings=settings),
            "video",
        )
    )
    cases.append(
        (
            "youtube_subtitle_download",
            YouTube.SubtitleDownload(video_id=video_id, common_settings=settings),
            "video",
        )
    )
    cases.append(
        (
            "youtube_video_info",
            YouTube.VideoInfo(video_id=video_id, common_settings=settings),
            "video",
        )
    )
    cases.append(
        (
            "youtube_video_post_by_url",
            YouTube.VideoPostByUrl(url="https://www.youtube.com/@stephcurry/videos"),
            "text",
        )
    )

    # Google Maps - Using real examples from docs
    cases.append(
        (
            "google_maps_by_url",
            GoogleMaps.DetailsByUrl(
                url="https://www.google.com/maps/place/Pizza%2BInn%2BMagdeburg/data=!4m7!3m6!1s0x47a5f50c083530a3:0xfdba8746b538141!8m2!3d52.1263086!4d11.6094743!16s%2Fg%2F11kqmtk3dt!19sChIJozA1CAz1pUcRQYFTa3So2w8?authuser=0&hl=en&rclk=1"
            ),
            "text",
        )
    )
    cases.append(
        (
            "google_maps_by_cid",
            GoogleMaps.DetailsByCid(CID="2476046430038551731"),
            "text",
        )
    )
    cases.append(
        (
            "google_maps_by_location",
            GoogleMaps.DetailsByLocation(
                country="us", keyword="Jio Store, 1449/137, Main 100 Ft Road"
            ),
            "text",
        )
    )
    cases.append(
        (
            "google_maps_by_placeid",
            GoogleMaps.DetailsByPlaceId(place_id="ChIJ3S-JXmauEmsRUcIaWtf4MzE"),
            "text",
        )
    )

    # Google Shopping
    cases.append(
        (
            "google_shopping_by_url",
            GoogleShopping.Product(url="https://www.google.com/shopping/product/123"),
            "text",
        )
    )
    cases.append(
        (
            "google_shopping_by_keywords",
            GoogleShopping.ProductByKeywords(keyword="iphone"),
            "text",
        )
    )

    # Google Play
    cases.append(
        (
            "google_play_app_info",
            GooglePlay.AppInfo(
                app_url="https://play.google.com/store/apps/details?id=com.whatsapp"
            ),
            "text",
        )
    )
    cases.append(
        (
            "google_play_reviews",
            GooglePlay.Reviews(
                app_url="https://play.google.com/store/apps/details?id=com.whatsapp"
            ),
            "text",
        )
    )

    # GitHub - Using real repository
    cases.append(
        (
            "github_repository",
            GitHub.Repository(repo_url="https://github.com/TheAlgorithms/Python"),
            "text",
        )
    )
    cases.append(
        (
            "github_repository_by_search",
            GitHub.RepositoryBySearchUrl(
                search_url="https://github.com/search?q=ML&type=repositories", max_num=5
            ),
            "text",
        )
    )

    # TikTok - Using real examples
    cases.append(
        (
            "tiktok_post",
            TikTok.Post(
                url="https://www.tiktok.com/@qatarliving/video/7294553558798650625",
                country="us",
            ),
            "text",
        )
    )
    cases.append(
        (
            "tiktok_profile",
            TikTok.Profile(url="https://www.tiktok.com/@fofimdmell", country="us"),
            "text",
        )
    )

    # Facebook - Using real example format
    cases.append(
        (
            "facebook_post_details",
            Facebook.PostDetails(
                url="https://www.facebook.com/permalink.php?story_fbid=pfbid0gNjZBhqCxSqj9xJS5aygNwqFqNEM2fYbTFKKbsvvGdEfTgFyAYWSckvkEHPqAE7gl&id=61574926580533"
            ),
            "text",
        )
    )

    # Instagram - Using real examples
    cases.append(
        ("instagram_profile", Instagram.Profile(username="zoobarcelona"), "text")
    )
    cases.append(
        (
            "instagram_post",
            Instagram.Post(
                profileurl="https://www.instagram.com/marcusfaberfdp", resultsLimit=5
            ),
            "text",
        )
    )

    # Twitter/X - Using real examples
    cases.append(
        ("twitter_profile", Twitter.Profile(url="https://x.com/elonmusk"), "text")
    )
    cases.append(
        (
            "twitter_post",
            Twitter.Post(url="https://x.com/FabrizioRomano/status/1665296716721946625"),
            "text",
        )
    )

    # LinkedIn - Using real example
    cases.append(
        (
            "linkedin_company",
            LinkedIn.Company(url="https://www.linkedin.com/company/dynamo-software"),
            "text",
        )
    )

    # Reddit - Using real examples
    cases.append(
        (
            "reddit_posts",
            Reddit.Posts(
                url="https://www.reddit.com/r/battlefield2042/comments/1cmqs1d/official_update_on_the_next_battlefield_game/"
            ),
            "text",
        )
    )
    cases.append(
        (
            "reddit_comment",
            Reddit.Comment(
                url="https://www.reddit.com/r/datascience/comments/1cmnf0m/comment/l32204i/"
            ),
            "text",
        )
    )

    # eBay - Using real example format
    cases.append(
        (
            "ebay_product_by_url",
            eBay.ProductByUrl(url="https://www.ebay.com/itm/187538926483"),
            "text",
        )
    )

    # Walmart - Using real example
    cases.append(
        (
            "walmart_product_by_url",
            Walmart.ProductByUrl(
                url="https://www.walmart.com/ip/HI-CHEW-Stand-Up-Pouch-Getaway-Mix-11-65oz/12284762931"
            ),
            "text",
        )
    )

    # Indeed
    cases.append(
        (
            "indeed_job_by_keyword",
            Indeed.JobByKeyword(keyword="analyst", location="New York, NY"),
            "text",
        )
    )

    # Glassdoor
    cases.append(
        (
            "glassdoor_company_by_url",
            Glassdoor.CompanyByUrl(
                url="https://www.glassdoor.com/Overview/Working-at-Test-EI_IE123.htm"
            ),
            "text",
        )
    )

    # Crunchbase - Using real examples
    cases.append(
        (
            "crunchbase_company_by_url",
            Crunchbase.CompanyByUrl(
                url="https://www.crunchbase.com/organization/apple"
            ),
            "text",
        )
    )

    # Booking - Using real example format
    cases.append(
        (
            "booking_hotel",
            Booking.HotelByUrl(
                url="https://www.booking.com/hotel/gb/westlands-of-pitlochry.en-gb.html"
            ),
            "text",
        )
    )

    # Zillow - Using real example
    cases.append(
        (
            "zillow_product_by_url",
            Zillow.ProductByUrl(
                url="https://www.zillow.com/homedetails/2506-Gordon-Cir-South-Bend-IN-46635/77050198_zpid/"
            ),
            "text",
        )
    )

    # Airbnb - Using real example format
    cases.append(
        (
            "airbnb_product_by_url",
            Airbnb.ProductByUrl(url="https://www.airbnb.com/rooms/21162039"),
            "text",
        )
    )

    return cases


def _export_to_csv(results: list[dict[str, Any]], output_path: Path) -> None:
    """Export results to CSV format (aligned with Dashboard)."""
    if not results:
        return

    fieldnames = [
        "name",
        "ok",
        "task_id",
        "status",
        "spider_id",
        "spider_name",
        "tool_type",
        "error",
        "download_url",
    ]
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        for r in results:
            writer.writerow(r)


def main() -> bool:
    print_header("COMPREHENSIVE WEB SCRAPER TOOLS COVERAGE TEST")

    if not is_integration_enabled():
        print("THORDATA_INTEGRATION not set, skipping.")
        return True

    out = ensure_output_dir("all_tools_coverage")

    scraper_token = require_env("THORDATA_SCRAPER_TOKEN")
    public_token = require_env("THORDATA_PUBLIC_TOKEN")
    public_key = require_env("THORDATA_PUBLIC_KEY")

    client = ThordataClient(
        scraper_token=scraper_token,
        public_token=public_token,
        public_key=public_key,
        api_timeout=120,
    )

    # Optimized timeout for faster testing - can be adjusted per tool type
    # Use shorter timeouts to prevent hanging, but allow enough time for real tasks
    cfg = AcceptanceConfig(timeout=60, poll_interval=2.0, max_wait=300.0)

    test_cases = _get_all_test_cases()
    results: list[dict[str, Any]] = []
    all_ok = True

    print(f"\nRunning {len(test_cases)} test cases...\n")
    print("Note: Some tests may fail due to invalid test data or API limitations.")
    print(
        "This is expected - focus on ensuring all tools can be instantiated and called.\n"
    )

    for idx, (name, tool, tool_type) in enumerate(test_cases, 1):
        print(f"[{idx}/{len(test_cases)}] Testing: {name} ({tool.get_spider_id()})")
        try:
            if tool_type == "video":
                r = _run_video_tool(client, name=name, tool=tool, cfg=cfg)
            else:
                r = _run_text_tool(client, name=name, tool=tool, cfg=cfg)

            results.append(r)
            if r.get("ok"):
                print(f"  [OK] task_id={r.get('task_id')} status={r.get('status')}")
            else:
                all_ok = False
                print(f"  [FAIL] {r.get('stage')}: {r.get('error')}")
        except Exception as e:
            all_ok = False
            error_result = {
                "name": name,
                "ok": False,
                "stage": "exception",
                "error": str(e),
                "spider_id": tool.get_spider_id(),
                "spider_name": tool.get_spider_name(),
                "tool_type": tool_type,
            }
            results.append(error_result)
            print(f"  [EXCEPTION] {str(e)}")

    # Export in multiple formats (aligned with Dashboard)
    write_json(out / "all_tools_coverage_results.json", results)
    _export_to_csv(results, out / "all_tools_coverage_results.csv")

    # Summary dictionary
    summary = {
        "total": len(results),
        "passed": sum(1 for r in results if r.get("ok")),
        "failed": sum(1 for r in results if not r.get("ok")),
        "by_tool_type": {},
        "by_spider": {},
    }

    for r in results:
        tool_type = r.get("tool_type", "unknown")
        spider_id = r.get("spider_id", "unknown")
        summary["by_tool_type"][tool_type] = summary["by_tool_type"].get(
            tool_type, 0
        ) + (1 if r.get("ok") else 0)
        summary["by_spider"][spider_id] = summary["by_spider"].get(
            spider_id, {"passed": 0, "failed": 0}
        )
        if r.get("ok"):
            summary["by_spider"][spider_id]["passed"] += 1
        else:
            summary["by_spider"][spider_id]["failed"] += 1

    write_json(out / "summary.json", summary)

    client.close()

    print("\n" + "=" * 80)
    print("COVERAGE SUMMARY")
    print("=" * 80)
    print(f"Total: {summary['total']}")
    print(f"Passed: {summary['passed']} ✅")
    print(f"Failed: {summary['failed']} ❌")
    print(f"Coverage: {summary['passed'] / summary['total'] * 100:.1f}%")
    print("\nBy Tool Type:")
    for tool_type, count in summary["by_tool_type"].items():
        print(f"  {tool_type}: {count}")

    # Calculate success rate
    total = len(results)
    passed = sum(1 for r in results if r.get("ok"))
    success_rate = (passed / total * 100) if total > 0 else 0

    print("\n" + "=" * 80)
    if all_ok:
        print("[SUCCESS] All tools passed!")
    else:
        print(
            f"[PARTIAL] {passed}/{total} tools passed ({success_rate:.1f}% success rate)"
        )
        print("Note: Some failures may be due to invalid test data, not SDK issues.")
        print("Check artifacts for detailed error information.")

    return all_ok


if __name__ == "__main__":
    exit_with_result(main())
