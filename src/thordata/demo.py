"""
Unified demo entrypoint for the Thordata Python SDK.

This module runs the example scripts from the repository's `examples/` directory
using `runpy`, so it does not require `examples/` to be an importable package.

Usage:
    python -m thordata.demo serp
    python -m thordata.demo universal
    python -m thordata.demo scraper
    python -m thordata.demo concurrency

Notes:
- This entrypoint is primarily intended for repository usage (dev/demo).
- When installed from PyPI, the `examples/` directory is typically not included.
"""

from __future__ import annotations

import os
import runpy
import sys
from pathlib import Path
from typing import Callable, Dict


def _configure_stdio() -> None:
    # Avoid UnicodeEncodeError on Windows consoles with legacy encodings.
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")


def _load_env() -> None:
    # Optional .env support for local development
    try:
        from dotenv import load_dotenv
    except ImportError:
        return
    load_dotenv()


def _repo_root() -> Path:
    """
    Resolve repository root based on src layout:
    <repo>/src/thordata/demo.py -> parents[2] == <repo>
    """
    return Path(__file__).resolve().parents[2]


def _examples_dir() -> Path:
    return _repo_root() / "examples"


def _demo_map() -> Dict[str, Path]:
    ex = _examples_dir()
    return {
        "serp": ex / "demo_serp_api.py",
        "universal": ex / "demo_universal.py",
        "scraper": ex / "demo_web_scraper_api.py",
        "concurrency": ex / "async_high_concurrency.py",
    }


def _usage() -> str:
    names = ", ".join(sorted(_demo_map().keys()))
    return f"Usage: python -m thordata.demo [{names}]"


def _run_demo(path: Path) -> int:
    if not path.exists():
        print(f"Error: demo script not found: {path}")
        return 2

    # Ensure examples dir is on sys.path (helpful if demo imports local helpers).
    examples_dir = str(path.parent.resolve())
    if examples_dir not in sys.path:
        sys.path.insert(0, examples_dir)

    try:
        # Load without triggering `if __name__ == "__main__": ...`
        ns = runpy.run_path(str(path), run_name="__thordata_demo__")

        main_func = ns.get("main")
        if callable(main_func):
            return int(main_func())  # type: ignore[arg-type]

        # Fallback: run as __main__ for scripts without main()
        runpy.run_path(str(path), run_name="__main__")
        return 0

    except KeyboardInterrupt:
        raise
    except SystemExit as e:
        # In case fallback run as __main__ triggered SystemExit
        code = e.code
        if code is None:
            return 0
        if isinstance(code, int):
            return code
        return 1
    except Exception as e:
        import traceback

        print()
        print("-" * 60)
        print("[thordata.demo] The demo script raised an exception.")
        print(f"[thordata.demo] Script: {path.name}")
        print(f"[thordata.demo] Error:  {type(e).__name__}: {e}")
        print()
        print("Note: This is a failure within the demo script itself,")
        print("      not an issue with the thordata.demo entrypoint.")
        print("-" * 60)
        traceback.print_exc()
        return 1


def main() -> int:
    _configure_stdio()
    _load_env()

    if len(sys.argv) < 2:
        print(_usage())
        return 2

    name = sys.argv[1].strip().lower()
    mapping = _demo_map()

    path = mapping.get(name)
    if path is None:
        print(f"Unknown demo: {name}")
        print(_usage())
        return 2

    return _run_demo(path)


if __name__ == "__main__":
    raise SystemExit(main())
