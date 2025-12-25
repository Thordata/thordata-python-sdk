"""
Internal utility functions for the Thordata Python SDK.

These are not part of the public API and may change without notice.
"""

from __future__ import annotations

import base64
import json
import logging
from typing import Any, Dict

logger = logging.getLogger(__name__)


def parse_json_response(data: Any) -> Any:
    """
    Parse a response that might be double-encoded JSON.

    Some API endpoints return JSON as a string inside JSON.

    Args:
        data: The response data to parse.

    Returns:
        Parsed data.
    """
    if isinstance(data, str):
        try:
            return json.loads(data)
        except json.JSONDecodeError:
            return data
    return data


def decode_base64_image(png_str: str) -> bytes:
    """
    Decode a base64-encoded PNG image.

    Handles Data URI scheme (data:image/png;base64,...) and fixes padding.

    Args:
        png_str: Base64-encoded string, possibly with Data URI prefix.

    Returns:
        Decoded PNG bytes.

    Raises:
        ValueError: If the string is empty or cannot be decoded.
    """
    if not png_str:
        raise ValueError("Empty PNG data received")

    # Remove Data URI scheme if present
    if "," in png_str:
        png_str = png_str.split(",", 1)[1]

    # Clean up whitespace
    png_str = png_str.replace("\n", "").replace("\r", "").replace(" ", "")

    # Fix Base64 padding
    missing_padding = len(png_str) % 4
    if missing_padding:
        png_str += "=" * (4 - missing_padding)

    try:
        return base64.b64decode(png_str)
    except Exception as e:
        raise ValueError(f"Failed to decode base64 image: {e}") from e


def build_auth_headers(token: str, mode: str = "bearer") -> Dict[str, str]:
    """
    Build authorization headers for API requests.

    Supports two modes:
    - bearer: Authorization: Bearer <token> (Thordata Docs examples)
    - header_token: token: <token> (Interface documentation)

    Args:
        token: The scraper token.
        mode: Authentication mode ("bearer" or "header_token").

    Returns:
        Headers dict with Authorization/token and Content-Type.
    """
    headers = {
        "Content-Type": "application/x-www-form-urlencoded",
    }

    if mode == "bearer":
        headers["Authorization"] = f"Bearer {token}"
    elif mode == "header_token":
        headers["token"] = token
    else:
        # Fallback to bearer for compatibility
        headers["Authorization"] = f"Bearer {token}"

    return headers


def build_builder_headers(
    scraper_token: str,
    public_token: str,
    public_key: str,
) -> Dict[str, str]:
    """
    Build headers for Web Scraper builder API.

    Builder requires THREE auth headers per official docs:
    - token: public token
    - key: public key
    - Authorization: Bearer scraper_token

    Args:
        scraper_token: The scraper API token.
        public_token: The public API token.
        public_key: The public API key.

    Returns:
        Headers dict with all required auth headers.
    """
    return {
        "token": public_token,
        "key": public_key,
        "Authorization": f"Bearer {scraper_token}",
        "Content-Type": "application/x-www-form-urlencoded",
    }


def build_public_api_headers(public_token: str, public_key: str) -> Dict[str, str]:
    """
    Build headers for public API requests (task status, locations, etc.)

    Args:
        public_token: The public API token.
        public_key: The public API key.

    Returns:
        Headers dict with token, key, and Content-Type.
    """
    return {
        "token": public_token,
        "key": public_key,
        "Content-Type": "application/x-www-form-urlencoded",
    }


def extract_error_message(payload: Any) -> str:
    """
    Extract a human-readable error message from an API response.

    Args:
        payload: The API response payload.

    Returns:
        Error message string.
    """
    if isinstance(payload, dict):
        # Try common error message fields
        for key in ("msg", "message", "error", "detail", "description"):
            if key in payload:
                return str(payload[key])

        # Fall back to full payload
        return str(payload)

    return str(payload)


def build_user_agent(sdk_version: str, http_client: str) -> str:
    """
    Build a default User-Agent for the SDK.

    Args:
        sdk_version: SDK version string.
        http_client: "requests" or "aiohttp" (or any identifier).

    Returns:
        A User-Agent string.
    """
    import platform

    py = platform.python_version()
    system = platform.system()
    return f"thordata-python-sdk/{sdk_version} (python {py}; {system}; {http_client})"


def build_sign_headers(sign: str, api_key: str) -> Dict[str, str]:
    """
    Build headers for Public API NEW (sign + apiKey authentication).

    This is a different authentication system from token+key.

    Args:
        sign: The sign value from Dashboard (immutable).
        api_key: The apiKey value from Dashboard (can be changed).

    Returns:
        Headers dict with sign, apiKey, and Content-Type.
    """
    return {
        "sign": sign,
        "apiKey": api_key,
        "Content-Type": "application/x-www-form-urlencoded",
    }
