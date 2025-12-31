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


def output_dir() -> Path:
    """Return output dir for examples; defaults to examples/output (ignored by git)."""
    repo_root = Path(__file__).resolve().parents[2]
    d = env("THORDATA_OUTPUT_DIR") or str(repo_root / "examples" / "output")
    p = Path(d)
    p.mkdir(parents=True, exist_ok=True)
    return p


def write_text(filename: str, content: str) -> Path:
    p = output_dir() / filename
    p.write_text(content, encoding="utf-8", errors="replace")
    return p


def write_json(filename: str, data: Any) -> Path:
    p = output_dir() / filename
    p.write_text(
        json.dumps(data, ensure_ascii=False, indent=2),
        encoding="utf-8",
        errors="replace",
    )
    return p
