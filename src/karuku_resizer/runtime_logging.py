"""ランタイムログの保存先と保持ポリシーを扱うユーティリティ。"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Mapping, Optional

DEFAULT_RETENTION_DAYS = 30
DEFAULT_MAX_FILES = 100
_RUN_LOG_PREFIX = "run_"
_RUN_LOG_SUFFIX = ".log"
_RUN_SUMMARY_SUFFIX = "_summary.json"


@dataclass(frozen=True)
class RunLogArtifacts:
    run_id: str
    log_dir: Path
    run_log_path: Path
    summary_path: Path


def get_default_log_dir(
    app_name: str = "KarukuResize",
    *,
    os_name: Optional[str] = None,
    env: Optional[Mapping[str, str]] = None,
    home: Optional[Path] = None,
) -> Path:
    """OSごとの標準ログディレクトリを返す。"""
    resolved_os_name = os_name or os.name
    resolved_env = env or os.environ
    resolved_home = home or Path.home()
    app_dir_name = app_name.strip().replace(" ", "")
    app_dir_name_lc = app_dir_name.lower()

    if resolved_os_name == "nt":
        local_app_data = resolved_env.get("LOCALAPPDATA") or resolved_env.get("APPDATA")
        if local_app_data:
            return Path(local_app_data) / app_dir_name / "logs"
        return resolved_home / f".{app_dir_name_lc}" / "logs"

    state_home = resolved_env.get("XDG_STATE_HOME")
    if state_home:
        return Path(state_home) / app_dir_name_lc / "logs"

    return resolved_home / ".local" / "state" / app_dir_name_lc / "logs"


def create_run_log_artifacts(
    app_name: str = "KarukuResize",
    *,
    retention_days: int = DEFAULT_RETENTION_DAYS,
    max_files: int = DEFAULT_MAX_FILES,
    now: Optional[datetime] = None,
) -> RunLogArtifacts:
    """実行ごとのログ/summaryファイルパスを作成して返す。"""
    now_dt = now or datetime.now()
    run_id = now_dt.strftime("%Y%m%d_%H%M%S")
    log_dir = get_default_log_dir(app_name=app_name)
    log_dir.mkdir(parents=True, exist_ok=True)
    prune_run_files(log_dir, retention_days=retention_days, max_files=max_files, now=now_dt)
    return RunLogArtifacts(
        run_id=run_id,
        log_dir=log_dir,
        run_log_path=log_dir / f"{_RUN_LOG_PREFIX}{run_id}{_RUN_LOG_SUFFIX}",
        summary_path=log_dir / f"{_RUN_LOG_PREFIX}{run_id}{_RUN_SUMMARY_SUFFIX}",
    )


def prune_run_files(
    log_dir: Path,
    *,
    retention_days: int = DEFAULT_RETENTION_DAYS,
    max_files: int = DEFAULT_MAX_FILES,
    now: Optional[datetime] = None,
) -> list[Path]:
    """保持日数・保持件数を超える実行ログを削除する。"""
    now_dt = now or datetime.now()
    cutoff = now_dt - timedelta(days=max(0, retention_days))

    removed: list[Path] = []
    run_files = _list_run_files(log_dir)

    for path in run_files:
        try:
            modified_at = datetime.fromtimestamp(path.stat().st_mtime)
        except OSError:
            continue
        if modified_at < cutoff:
            if _safe_unlink(path):
                removed.append(path)

    remaining = _list_run_files(log_dir)
    if max_files > 0 and len(remaining) > max_files:
        extra_count = len(remaining) - max_files
        for path in remaining[:extra_count]:
            if _safe_unlink(path):
                removed.append(path)

    return removed


def write_run_summary(summary_path: Path, payload: dict[str, Any]) -> None:
    """summary JSON をアトミックに保存する。"""
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = summary_path.with_suffix(f"{summary_path.suffix}.tmp")
    with tmp_path.open("w", encoding="utf-8") as fh:
        json.dump(payload, fh, ensure_ascii=False, indent=2)
    tmp_path.replace(summary_path)


def _list_run_files(log_dir: Path) -> list[Path]:
    try:
        files = [path for path in log_dir.iterdir() if _is_run_file(path)]
    except OSError:
        return []
    return sorted(files, key=lambda p: p.stat().st_mtime)


def _is_run_file(path: Path) -> bool:
    if not path.is_file():
        return False

    name = path.name
    if not name.startswith(_RUN_LOG_PREFIX):
        return False

    if name.endswith(_RUN_LOG_SUFFIX):
        run_id = name[len(_RUN_LOG_PREFIX) : -len(_RUN_LOG_SUFFIX)]
        return _is_run_id(run_id)

    if name.endswith(_RUN_SUMMARY_SUFFIX):
        run_id = name[len(_RUN_LOG_PREFIX) : -len(_RUN_SUMMARY_SUFFIX)]
        return _is_run_id(run_id)

    return False


def _is_run_id(value: str) -> bool:
    try:
        datetime.strptime(value, "%Y%m%d_%H%M%S")
    except ValueError:
        return False
    return True


def _safe_unlink(path: Path) -> bool:
    try:
        path.unlink(missing_ok=True)
    except OSError:
        return False
    return True
