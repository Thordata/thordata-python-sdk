#!/usr/bin/env python
"""Proxy Network connectivity acceptance (read-only).

Goals:
- Validate Proxy Network auth + tunnel works with configured credentials.
- Avoid relying on a single endpoint: use multiple stable targets.
- Provide strong diagnostics (host/port/protocol/upstream proxy) to help root-cause failures.
- Never hang: hard timeout per request + bounded probe attempts.

This script does NOT modify account state.

Key points from your proven green run (examples/full_acceptance_test.py):
- Residential may require a dedicated entry host like vpnXXXX.pr.thordata.net.
  If you know it, set THORDATA_RESIDENTIAL_PROXY_HOST accordingly.

Recommended env pattern:
- THORDATA_RESIDENTIAL_PROXY_HOST=vpnXXXX.pr.thordata.net (only if needed)
- THORDATA_RESIDENTIAL_PROXY_PORT=9999
- THORDATA_RESIDENTIAL_PROXY_PROTOCOL=http
"""

from __future__ import annotations

import os
import sys
from dataclasses import dataclass
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from thordata import ProxyConfig, ProxyProduct, StaticISPProxy, ThordataClient

from .common import (
    AcceptanceConfig,
    ensure_output_dir,
    exit_with_result,
    is_integration_enabled,
    print_header,
    safe_call_with_timeout,
    write_json,
)


@dataclass(frozen=True)
class Probe:
    name: str
    kind: str  # proxy_config | static_isp
    host: str
    port: int
    protocol: str


TARGETS = [
    "https://httpbin.org/ip",
    "https://api64.ipify.org?format=json",
    "https://ifconfig.me/all.json",
]


def _env_username_password(product: ProxyProduct) -> tuple[str, str] | None:
    prefix = product.value.upper()
    u = os.getenv(f"THORDATA_{prefix}_USERNAME")
    p = os.getenv(f"THORDATA_{prefix}_PASSWORD")
    if u and p:
        return u, p
    return None


def _default_entry_host(product: ProxyProduct) -> str:
    return {
        ProxyProduct.RESIDENTIAL: "pr.thordata.net",
        ProxyProduct.DATACENTER: "dc.pr.thordata.net",
        ProxyProduct.MOBILE: "m.pr.thordata.net",
        ProxyProduct.ISP: "isp.pr.thordata.net",
    }.get(product, "pr.thordata.net")


def _default_entry_port(product: ProxyProduct) -> int:
    return {
        ProxyProduct.RESIDENTIAL: 9999,
        ProxyProduct.DATACENTER: 7777,
        ProxyProduct.MOBILE: 5555,
        ProxyProduct.ISP: 6666,
    }.get(product, 9999)


def _proxy_host_port_protocol_candidates(
    product: ProxyProduct,
) -> list[tuple[str, int, str]]:
    prefix = product.value.upper()

    # hosts
    hosts: list[str] = []

    # Product-specific host overrides
    if product == ProxyProduct.ISP:
        isp_host = os.getenv("THORDATA_ISP_HOST")
        if isp_host:
            hosts.append(isp_host)

    prod_host = os.getenv(f"THORDATA_{prefix}_PROXY_HOST")
    if prod_host:
        hosts.append(prod_host)

    # Generic host override
    generic_host = os.getenv("THORDATA_PROXY_HOST")
    if generic_host:
        hosts.append(generic_host)

    # Known defaults
    hosts.append(_default_entry_host(product))

    hosts = [h.strip() for h in hosts if h and h.strip()]
    hosts = list(dict.fromkeys(hosts))

    # ports
    ports: list[int] = []
    prod_port_raw = os.getenv(f"THORDATA_{prefix}_PROXY_PORT")
    if prod_port_raw and prod_port_raw.isdigit():
        ports.append(int(prod_port_raw))

    generic_port_raw = os.getenv("THORDATA_PROXY_PORT")
    if generic_port_raw and generic_port_raw.isdigit():
        ports.append(int(generic_port_raw))

    ports.append(_default_entry_port(product))
    ports = list(dict.fromkeys(ports))

    # protos
    protos: list[str] = []
    prod_proto = os.getenv(f"THORDATA_{prefix}_PROXY_PROTOCOL")
    if prod_proto:
        protos.append(prod_proto)

    generic_proto = os.getenv("THORDATA_PROXY_PROTOCOL")
    if generic_proto:
        protos.append(generic_proto)

    # prefer http first
    protos.extend(["http", "https", "socks5h"])
    protos = [p.strip().lower() for p in protos if p and p.strip()]
    protos = list(dict.fromkeys(protos))

    # Build candidates with product's default combo first
    candidates: list[tuple[str, int, str]] = []

    # 1) If env provides explicit product host/port/proto, try those first
    if prod_host and prod_port_raw and prod_port_raw.isdigit():
        pport = int(prod_port_raw)
        pproto = (prod_proto or "http").lower()
        candidates.append((prod_host, pport, pproto))

    # 2) Default host+port with http first
    candidates.append(
        (_default_entry_host(product), _default_entry_port(product), "http")
    )

    # 3) All combinations
    for host in hosts:
        for port in ports:
            for proto in protos:
                tup = (host, port, proto)
                if tup not in candidates:
                    candidates.append(tup)

    return candidates


