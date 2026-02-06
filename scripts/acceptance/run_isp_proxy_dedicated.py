#!/usr/bin/env python
"""Dedicated acceptance test for ISP Proxy connectivity.

This script uses specific credentials and an upstream proxy to isolate
and debug ISP proxy issues reported in the full connectivity test.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from thordata import ProxyConfig, ProxyProduct, ThordataClient
from thordata.exceptions import ThordataNetworkError

from .common import (
    exit_with_result,
    is_integration_enabled,
    load_dotenv_if_present,
    print_header,
)


def main() -> bool:
    print_header("ISP PROXY DEDICATED CONNECTIVITY TEST")

    if not is_integration_enabled():
        print("THORDATA_INTEGRATION not set, skipping.")
        return True

    load_dotenv_if_present(override=True)

    # Explicitly set upstream proxy for this test run
    # This ensures we are testing through the user's Clash Verge setup
    os.environ["THORDATA_UPSTREAM_PROXY"] = "http://127.0.0.1:7897"
    print(f"Using upstream proxy: {os.environ['THORDATA_UPSTREAM_PROXY']}")

    # Use credentials provided by the user
    isp_host = "38.213.208.238"
    isp_port = 6666
    isp_user = "Bl9xSZSsJAdF"
    isp_pass = "Iu1zFeZDa4"

    print(f"Testing ISP Proxy: {isp_user}@{isp_host}:{isp_port}")

    client = ThordataClient()

    proxy_config = ProxyConfig(
        product=ProxyProduct.ISP,
        host=isp_host,
        port=isp_port,
        username=isp_user,
        password=isp_pass,
        protocol="http",  # Start with the most common protocol
    )

    all_ok = False
    try:
        # The client will automatically use the THORDATA_UPSTREAM_PROXY
        resp = client.get(
            "https://httpbin.org/ip", proxy_config=proxy_config, timeout=60
        )
        resp.raise_for_status()
        data = resp.json()
        origin_ip = data.get("origin")

        if origin_ip:
            print(f"  [OK] Successfully connected. Origin IP: {origin_ip}")
            # A simple check to ensure it's not the local IP
            if "127.0.0.1" not in origin_ip and "localhost" not in origin_ip:
                all_ok = True
            else:
                print(
                    "  [WARN] Origin IP seems to be local, proxy might not be working as expected."
                )
        else:
            print(f"  [FAIL] Could not determine origin IP from response: {data}")

    except ThordataNetworkError as e:
        print(f"  [FAIL] Network error during connection: {e}")
    except Exception as e:
        print(f"  [FAIL] An unexpected error occurred: {e}")
    finally:
        client.close()

    print("\n--- ISP Proxy Test Summary ---")
    if all_ok:
        print("ISP Proxy connectivity test passed.")
    else:
        print("ISP Proxy connectivity test failed.")

    return all_ok


if __name__ == "__main__":
    exit_with_result(main())
