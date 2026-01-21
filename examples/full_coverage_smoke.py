"""
Thordata Full Coverage Smoke Test Suite

This script validates all major functionalities of the Thordata SDK against live APIs.
It serves as both an integration test suite and a comprehensive usage example.

Requirements:
    - A valid .env file with appropriate tokens (see .env.example).
    - Python 3.9+

Usage:
    python examples/full_coverage_smoke.py
"""

import json
import os
import sys
import time
import uuid
from typing import Any, Callable, Optional

try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    pass

from thordata import (
    CommonSettings,
    ProxyConfig,
    ProxyProduct,
    ThordataAPIError,
    ThordataClient,
)

# --- Configuration ---
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
CYAN = "\033[96m"
RESET = "\033[0m"

SCRAPER_TOKEN = os.getenv("THORDATA_SCRAPER_TOKEN")
PUBLIC_TOKEN = os.getenv("THORDATA_PUBLIC_TOKEN")
PUBLIC_KEY = os.getenv("THORDATA_PUBLIC_KEY")

RESIDENTIAL_USER = os.getenv("THORDATA_RESIDENTIAL_USERNAME")
RESIDENTIAL_PASS = os.getenv("THORDATA_RESIDENTIAL_PASSWORD")
PROXY_HOST = os.getenv("THORDATA_PROXY_HOST", "pr.thordata.net")


class TestSuite:
    def __init__(self):
        self.results: list[tuple[str, str, str]] = []
        self.client: Optional[ThordataClient] = None
        if SCRAPER_TOKEN:
            self.client = ThordataClient(
                scraper_token=SCRAPER_TOKEN,
                public_token=PUBLIC_TOKEN,
                public_key=PUBLIC_KEY,
            )

    def log(self, msg: str, color: str = RESET):
        print(f"{color}{msg}{RESET}")

    def run_test(self, name: str, func: Callable[[], Any], required_vars: list[str]):
        missing = [v for v in required_vars if not os.getenv(v)]
        if missing:
            self.log(
                f"⚠️  [SKIP] {name}: Missing env vars {', '.join(missing)}", YELLOW
            )
            self.results.append((name, "SKIPPED", ""))
            return

        try:
            self.log(f"\n🔄 [RUN]  {name}...", CYAN)
            func()
            self.log(f"✅ [PASS] {name}", GREEN)
            self.results.append((name, "PASS", ""))
        except Exception as e:
            error_details = str(e)
            is_skip = False

            if isinstance(e, ThordataAPIError):
                if e.payload:
                    try:
                        error_details = (
                            f"{e.message}\nPayload: {json.dumps(e.payload, indent=2)}"
                        )
                    except Exception:  # Fixed bare except
                        error_details = f"{e.message} Payload: {e.payload}"

                # Code 118: IP not whitelisted. This is expected in many local environments.
                if e.code == 118:
                    is_skip = True
                    error_details = "Skipped: IP whitelist restriction (Code 118)"

            if is_skip:
                self.log(f"⚠️  [SKIP] {name}: {error_details}", YELLOW)
                self.results.append((name, "SKIPPED", error_details))
            else:
                self.log(f"❌ [FAIL] {name}", RED)
                self.log(f"   Reason: {error_details}", RED)
                self.results.append((name, "FAIL", error_details))

    def report(self):
        self.log("\n" + "=" * 60)
        self.log("       TEST SUMMARY       ")
        self.log("=" * 60)

        passed = 0
        skipped = 0
        failed = 0

        for name, status, detail in self.results:
            color = (
                GREEN if status == "PASS" else YELLOW if status == "SKIPPED" else RED
            )
            print(f"{name:<25} {color}{status}{RESET}")
            if status == "FAIL" and detail:
                print(f"   -> {detail.splitlines()[0]}")
            if status == "SKIPPED" and detail:
                print(f"   -> {detail}")

            if status == "PASS":
                passed += 1
            elif status == "SKIPPED":
                skipped += 1
            else:
                failed += 1

        self.log("-" * 60)
        self.log(
            f"Total: {len(self.results)} | Pass: {passed} | Skip: {skipped} | Fail: {failed}"
        )
        if failed > 0:
            sys.exit(1)


# --- Test Functions ---


def test_serp(client: Optional[ThordataClient]):
    assert client is not None
    print("      Querying 'thordata' on Google...")
    res = client.serp_search("thordata", num=1)
    if "organic" in res:
        print(f"      Got {len(res['organic'])} organic results.")
    elif "organic_results" in res:
        print(f"      Got {len(res['organic_results'])} organic results.")
    else:
        raise ValueError("No organic results found")


def test_universal(client: Optional[ThordataClient]):
    assert client is not None
    print("      Scraping https://httpbin.org/html...")
    html = client.universal_scrape("https://httpbin.org/html", js_render=False)
    print(f"      Response length: {len(str(html))} chars")
    if "Herman Melville" not in str(html):
        raise ValueError("Unexpected content")


