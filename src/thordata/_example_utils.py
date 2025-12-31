from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Iterable, Optional

try:
    from dotenv import load_dotenv
except Exception:  # pragma: no cover
    load_dotenv = None


def load_env() -> None:
    """Load .env from repo root if python-dotenv is installed."""
    if load_dotenv is None:
        return
    repo_root = Path(__file__).resolve().parents[2]
    load_dotenv(dotenv_path=repo_root / ".env")


def env(name: str) -> str:
    return (os.getenv(name) or "").strip()


def skip_if_missing(required: Iterable[str], *, tip: Optional[str] = None) -> bool:
    missing = [k for k in required if not env(k)]
    if not missing:
        return False
    print("Skipping live example: missing env:", ", ".join(missing))
    if tip:
        print(tip)
    else:
        print("Tip: copy .env.example to .env and fill values, then re-run.")
    return True


def parse_json_env(name: str, default: str = "{}") -> Any:
    raw = env(name) or default
    return json.loads(raw)


def normalize_task_parameters(raw: Any) -> dict[str, Any]:
    """Accept {..} or [{..}] and return a single dict for create_scraper_task(parameters=...)."""
    if isinstance(raw, list):
        if not raw:
            raise ValueError("Task parameters JSON array must not be empty")
        raw = raw[0]
    if not isinstance(raw, dict):
        raise ValueError("Task parameters must be a JSON object (or array of objects)")
    return raw