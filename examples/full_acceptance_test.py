"""
🔥 Thordata SDK Full Acceptance Test Suite (v3.3) 🔥
====================================================

Updates:
- Fix: Pylance typing errors (str | None mismatch).
- Fix: User Update logic complies with API regex.
- Feat: Added coverage for newly implemented API endpoints (Monitor, Hour Usage, Latest Task).

Usage:
    python examples/full_acceptance_test.py
"""

import json
import os
import sys
import time
import uuid
from typing import Optional

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../src")))

from thordata import (
    CommonSettings,
    ProxyConfig,
    ProxyProduct,
    StaticISPProxy,
    ThordataClient,
)
from thordata.exceptions import ThordataAPIError
from thordata.tools import Amazon, YouTube

RESET = "\033[0m"
BOLD = "\033[1m"
GREEN = "\033[32m"
RED = "\033[31m"
YELLOW = "\033[33m"
CYAN = "\033[36m"


def log_section(title: str):
    print(f"\n{BOLD}{CYAN}=== {title} ==={RESET}")


def log_pass(msg: str):
    print(f"{GREEN}✅ PASS:{RESET} {msg}")


def log_fail(msg: str, err: Optional[Exception] = None):
    print(f"{RED}❌ FAIL:{RESET} {msg}")
    if err:
        details = str(err)
        if isinstance(err, ThordataAPIError) and err.payload:
            details = f"{err.message} | Payload: {json.dumps(err.payload)}"
        print(f"   {RED}   -> {details}{RESET}")


def log_skip(msg: str):
    print(f"{YELLOW}⚠️ SKIP:{RESET} {msg}")


def log_info(msg: str):
    print(f"   ℹ️ {msg}")


