"""
Network & Proxy Diagnostic Tool
================================
This script bypasses the SDK to test raw connectivity.
It helps identify if the issue is with:
1. Local Network/Firewall
2. Upstream Proxy (Clash/V2Ray)
3. Thordata Proxy Server
4. SSL/TLS Configuration
"""

import base64
import os
import socket
from urllib.parse import urlparse

import requests

# --- CONFIG ---
TARGET_URL = "http://httpbin.org/ip"  # Use HTTP to avoid SSL complexity first
TIMEOUT = 20


def print_header(title):
    print(f"\n{'='*10} {title} {'='*10}")


def check_direct_connect():
    print_header("1. Direct Connection Check")
    try:
        resp = requests.get(TARGET_URL, timeout=5)
        print(f"[OK] Direct Access OK. IP: {resp.json().get('origin')}")
        return True
    except Exception as e:
        print(f"[FAIL] Direct Access Failed: {e}")
        return False


def check_upstream_proxy():
    print_header("2. Upstream Proxy Check")
    upstream = os.getenv("THORDATA_UPSTREAM_PROXY")
    if not upstream:
        print("[WARN] No THORDATA_UPSTREAM_PROXY configured in env.")
        return

    print(f"Testing Upstream: {upstream}")
    proxies = {"http": upstream, "https": upstream}
    try:
        resp = requests.get("http://www.google.com", proxies=proxies, timeout=10)
        print(f"[OK] Upstream to Google OK. Status: {resp.status_code}")
    except Exception as e:
        print(f"[FAIL] Upstream to Google Failed: {e}")


def manual_proxy_connect(name, host, port, user, password):
    print_header(f"3. Testing Thordata: {name}")
    print(f"Endpoint: {host}:{port}")

    # We construct a manual CONNECT request to simulate what curl does
    # This helps see exactly where the handshake dies

    upstream = os.getenv("THORDATA_UPSTREAM_PROXY")

    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(TIMEOUT)

        if upstream:
            # Connect via Upstream
            up_parsed = urlparse(upstream)
            print(f"-> Connecting via Upstream: {up_parsed.hostname}:{up_parsed.port}")
            s.connect((up_parsed.hostname, up_parsed.port))

            # 1. Handshake with Upstream to connect to Thordata
            # If upstream is SOCKS, this gets complex. Assuming HTTP Upstream for simplicity here.
            # If SOCKS upstream, this raw test might fail, which is a finding in itself.
            if up_parsed.scheme.startswith("http"):
                connect_msg = (
                    f"CONNECT {host}:{port} HTTP/1.1\r\nHost: {host}:{port}\r\n\r\n"
                )
                s.sendall(connect_msg.encode())
                data = s.recv(1024)
                if b"200" not in data.split(b"\r\n")[0]:
                    print(f"❌ Upstream CONNECT failed: {data}")
                    return
        else:
            # Connect Direct
            s.connect((host, int(port)))

        print("-> TCP Connection Established")

        # 2. Handshake with Thordata (HTTP CONNECT)
        # Auth
        auth_str = f"{user}:{password}"
        auth_b64 = base64.b64encode(auth_str.encode()).decode()

        # Target: httpbin.org:80
        target_host = "httpbin.org"
        req = (
            f"CONNECT {target_host}:80 HTTP/1.1\r\n"
            f"Host: {target_host}:80\r\n"
            f"Proxy-Authorization: Basic {auth_b64}\r\n"
            f"\r\n"
        )
        s.sendall(req.encode())

        # Read Response
        data = s.recv(4096)
        head = data.split(b"\r\n\r\n")[0].decode(errors="ignore")

        if "200 Connection established" in head:
            print("[OK] Thordata Auth Success! (HTTP Tunnel Established)")
        elif "407" in head:
            print("[FAIL] Thordata Auth Failed (407 Proxy Authentication Required)")
        else:
            print(f"[FAIL] Thordata Handshake Failed. Response:\n{head}")

    except Exception as e:
        print(f"[FAIL] Connection Error: {e}")
    finally:
        s.close()


def main():
    try:
        from dotenv import load_dotenv

        load_dotenv()
    except Exception:  # Fix E722
        pass

    check_direct_connect()
    check_upstream_proxy()

    # Test Residential
    u = os.getenv("THORDATA_RESIDENTIAL_USERNAME")
    p = os.getenv("THORDATA_RESIDENTIAL_PASSWORD")
    h = os.getenv("THORDATA_PROXY_HOST", "pr.thordata.net")
    if u:
        manual_proxy_connect("Residential", h, 9999, u, p)

    # Test Datacenter
    du = os.getenv("THORDATA_DATACENTER_USERNAME")
    dp = os.getenv("THORDATA_DATACENTER_PASSWORD")
    if du:
        manual_proxy_connect("Datacenter", "dc.pr.thordata.net", 7777, du, dp)


if __name__ == "__main__":
    main()
