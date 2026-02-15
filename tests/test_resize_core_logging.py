from __future__ import annotations

from pathlib import Path

from karuku_resizer import resize_core


def test_resolve_cli_log_dir_prefers_env(monkeypatch, tmp_path):
    expected = tmp_path / "my-logs"
    monkeypatch.setenv("KARUKU_LOG_DIR", str(expected))

    assert resize_core._resolve_cli_log_dir() == expected


def test_resolve_cli_log_dir_defaults_to_repo_src_logs(monkeypatch):
    monkeypatch.delenv("KARUKU_LOG_DIR", raising=False)

    result = resize_core._resolve_cli_log_dir()
    expected = Path(__file__).resolve().parents[1] / "src" / "logs"
    assert result == expected


def test_resolve_cli_log_path_relative_is_under_log_dir(monkeypatch, tmp_path):
    base = tmp_path / "custom-logs"
    monkeypatch.setenv("KARUKU_LOG_DIR", str(base))

    result = resize_core._resolve_cli_log_path("process.log")
    assert result == base / "process.log"


def test_resolve_cli_log_path_absolute_is_preserved(monkeypatch, tmp_path):
    monkeypatch.delenv("KARUKU_LOG_DIR", raising=False)
    absolute_path = tmp_path / "direct.log"

    result = resize_core._resolve_cli_log_path(absolute_path)
    assert result == absolute_path

