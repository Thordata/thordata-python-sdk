import os

from dotenv import load_dotenv

from thordata import ThordataClient
from thordata.models import ProxyConfig, ProxyProduct

TARGET = "https://ipinfo.thordata.com"


def must_env(name: str) -> str:
    v = (os.getenv(name) or "").strip()
    if not v:
        raise RuntimeError(f"Missing {name} in env/.env")
    return v


def run_one(proto: str) -> None:
    # Load env from .env
    load_dotenv(".env")

    # Host selection:
    # - For HTTP/HTTPS proxy: use dashboard shard host (THORDATA_PROXY_HOST)
    # - For SOCKS5h: allow overriding via THORDATA_SOCKS_PROXY_HOST, otherwise fall back to dashboard host
    if proto.startswith("socks"):
        host = (
            os.getenv("THORDATA_SOCKS_PROXY_HOST")
            or os.getenv("THORDATA_PROXY_HOST")
            or ""
        ).strip()
        if not host:
            host = "t.pr.thordata.net"  # fallback only
    else:
        host = must_env("THORDATA_PROXY_HOST")

    port = int((os.getenv("THORDATA_PROXY_PORT") or "9999").strip())

    u = must_env("THORDATA_RESIDENTIAL_USERNAME")
    p = must_env("THORDATA_RESIDENTIAL_PASSWORD")

    client = ThordataClient(
        scraper_token=(os.getenv("THORDATA_SCRAPER_TOKEN") or "dummy").strip()
    )

    proxy = ProxyConfig(
        username=u,
        password=p,
        product=ProxyProduct.RESIDENTIAL,
        host=host,
        port=port,
        protocol=proto,
        country="us",
    )

    print("====", proto, "====")
    print("proxy_endpoint:", proxy.build_proxy_endpoint())

    r = client.get(TARGET, proxy_config=proxy, timeout=30)
    print("status:", r.status_code)
    print("body:", r.text[:200])


def main() -> None:
    for proto in ["http", "https", "socks5h"]:
        try:
            run_one(proto)
        except Exception as e:
            print("====", proto, "FAILED ====")
            print(repr(e))


if __name__ == "__main__":
    main()
