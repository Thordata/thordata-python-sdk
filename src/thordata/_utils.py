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


def build_auth_headers(token: str) -> Dict[str, str]:
    """
    Build authorization headers for API requests.

    Args:
        token: The scraper token.

    Returns:
        Headers dict with Authorization and Content-Type.
    """
    return {
        "Authorization": f"Bearer {token}",
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