class AcceptanceSuite:
    def __init__(self):
        try:
            from dotenv import load_dotenv

            load_dotenv()
        except Exception:
            pass

        self.scraper_token = os.getenv("THORDATA_SCRAPER_TOKEN")
        self.public_token = os.getenv("THORDATA_PUBLIC_TOKEN")
        self.public_key = os.getenv("THORDATA_PUBLIC_KEY")

        # FIX: Pylance 'str | None' error -> use os.getenv(key, "")
        self.creds = {
            "residential": (
                os.getenv("THORDATA_RESIDENTIAL_USERNAME", ""),
                os.getenv("THORDATA_RESIDENTIAL_PASSWORD", ""),
            ),
            "mobile": (
                os.getenv("THORDATA_MOBILE_USERNAME", ""),
                os.getenv("THORDATA_MOBILE_PASSWORD", ""),
            ),
            "datacenter": (
                os.getenv("THORDATA_DATACENTER_USERNAME", ""),
                os.getenv("THORDATA_DATACENTER_PASSWORD", ""),
            ),
            "isp": (
                os.getenv("THORDATA_ISP_USERNAME", ""),
                os.getenv("THORDATA_ISP_PASSWORD", ""),
            ),
        }
        self.res_host = os.getenv("THORDATA_PROXY_HOST", "pr.thordata.net")
        self.isp_host = os.getenv("THORDATA_ISP_HOST", "")
        self.upstream = os.getenv("THORDATA_UPSTREAM_PROXY")

        if not all([self.scraper_token, self.public_token, self.public_key]):
            print(f"{RED}CRITICAL: Missing API tokens.{RESET}")
            sys.exit(1)

        self.client = ThordataClient(
            scraper_token=self.scraper_token,
            public_token=self.public_token,
            public_key=self.public_key,
            timeout=30,
        )

    def run_all(self):
        print(f"{BOLD}Starting Full Acceptance Test (v3.3)...{RESET}")

        self.test_account()
        self.test_locations()
        self.test_all_proxies()
        self.test_serp()
        self.test_universal()
        self.test_tools_ecommerce()
        self.test_tools_video()
        self.test_management()
        self.test_new_features_audit()  # New coverage
        print(f"\n{BOLD}{GREEN}All Tests Completed.{RESET}")

    def test_account(self):
        log_section("1. Account & Balance")
        try:
            bal = self.client.get_traffic_balance()
            log_pass(f"Traffic: {bal} KB")
            wal = self.client.get_wallet_balance()
            log_pass(f"Wallet: ${wal}")
        except Exception as e:
            log_fail("Account check failed", e)

    def test_locations(self):
        log_section("2. Locations API")
        try:
            c = self.client.list_countries()
            if c:
                log_pass(f"Fetched {len(c)} countries")
            else:
                log_fail("Country list empty")
        except Exception as e:
            log_fail("Locations failed", e)

    def _test_single_proxy(self, name: str, config):
        target = "https://httpbin.org/ip"
        log_info(
            f"Connecting to {name} via {config.host}:{config.port} ({config.protocol})..."
        )
        try:
            start = time.time()
            config.protocol = "http"
            resp = self.client.get(target, proxy_config=config, timeout=60)
            if resp.status_code == 200:
                log_pass(
                    f"{name}: Success! IP={resp.json().get('origin')} ({(time.time()-start)*1000:.0f}ms)"
                )
            else:
                log_fail(f"{name}: Status {resp.status_code}")
        except Exception as e:
            log_fail(f"{name}: Connection Failed", e)

    def test_all_proxies(self):
        log_section("3. Proxy Network Tunneling")
        u, p = self.creds["residential"]
        if u:
            cfg = ProxyConfig(
                username=u,
                password=p,
                product=ProxyProduct.RESIDENTIAL,
                host=self.res_host,
                country="us",
                protocol="http",
            )
            self._test_single_proxy("Residential", cfg)
        else:
            log_skip("Residential missing")

        u, p = self.creds["mobile"]
        if u:
            cfg = ProxyConfig(
                username=u, password=p, product=ProxyProduct.MOBILE, protocol="http"
            )
            self._test_single_proxy("Mobile", cfg)
        else:
            log_skip("Mobile missing")

        u, p = self.creds["datacenter"]
        if u:
            cfg = ProxyConfig(
                username=u, password=p, product=ProxyProduct.DATACENTER, protocol="http"
            )
            self._test_single_proxy("Datacenter", cfg)
        else:
            log_skip("Datacenter missing")

        u, p = self.creds["isp"]
        if u and self.isp_host:
            cfg = StaticISPProxy(
                host=self.isp_host, username=u, password=p, protocol="http"
            )
            self._test_single_proxy("Static ISP", cfg)
        else:
            log_skip("ISP missing")

    def test_serp(self):
        log_section("4. SERP API")
        try:
            res = self.client.serp_search("Thordata", engine="google", num=1)
            if res.get("organic"):
                log_pass("Google Search: Success")
            else:
                log_fail("Google Search: Zero results")
        except Exception as e:
            log_fail("SERP failed", e)

    def test_universal(self):
        log_section("5. Universal API")
        try:
            html = self.client.universal_scrape(
                "https://httpbin.org/html", js_render=False
            )
            if len(str(html)) > 50:
                log_pass("Universal: Success")
            else:
                log_fail("Universal: Content too short")
        except Exception as e:
            log_fail("Universal failed", e)

    def test_tools_ecommerce(self):
        log_section("6. Web Scraper Tools")
        try:
            tid = self.client.run_tool(Amazon.Product(asin="059035342X"))
            log_pass(f"Task Created: {tid}")
            s = self.client.wait_for_task(tid, max_wait=180)
            if s.lower() in ("finished", "success", "ready"):
                log_pass(f"Task Succeeded: {s}")
            else:
                log_fail(f"Task status: {s}")
        except Exception as e:
            log_fail("Task failed", e)

    def test_tools_video(self):
        log_section("7. Video Tools")
        try:
            # STRICTLY MATCHING RAW SCRIPT PARAMETERS
            settings = CommonSettings(
                resolution="<=360p",
                video_codec="vp9",
                audio_format="opus",
                bitrate="<=320",
                selected_only=False,  # Will be converted to "false" string by new CommonSettings
                is_subtitles=False,
            )
            tid = self.client.run_tool(
                YouTube.VideoDownload(
                    url="https://www.youtube.com/watch?v=jNQXAC9IVRw",
                    common_settings=settings,
                )
            )
            log_pass(f"Video Task: {tid}")
            time.sleep(3)
            s = self.client.get_task_status(tid)
            if s.lower() == "failed":
                log_fail(
                    "Task failed server-side. (Check debug output for payload mismatch)"
                )
            else:
                log_pass(f"Initial Status: {s}")
        except Exception as e:
            log_fail("Video failed", e)

    def test_management(self):
        log_section("8. Management API")
        ip = "1.2.3.4"
        try:
            self.client.add_whitelist_ip(ip)
            log_pass(f"Added IP: {ip}")
            self.client.delete_whitelist_ip(ip)
            log_pass(f"Deleted IP: {ip}")
        except Exception as e:
            log_fail("Whitelist failed", e)

        user = f"t{uuid.uuid4().hex[:6]}"  # e.g., t1a2b3c
        pwd = "Pass123"
        try:
            self.client.create_proxy_user(user, pwd, traffic_limit=100)
            log_pass(f"Created User: {user}")

            # Debugging Update
            try:
                # API requires letters and numbers only. No underscores.
                # Generate a new random alphanum user.
                new_user_name = f"u{uuid.uuid4().hex[:6]}"

                self.client.update_proxy_user(
                    username=user,
                    new_username=new_user_name,
                    password=pwd,
                    traffic_limit=500,
                    status=True,
                    proxy_type=1,
                )
                log_pass(f"Updated User (Renamed to {new_user_name})")
                user = new_user_name
            except Exception as e:
                log_fail("Update User Failed", e)

            self.client.delete_proxy_user(user)
            log_pass("Deleted User")
        except Exception as e:
            log_fail("Proxy User failed", e)

    def test_new_features_audit(self):
        log_section("9. Features Audit (100% Coverage)")

        # 1. Latest Task Status
        try:
            status = self.client.get_latest_task_status()
            log_pass(f"Latest Task Status: {status}")
        except AttributeError:
            log_fail("Method get_latest_task_status() MISSING in SDK")
        except Exception as e:
            log_fail("Latest Task Status failed", e)

        # 2. Hourly Usage
        user = os.getenv("THORDATA_RESIDENTIAL_USERNAME")
        if user:
            try:
                # Use yesterday to ensure data exists, or just check call success
                from datetime import datetime, timedelta

                now = datetime.now()
                start = (now - timedelta(hours=2)).strftime("%Y-%m-%d %H")
                end = now.strftime("%Y-%m-%d %H")

                usage = self.client.get_proxy_user_usage_hour(user, start, end)
                log_pass(f"Hourly Usage: fetched {len(usage)} records")
            except AttributeError:
                log_fail("Method get_proxy_user_usage_hour() MISSING in SDK")
            except Exception as e:
                log_fail("Hourly Usage failed", e)
        else:
            log_skip("Skipping Hourly Usage (No residential user env)")

        # 3. Unlimited Monitor
        try:
            # We might not have a valid ins_id, so we expect a failure or empty return,
            # but we verify the METHOD exists and runs.
            # Using a dummy ins_id to test parameter passing
            try:
                self.client.unlimited.get_server_monitor("ins-dummy", "us", 1000, 2000)
                log_pass("Unlimited Server Monitor (Method Exists)")
            except ThordataAPIError:
                log_pass(
                    "Unlimited Server Monitor (Method Exists - API Rejected dummy ID)"
                )
        except AttributeError:
            log_fail("Method unlimited.get_server_monitor() MISSING in SDK")
        except Exception as e:
            log_fail("Unlimited Monitor failed", e)


if __name__ == "__main__":
    AcceptanceSuite().run_all()