def _build_probes(product: ProxyProduct) -> list[Probe]:
    probes: list[Probe] = []

    if product == ProxyProduct.ISP and os.getenv("THORDATA_ISP_HOST"):
        for host, port, proto in _proxy_host_port_protocol_candidates(product):
            probes.append(
                Probe(
                    name=f"static_isp:{proto}@{host}:{port}",
                    kind="static_isp",
                    host=host,
                    port=port,
                    protocol=proto,
                )
            )
        return probes

    for host, port, proto in _proxy_host_port_protocol_candidates(product):
        probes.append(
            Probe(
                name=f"{product.value}:{proto}@{host}:{port}",
                kind="proxy_config",
                host=host,
                port=port,
                protocol=proto,
            )
        )

    return probes


def main() -> bool:
    print_header("PROXY CONNECTIVITY ACCEPTANCE (READ-ONLY)")
    if not is_integration_enabled():
        print("THORDATA_INTEGRATION not set, skipping.")
        return True

    out = ensure_output_dir("proxy")
    cfg = AcceptanceConfig(timeout=60)

    upstream = os.getenv("THORDATA_UPSTREAM_PROXY")
    if upstream:
        print(f"[INFO] THORDATA_UPSTREAM_PROXY is set: {upstream}")

    client = ThordataClient(timeout=cfg.timeout)

    products = [
        ProxyProduct.RESIDENTIAL,
        ProxyProduct.DATACENTER,
        ProxyProduct.MOBILE,
        ProxyProduct.ISP,
    ]

    results: dict[str, object] = {
        "targets": TARGETS,
        "upstream_proxy": upstream,
        "products": {},
    }

    max_probes_per_product = 6
    request_timeout = float(os.getenv("THORDATA_ACCEPT_PROXY_REQ_TIMEOUT", "20"))

    all_ok = True

    for product in products:
        creds = _env_username_password(product)
        if not creds:
            continue
        username, password = creds

        print(f"\n--- Testing product: {product.value} ---")
        probes = _build_probes(product)

        prod_res: dict[str, object] = {
            "probe_count": len(probes),
            "max_probes_used": max_probes_per_product,
            "request_timeout": request_timeout,
            "probes": [],
        }

        ok_any = False

        for i, probe in enumerate(probes[:max_probes_per_product], start=1):
            print(
                f"[{product.value}] probe {i}/{min(len(probes), max_probes_per_product)} -> {probe.name}"
            )

            probe_item: dict[str, object] = {
                "name": probe.name,
                "kind": probe.kind,
                "host": probe.host,
                "port": probe.port,
                "protocol": probe.protocol,
                "attempts": [],
            }

            try:
                if probe.kind == "static_isp":
                    proxy_obj = StaticISPProxy(
                        host=probe.host,
                        username=username,
                        password=password,
                        port=probe.port,
                        protocol=probe.protocol,
                    )
                else:
                    proxy_obj = ProxyConfig(
                        username=username,
                        password=password,
                        product=product,
                        host=probe.host,
                        port=probe.port,
                        protocol=probe.protocol,
                    )
            except Exception as e:
                probe_item["error"] = f"proxy_build_error: {e}"
                prod_res["probes"].append(probe_item)
                continue

            for target in TARGETS:
                ok, resp_or_err = safe_call_with_timeout(
                    client.get,
                    target,
                    proxy_config=proxy_obj,
                    timeout=cfg.timeout,
                    hard_timeout=request_timeout,
                )

                if not ok:
                    probe_item["attempts"].append(
                        {"url": target, "ok": False, "error": str(resp_or_err)}
                    )
                    continue

                resp = resp_or_err
                try:
                    data = resp.json()
                except Exception:
                    data = {"text": resp.text[:200]}

                probe_item["attempts"].append(
                    {
                        "url": target,
                        "ok": True,
                        "status_code": resp.status_code,
                        "data": data,
                    }
                )
                ok_any = True
                break

            prod_res["probes"].append(probe_item)
            if ok_any:
                break

        results["products"][product.value] = prod_res

        if ok_any:
            print("  [OK] At least one probe worked.")
        else:
            print("  [FAIL] No probe worked.")
            all_ok = False

    write_json(out / "proxy_connectivity.json", results)
    client.close()

    print("\n--- Proxy Connectivity Summary ---")
    if all_ok:
        print("✅ Proxy connectivity passed.")
    else:
        print(
            "❌ Proxy connectivity failed for one or more products. See artifacts for details."
        )

    return all_ok


if __name__ == "__main__":
    exit_with_result(main())
