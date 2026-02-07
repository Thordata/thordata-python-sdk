from __future__ import annotations

import os
from pathlib import Path


def _ensure_writable_tmp_dir(tmp_root: Path) -> None:
    tmp_root.mkdir(parents=True, exist_ok=True)
    # Basic write check (surface early if permissions are broken)
    probe = tmp_root / ".write_test"
    probe.write_text("ok", encoding="utf-8")
    probe.unlink(missing_ok=True)


def pytest_configure(config):
    """Force pytest temp/cache dirs into the repo to avoid Windows permission issues."""
    repo_root = Path(__file__).resolve().parent

    # 1) tmp_path factory base (used by tmp_path fixture)
    tmp_root = repo_root / ".pytest_tmp"
    _ensure_writable_tmp_dir(tmp_root)

    # Only set if not already set by user
    os.environ.setdefault("TMPDIR", str(tmp_root))
    os.environ.setdefault("TEMP", str(tmp_root))
    os.environ.setdefault("TMP", str(tmp_root))

    # 2) pytest cache dir (used by cacheprovider)
    # Pytest reads this from config option 'cache_dir'
    # If user already set it, do not override.
    if not getattr(config.option, "cache_dir", None):
        config.option.cache_dir = str(repo_root / ".pytest_cache")