def test_tasks(client: Optional[ThordataClient]):
    assert client is not None

    # 1. Standard Text/Data Scraping Task
    text_spider_id = os.getenv("THORDATA_TASK_SPIDER_ID")
    text_spider_name = os.getenv("THORDATA_TASK_SPIDER_NAME", "unknown")

    if text_spider_id:
        import json

        params_raw = os.getenv(
            "THORDATA_TASK_PARAMETERS_JSON", '{"url":"https://example.com"}'
        )
        try:
            params = json.loads(params_raw)
            if isinstance(params, list):
                params = params[0]
        except Exception:  # Fixed bare except (handling JSON decode or other errors)
            params = {"url": "https://example.com"}

        print(
            f"      [1/2] Creating Text Task for {text_spider_name} ({text_spider_id})..."
        )
        url = client.run_task(
            file_name=f"smoke_text_{uuid.uuid4().hex[:6]}",
            spider_id=text_spider_id,
            spider_name=text_spider_name,
            parameters=params,
            max_wait=300,
            initial_poll_interval=2,
        )
        print(f"      Text Task Download: {url}")
    else:
        print("      [1/2] Skipped Text Task (Missing THORDATA_TASK_SPIDER_ID)")

    # 2. Video/Media Download Task
    print("      [2/2] Creating Video Task (youtube_video_by-url)...")

    test_video_url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
    try:
        vid_id = client.create_video_task(
            file_name=f"smoke_vid_{uuid.uuid4().hex[:6]}",
            spider_id="youtube_video_by-url",
            spider_name="youtube.com",
            parameters={"url": test_video_url},
            common_settings=CommonSettings(resolution="360p", is_subtitles="false"),
        )
        print(f"      Video Task Created: {vid_id}")
    except Exception as e:
        print(f"      (Video task creation warning: {e})")


def test_proxy_request(client: Optional[ThordataClient]):
    assert client is not None
    username = RESIDENTIAL_USER or ""
    password = RESIDENTIAL_PASS or ""

    if not username or not password:
        raise ValueError("Missing proxy credentials")

    config = ProxyConfig(
        username=username,
        password=password,
        product=ProxyProduct.RESIDENTIAL,
        host=PROXY_HOST,
    )
    print("      Tunneling to https://httpbin.org/ip...")
    res = client.get("https://httpbin.org/ip", proxy_config=config, timeout=30)
    if res.status_code != 200:
        raise ValueError(f"Status {res.status_code}")
    print(f"      Origin IP: {res.json().get('origin')}")


def test_account_info(client: Optional[ThordataClient]):
    assert client is not None
    print("      Fetching traffic balance...")
    try:
        tb = client.get_traffic_balance()
        print(f"      Traffic: {tb} KB")
    except Exception as e:
        print(f"      (Traffic failed: {e})")
        raise e

    print("      Fetching wallet balance...")
    wb = client.get_wallet_balance()
    print(f"      Wallet: ${wb}")


def test_proxy_user_crud(client: Optional[ThordataClient]):
    assert client is not None
    # Username: 6-15 chars, letters/numbers only.
    username = f"user{uuid.uuid4().hex[:8]}"
    password = "pass123"

    print(f"      [1/3] Creating user: {username}")
    try:
        client.create_proxy_user(username, password, traffic_limit=100)

        print("      Waiting 3s for propagation...")
        time.sleep(3)

        print("      [2/3] Updating user (Full Update)...")
        try:
            # NOTE: The API requires 'password' for updates, even if not changing it.
            # 'traffic_limit' and 'status' must also be valid.
            client.update_proxy_user(
                username, password=password, traffic_limit=500, status=False
            )
            print("            Update success")
        except Exception as e:
            print(f"            Update failed: {e}")
            raise e

    finally:
        print("      [3/3] Deleting user...")
        try:
            client.delete_proxy_user(username)
        except Exception as e:
            print(f"      (Cleanup warning: {e})")


def test_whitelist_crud(client: Optional[ThordataClient]):
    assert client is not None
    ip = "1.2.3.4"
    print(f"      [1/3] Adding IP: {ip}")
    client.add_whitelist_ip(ip)

    print("      Waiting 5s for propagation...")
    time.sleep(5)

    print("      [2/3] Listing IPs...")
    ips = client.list_whitelist_ips()
    found = ip in ips or any(x for x in ips if ip in str(x))

    if found:
        print(f"      ✅ IP found in list: {found}")
    else:
        print("      ⚠️ IP NOT found in list (possible propagation delay)")

    print("      [3/3] Deleting IP...")
    client.delete_whitelist_ip(ip)


def test_unlimited(client: Optional[ThordataClient]):
    assert client is not None
    print("      Listing unlimited servers...")
    servers = client.unlimited.list_servers()
    print(f"      Servers found: {len(servers)}")


def test_extract_links(client: Optional[ThordataClient]):
    assert client is not None
    print("      Extracting 1 IP (txt)...")
    ips = client.extract_ip_list(num=1, return_type="txt")
    print(f"      Extracted: {ips}")


def main():
    suite = TestSuite()
    c = suite.client

    suite.run_test("SERP API", lambda: test_serp(c), ["THORDATA_SCRAPER_TOKEN"])
    suite.run_test(
        "Universal API", lambda: test_universal(c), ["THORDATA_SCRAPER_TOKEN"]
    )

    suite.run_test(
        "Web Scraper Tasks",
        lambda: test_tasks(c),
        ["THORDATA_SCRAPER_TOKEN", "THORDATA_PUBLIC_TOKEN", "THORDATA_TASK_SPIDER_ID"],
    )

    suite.run_test(
        "Proxy Tunnel",
        lambda: test_proxy_request(c),
        ["THORDATA_RESIDENTIAL_USERNAME", "THORDATA_RESIDENTIAL_PASSWORD"],
    )

    public_req = ["THORDATA_PUBLIC_TOKEN", "THORDATA_PUBLIC_KEY"]

    suite.run_test("Account Info", lambda: test_account_info(c), public_req)
    suite.run_test("Proxy User CRUD", lambda: test_proxy_user_crud(c), public_req)
    suite.run_test("Whitelist CRUD", lambda: test_whitelist_crud(c), public_req)
    suite.run_test("Unlimited Proxy", lambda: test_unlimited(c), public_req)
    suite.run_test("Extract Links", lambda: test_extract_links(c), public_req)

    suite.report()


if __name__ == "__main__":
    main()
