"""
Low-level networking tunnel utilities.
Handles Upstream Proxies, TLS-in-TLS wrapping, and SOCKS handshakes.
"""

from __future__ import annotations

import base64
import contextlib
import logging
import socket
import ssl
import time
from typing import Any, Optional
from urllib.parse import urlparse

try:
    import socks

    HAS_PYSOCKS = True
except ImportError:
    HAS_PYSOCKS = False

logger = logging.getLogger(__name__)


def parse_upstream_proxy() -> dict[str, Any] | None:
    import os

    upstream_url = os.environ.get("THORDATA_UPSTREAM_PROXY", "").strip()
    if not upstream_url:
        return None

    parsed = urlparse(upstream_url)
    scheme = (parsed.scheme or "").lower()

    # Normalize scheme
    if scheme in ("socks5", "socks5h"):
        scheme = "socks5"
    elif scheme in ("http", "https"):
        scheme = "http"
    else:
        return None

    return {
        "scheme": scheme,
        "host": parsed.hostname or "127.0.0.1",
        "port": parsed.port or 7890,
        "username": parsed.username,
        "password": parsed.password,
    }


class UpstreamProxySocketFactory:
    """Creates sockets routed through an upstream proxy."""

    def __init__(self, upstream_config: dict[str, Any]):
        self.config = upstream_config

    def create_connection(
        self,
        address: tuple[str, int],
        timeout: float | None = None,
    ) -> socket.socket:
        scheme = self.config["scheme"]
        if timeout is None or timeout <= 0:
            timeout = 30.0

        if scheme == "socks5":
            return self._create_socks_connection(address, timeout)
        else:
            return self._create_http_tunnel(address, timeout)

    def _create_socks_connection(
        self, address: tuple[str, int], timeout: float
    ) -> socket.socket:
        if not HAS_PYSOCKS:
            raise ImportError("PySocks is required for upstream SOCKS proxy.")

        sock = socks.socksocket(socket.AF_INET, socket.SOCK_STREAM)
        sock.set_proxy(
            socks.SOCKS5,
            self.config["host"],
            self.config["port"],
            rdns=True,
            username=self.config.get("username"),
            password=self.config.get("password"),
        )
        sock.settimeout(timeout)
        try:
            sock.connect(address)
        except Exception:
            sock.close()
            raise
        return sock

    def _create_http_tunnel(
        self, address: tuple[str, int], timeout: float
    ) -> socket.socket:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)

        try:
            # 1. Connect to Upstream
            sock.connect((self.config["host"], self.config["port"]))

            # 2. Send CONNECT
            target_host, target_port = address
            connect_req = f"CONNECT {target_host}:{target_port} HTTP/1.1\r\n"
            connect_req += f"Host: {target_host}:{target_port}\r\n"

            if self.config.get("username"):
                creds = f"{self.config['username']}:{self.config.get('password','')}"
                b64_creds = base64.b64encode(creds.encode()).decode()
                connect_req += f"Proxy-Authorization: Basic {b64_creds}\r\n"

            connect_req += "\r\n"
            sock.sendall(connect_req.encode())

            # 3. Read Response (Byte by byte to avoid over-reading)
            resp = b""
            while b"\r\n\r\n" not in resp:
                chunk = sock.recv(1)
                if not chunk:
                    raise ConnectionError(
                        "Upstream proxy closed connection during CONNECT"
                    )
                resp += chunk

            status_line = resp.split(b"\r\n")[0]
            if b"200" not in status_line:
                raise ConnectionError(f"Upstream proxy CONNECT failed: {status_line}")

        except Exception:
            sock.close()
            raise

        return sock


