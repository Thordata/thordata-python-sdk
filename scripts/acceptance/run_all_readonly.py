#!/usr/bin/env python
"""Run all acceptance groups in READ-ONLY mode.

Design goals:
- Each group runs in its own Python process.
- One group failing does NOT stop the rest.
- Final exit code is non-zero if any group fails.

Usage:
  THORDATA_INTEGRATION=true python scripts/acceptance/run_all_readonly.py

Notes:
- This runner will propagate current environment variables to sub-scripts.
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

from .common import print_header


def _run(script: Path) -> tuple[bool, int]:
    cmd = [sys.executable, str(script)]
    # Ensure env vars like THORDATA_INTEGRATION propagate
    env = dict(os.environ)
    p = subprocess.run(cmd, env=env)
    return p.returncode == 0, p.returncode


def main() -> int:
    print_header("THORDATA SDK ACCEPTANCE - RUN ALL (READ-ONLY)")

    here = Path(__file__).resolve().parent
    scripts = [
        here / "run_account_readonly.py",
        here / "run_locations.py",
        here / "run_whitelist_readonly.py",
        here / "run_proxy_users_readonly.py",
        here / "run_serp.py",
        here / "run_universal.py",
        here / "run_proxy_connectivity.py",
        here / "run_web_scraper_text_tasks.py",
        here / "run_web_scraper_video_tasks.py",
    ]

    any_fail = False
    for s in scripts:
        if not s.exists():
            print(f"[SKIP] Missing script: {s.name}")
            continue
        print(f"\n>>> Running: {s.name}")
        ok, code = _run(s)
        if ok:
            print(f"<<< OK: {s.name}")
        else:
            print(f"<<< FAIL({code}): {s.name}")
            any_fail = True

    return 1 if any_fail else 0


if __name__ == "__main__":
    raise SystemExit(main())
