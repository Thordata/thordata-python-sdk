"""
Lightweight helpers for loading environment variables from a `.env` file.

This module is intentionally dependency‑free (no python-dotenv) so that
it can be safely used in any environment:

    from thordata.env import load_env_file
    load_env_file()  # load ./.env if present

Behavior:
- Lines starting with `#` or blank lines are ignored.
- Only simple `KEY=VALUE` pairs are supported.
- Surrounding single/double quotes around VALUE are stripped.
- By default, existing OS environment variables are NOT overridden.
"""

from __future__ import annotations

import os
from pathlib import Path

__all__ = ["load_env_file"]


def _parse_env_line(line: str) -> tuple[str, str] | None:
    """Parse a single KEY=VALUE line."""
    if not line or line.startswith("#") or "=" not in line:
        return None
    key, val = line.split("=", 1)
    key = key.strip()
    val = val.strip()
    if not key:
        return None

    # Strip surrounding quotes
    if (val.startswith('"') and val.endswith('"')) or (
        val.startswith("'") and val.endswith("'")
    ):
        val = val[1:-1]
    return key, val


def load_env_file(
    path: str | os.PathLike[str] = ".env",
    *,
    override: bool = False,
) -> None:
    """
    Load environment variables from a `.env` file if it exists.

    Args:
        path: Path to `.env` file. Defaults to "./.env".
        override: If True, always override existing environment variables.
                  If False (default), only set variables that are missing
                  or empty in `os.environ`.

    This helper is intentionally conservative and side‑effect free:
    - It does nothing if the file does not exist.
    - It never raises for malformed lines; they are simply skipped.
    """
    env_path = Path(path)
    if not env_path.exists():
        return

    try:
        content = env_path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        content = env_path.read_text(encoding="utf-8", errors="ignore")

    for raw in content.splitlines():
        parsed = _parse_env_line(raw.strip())
        if not parsed:
            continue
        key, val = parsed
        if override or key not in os.environ or os.environ.get(key, "") == "":
            os.environ[key] = val