class TLSInTLSSocket:
    def __init__(
        self,
        outer: ssl.SSLSocket,
        ssl_obj: ssl.SSLObject,
        incoming: ssl.MemoryBIO,
        outgoing: ssl.MemoryBIO,
    ):
        self._outer = outer
        self._ssl = ssl_obj
        self._incoming = incoming
        self._outgoing = outgoing
        self._timeout: Optional[float] = None

    def settimeout(self, t: float | None) -> None:
        self._timeout = t
        self._outer.settimeout(t)

    def sendall(self, data: bytes) -> None:
        try:
            self._ssl.write(data)
            enc = self._outgoing.read()
            if enc:
                self._outer.sendall(enc)
        except ssl.SSLWantReadError:
            pass

    def recv(self, bufsize: int) -> bytes:
        while True:
            try:
                return self._ssl.read(bufsize)
            except ssl.SSLWantReadError:
                try:
                    data = self._outer.recv(8192)
                    if not data:
                        return b""
                    self._incoming.write(data)
                except socket.timeout:
                    raise
            except ssl.SSLWantWriteError:
                enc = self._outgoing.read()
                if enc:
                    self._outer.sendall(enc)

    def close(self) -> None:
        with contextlib.suppress(Exception):
            self._outer.close()


def create_tls_in_tls(
    outer_sock: ssl.SSLSocket, hostname: str, timeout: float
) -> TLSInTLSSocket:
    ctx = ssl.create_default_context()
    incoming = ssl.MemoryBIO()
    outgoing = ssl.MemoryBIO()
    ssl_obj = ctx.wrap_bio(incoming, outgoing, server_hostname=hostname)

    outer_sock.settimeout(timeout)
    start_time = time.time()

    while True:
        if time.time() - start_time > timeout:
            raise TimeoutError("TLS handshake timed out")
        try:
            ssl_obj.do_handshake()
            break
        except ssl.SSLWantReadError:
            data = outgoing.read()
            if data:
                outer_sock.sendall(data)
            try:
                chunk = outer_sock.recv(4096)
                if not chunk:
                    raise ConnectionError("Connection closed")
                incoming.write(chunk)
            except socket.timeout:
                pass
        except ssl.SSLWantWriteError:
            data = outgoing.read()
            if data:
                outer_sock.sendall(data)

    return TLSInTLSSocket(outer_sock, ssl_obj, incoming, outgoing)


def socks5_handshake(
    sock: socket.socket,
    target_host: str,
    target_port: int,
    user: str | None,
    pwd: str | None,
) -> socket.socket:
    # 1. Auth Method
    if user and pwd:
        sock.sendall(b"\x05\x02\x00\x02")
    else:
        sock.sendall(b"\x05\x01\x00")

    resp = sock.recv(2)
    if not resp or resp[0] != 0x05:
        raise ConnectionError(f"Invalid SOCKS5 init response: {resp}")

    if resp[1] == 0x02:  # User/Pass
        u_bytes = (user or "").encode()
        p_bytes = (pwd or "").encode()
        auth_payload = (
            b"\x01" + bytes([len(u_bytes)]) + u_bytes + bytes([len(p_bytes)]) + p_bytes
        )
        sock.sendall(auth_payload)
        auth_resp = sock.recv(2)
        if not auth_resp or auth_resp[1] != 0x00:
            raise ConnectionError("SOCKS5 Authentication failed")
    elif resp[1] == 0xFF:
        raise ConnectionError("No acceptable authentication methods")

    # 2. Connect
    req = (
        b"\x05\x01\x00\x03"
        + bytes([len(target_host)])
        + target_host.encode()
        + target_port.to_bytes(2, "big")
    )
    sock.sendall(req)

    # 3. Response
    resp = sock.recv(4)
    if not resp or resp[1] != 0x00:
        err = resp[1] if resp else "Empty"
        raise ConnectionError(f"SOCKS5 Connect failed, error: {err}")

    atype = resp[3]
    if atype == 1:
        sock.recv(4 + 2)
    elif atype == 3:
        sock.recv(sock.recv(1)[0] + 2)
    elif atype == 4:
        sock.recv(16 + 2)

    return sock
