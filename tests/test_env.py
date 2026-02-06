from __future__ import annotations

import os
from pathlib import Path

from thordata.env import load_env_file


def test_load_env_file_basic(tmp_path: Path, monkeypatch) -> None:
    env_path = tmp_path / ".env"
    env_path.write_text(
        "\n".join(
            [
                "# comment",
                "FOO=bar",
                'QUOTED="hello world"',
                "SINGLE='x'",
                "EMPTY_KEY=",
            ]
        ),
        encoding="utf-8",
    )

    # Ensure clean env
    monkeypatch.delenv("FOO", raising=False)
    monkeypatch.delenv("QUOTED", raising=False)
    monkeypatch.delenv("SINGLE", raising=False)

    load_env_file(env_path)

    assert os.getenv("FOO") == "bar"
    assert os.getenv("QUOTED") == "hello world"
    assert os.getenv("SINGLE") == "x"


def test_load_env_file_no_override(tmp_path: Path, monkeypatch) -> None:
    env_path = tmp_path / ".env"
    env_path.write_text("FOO=from_file\n", encoding="utf-8")

    monkeypatch.setenv("FOO", "from_env")

    load_env_file(env_path, override=False)
    assert os.getenv("FOO") == "from_env"


def test_load_env_file_with_override(tmp_path: Path, monkeypatch) -> None:
    env_path = tmp_path / ".env"
    env_path.write_text("FOO=from_file\n", encoding="utf-8")

    monkeypatch.setenv("FOO", "from_env")

    load_env_file(env_path, override=True)
    assert os.getenv("FOO") == "from_file"
