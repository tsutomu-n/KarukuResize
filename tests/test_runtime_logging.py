from __future__ import annotations

import os
from datetime import datetime, timedelta
from pathlib import Path

from karuku_resizer import runtime_logging


def _write_file_with_mtime(path: Path, mtime: datetime) -> None:
    path.write_text("x", encoding="utf-8")
    ts = mtime.timestamp()
    os.utime(path, (ts, ts))


def test_get_default_log_dir_windows_uses_localappdata(tmp_path: Path) -> None:
    env = {"LOCALAPPDATA": str(tmp_path / "LocalAppData")}
    result = runtime_logging.get_default_log_dir(
        app_name="KarukuResize",
        os_name="nt",
        env=env,
        home=tmp_path / "home",
    )
    assert result == Path(env["LOCALAPPDATA"]) / "KarukuResize" / "logs"


def test_get_default_log_dir_unix_uses_xdg_state_home(tmp_path: Path) -> None:
    env = {"XDG_STATE_HOME": str(tmp_path / "state")}
    result = runtime_logging.get_default_log_dir(
        app_name="KarukuResize",
        os_name="posix",
        env=env,
        home=tmp_path / "home",
    )
    assert result == Path(env["XDG_STATE_HOME"]) / "karukuresize" / "logs"


def test_prune_run_files_removes_expired_files(tmp_path: Path) -> None:
    now = datetime(2026, 2, 12, 12, 0, 0)
    old = now - timedelta(days=45)
    new = now - timedelta(days=3)

    old_log = tmp_path / "run_20251220_120000.log"
    old_summary = tmp_path / "run_20251220_120000_summary.json"
    new_log = tmp_path / "run_20260209_120000.log"
    new_summary = tmp_path / "run_20260209_120000_summary.json"
    ignore_file = tmp_path / "misc.log"

    _write_file_with_mtime(old_log, old)
    _write_file_with_mtime(old_summary, old)
    _write_file_with_mtime(new_log, new)
    _write_file_with_mtime(new_summary, new)
    ignore_file.write_text("keep", encoding="utf-8")

    removed = runtime_logging.prune_run_files(
        tmp_path,
        retention_days=30,
        max_files=100,
        now=now,
    )

    removed_set = {p.name for p in removed}
    assert removed_set == {"run_20251220_120000.log", "run_20251220_120000_summary.json"}
    assert not old_log.exists()
    assert not old_summary.exists()
    assert new_log.exists()
    assert new_summary.exists()
    assert ignore_file.exists()


def test_prune_run_files_respects_max_files(tmp_path: Path) -> None:
    now = datetime(2026, 2, 12, 12, 0, 0)

    # mtimeが古い順に並ぶよう作成
    for idx in range(1, 6):
        run_id = f"2026020{idx}_120000"
        file_path = tmp_path / f"run_{run_id}.log"
        _write_file_with_mtime(file_path, now - timedelta(days=idx))

    runtime_logging.prune_run_files(
        tmp_path,
        retention_days=365,
        max_files=3,
        now=now,
    )

    remaining = sorted(p.name for p in tmp_path.glob("run_*.log"))
    assert len(remaining) == 3
    assert remaining == [
        "run_20260201_120000.log",
        "run_20260202_120000.log",
        "run_20260203_120000.log",
    ]


def test_create_run_log_artifacts_builds_paths(tmp_path: Path, monkeypatch) -> None:
    fixed_now = datetime(2026, 2, 12, 9, 30, 45)
    monkeypatch.setattr(runtime_logging, "get_default_log_dir", lambda app_name="KarukuResize": tmp_path)

    artifacts = runtime_logging.create_run_log_artifacts(
        app_name="KarukuResize",
        retention_days=30,
        max_files=100,
        now=fixed_now,
    )

    assert artifacts.run_id == "20260212_093045"
    assert artifacts.run_log_path == tmp_path / "run_20260212_093045.log"
    assert artifacts.summary_path == tmp_path / "run_20260212_093045_summary.json"
