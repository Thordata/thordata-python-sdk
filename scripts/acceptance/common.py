from __future__ import annotations

import json
import os
import time
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, TypeVar


def load_dotenv_if_present(*, override: bool = False) -> None:
    """Load .env from repo root (best-effort, no external deps).

    - If override=False (default), existing environment variables win.
    - Supports simple KEY=VALUE lines and ignores comments/blank lines.
    """

    # repo root = thordata-python-sdk
    repo_root = Path(__file__).resolve().parents[2]
    env_path = repo_root / ".env"
    if not env_path.exists():
        return

    try:
        content = env_path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        content = env_path.read_text(encoding="utf-8", errors="ignore")

    for raw in content.splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            continue
        key, val = line.split("=", 1)
        key = key.strip()
        val = val.strip()
        if not key:
            continue

        # remove surrounding quotes
        if (val.startswith('"') and val.endswith('"')) or (
            val.startswith("'") and val.endswith("'")
        ):
            val = val[1:-1]

        if override or key not in os.environ or os.environ.get(key, "") == "":
            os.environ[key] = val


@dataclass(frozen=True)
class AcceptanceConfig:
    timeout: int = 60
    poll_interval: float = 3.0
    max_wait: float = 300.0
    output_dir: Path = Path("artifacts") / "acceptance"


def is_integration_enabled() -> bool:
    load_dotenv_if_present(override=False)
    return os.getenv("THORDATA_INTEGRATION", "").lower() in {"1", "true", "yes"}


def is_strict_enabled() -> bool:
    return os.getenv("THORDATA_INTEGRATION_STRICT", "").lower() in {"1", "true", "yes"}


def ensure_output_dir(group: str) -> Path:
    out = AcceptanceConfig().output_dir / group
    out.mkdir(parents=True, exist_ok=True)
    return out


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def now_ts() -> str:
    return time.strftime("%Y%m%d-%H%M%S")


def first_working_url(urls: Iterable[str]) -> str:
    for u in urls:
        if u and isinstance(u, str):
            return u
    raise ValueError("No candidate urls provided")


def require_env(var_name: str) -> str:
    val = os.getenv(var_name)
    if not val:
        raise RuntimeError(f"Missing env var: {var_name}")
    return val


def print_header(title: str) -> None:
    line = "=" * 80
    print(line)
    print(title)
    print(line)


def exit_with_result(ok: bool) -> None:
    raise SystemExit(0 if ok else 1)


_T = TypeVar("_T")


def safe_call(
    fn: Callable[..., _T], *args: Any, **kwargs: Any
) -> tuple[bool, _T | Exception]:
    try:
        return True, fn(*args, **kwargs)
    except Exception as e:
        return False, e


def safe_call_with_timeout(
    fn: Callable[..., _T],
    *args: Any,
    hard_timeout: float,
    **kwargs: Any,
) -> tuple[bool, _T | Exception]:
    """Run blocking function with a hard timeout (best-effort).

    Uses a worker thread. If hard_timeout triggers, returns TimeoutError.

    Note: the underlying request may still run in background. This helper is for
    acceptance scripts to avoid indefinite hangs.
    """

    import concurrent.futures

    ex = concurrent.futures.ThreadPoolExecutor(max_workers=1)
    try:
        fut = ex.submit(fn, *args, **kwargs)
        try:
            return True, fut.result(timeout=hard_timeout)
        except concurrent.futures.TimeoutError:
            return False, TimeoutError(f"timeout after {hard_timeout}s")
        except Exception as e:
            return False, e
    finally:
        # Do not wait for hung threads. This prevents acceptance scripts from blocking.
        ex.shutdown(wait=False, cancel_futures=True)


def safe_await(coro):
    import asyncio

    async def _run():
        try:
            return True, await coro
        except Exception as e:
            return False, e

    return asyncio.run(_run())
