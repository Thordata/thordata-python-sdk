"""
Thordata Proxy Network Demo
---------------------------

Goal: Verify proxy network connectivity with minimal overhead:
- Load Residential proxy credentials and optional upstream proxy (e.g., Clash) from .env
- Create a ProxyConfig
- Access https://httpbin.org/ip through Thordata proxy and print the returned IP
- Support multiple Clash ports: 7898 (SOCKS5) and 7899 (HTTPS)

Setup:
- Fill in .env:
    THORDATA_RESIDENTIAL_USERNAME=...
    THORDATA_RESIDENTIAL_PASSWORD=...
  If using Clash upstream proxy, set:
    THORDATA_UPSTREAM_PROXY=https://127.0.0.1:7899  # HTTPS proxy
    or
    THORDATA_UPSTREAM_PROXY=socks5://127.0.0.1:7898  # SOCKS5 proxy
"""

from __future__ import annotations

import os

from thordata import (
    ProxyConfig,
    ProxyProduct,
    ThordataClient,
    load_env_file,
)


def main() -> int:
    # Load .env from repo root (best-effort, ignore if not present)
    repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    load_env_file(os.path.join(repo_root, ".env"))

    username = os.getenv("THORDATA_RESIDENTIAL_USERNAME")
    password = os.getenv("THORDATA_RESIDENTIAL_PASSWORD")
    if not username or not password:
        print(
            "Missing THORDATA_RESIDENTIAL_USERNAME / THORDATA_RESIDENTIAL_PASSWORD in env/.env"
        )
        return 1

    client = ThordataClient()

    # Base config (will override protocol/port during probing)
    base_proxy = ProxyConfig(
        username=username,
        password=password,
        product=ProxyProduct.RESIDENTIAL,
        country=os.getenv("THORDATA_DEMO_PROXY_COUNTRY", "us"),
    )

    upstream = os.getenv("THORDATA_UPSTREAM_PROXY")
    if upstream:
        print(f"[OK] Upstream proxy detected: {upstream}")
        print(
            "   Will attempt to connect to Thordata proxy server via upstream proxy..."
        )
    else:
        print(
            "[INFO] No upstream proxy configured; consider setting THORDATA_UPSTREAM_PROXY for Clash."
        )
        print("       Clash Verge ports: socks5=7898, http(s)=7899")

    # If upstream is not set but user is using Clash system proxy/TUN, allow auto-pick
    # Note: SDK tunnel uses THORDATA_UPSTREAM_PROXY. System proxy is not automatically used.
    if not upstream and os.getenv("THORDATA_DEMO_ASSUME_CLASH", "").lower() in {
        "1",
        "true",
        "yes",
    }:
        os.environ["THORDATA_UPSTREAM_PROXY"] = "socks5://127.0.0.1:7898"
        upstream = os.environ["THORDATA_UPSTREAM_PROXY"]
        print(
            f"[INFO] THORDATA_DEMO_ASSUME_CLASH enabled; set THORDATA_UPSTREAM_PROXY={upstream}"
        )

    print("\nTesting proxy network connection (auto-probing)...")
    print("Target: https://httpbin.org/ip")

    probe_ports = [9999]
    probe_protocols = ["http", "https", "socks5h"]

    # If upstream is set and looks like Clash, prefer plain HTTP to Thordata first
    # The upstream protocol itself is defined in THORDATA_UPSTREAM_PROXY.

    last_err: Exception | None = None
    resp = None

    for proto in probe_protocols:
        for port in probe_ports:
            proxy = ProxyConfig(
                username=base_proxy.username,
                password=base_proxy.password,
                product=base_proxy.product,
                country=base_proxy.country,
                host=base_proxy.host,
                protocol=proto,
                port=port,
            )
            print(
                f"\n[PROBE] protocol={proto} host={proxy.host or 'pr.thordata.net'} port={port}"
            )
            try:
                resp = client.get(
                    "https://httpbin.org/ip", proxy_config=proxy, timeout=60
                )
                if resp.status_code == 200:
                    break
            except Exception as e:
                last_err = e
                print(f"[PROBE-FAIL] {type(e).__name__}: {e}")
                continue
        if resp is not None and getattr(resp, "status_code", 0) == 200:
            break

    if resp is None or resp.status_code != 200:
        err_msg = str(last_err) if last_err is not None else "All proxy probes failed"
        print(f"[FAIL] Proxy connectivity failed after probing. Last error: {err_msg}")
        if not upstream:
            print(
                "[TIP] You are using Clash system proxy/TUN. Set THORDATA_UPSTREAM_PROXY explicitly:"
            )
            print("      - SOCKS5: socks5://127.0.0.1:7898")
            print("      - HTTPS:  https://127.0.0.1:7899")
            print("      Or run with: THORDATA_DEMO_ASSUME_CLASH=true")
        return 2

    try:
        data = resp.json()
        origin_ip = data.get("origin", "unknown")
    except Exception:
        print("[WARN] Received non-JSON response:")
        print(resp.text[:200])
        return 4

    print("\n[OK] Proxy network connection successful!")
    print(f"   Returned IP: {origin_ip}")

    # Try to get local IP for comparison
    try:
        import requests

        local_resp = requests.get("https://httpbin.org/ip", timeout=10)
        local_ip = local_resp.json().get("origin", "unknown")
        if origin_ip != local_ip:
            print(f"   Local IP: {local_ip}")
            print("   [OK] IP changed, proxy is working correctly!")
        else:
            print(
                "   [WARN] Warning: Returned IP matches local IP, proxy may not be active"
            )
    except Exception:
        print("   [INFO] Unable to get local IP for comparison")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
