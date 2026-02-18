"""Async file-load session helpers for ResizeApp."""

from __future__ import annotations

import logging
import queue
import threading
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence

from PIL import Image
from tkinter import messagebox

from karuku_resizer.ui_file_load_helpers import (
    load_paths_worker,
    scan_and_load_drop_items_worker,
    scan_and_load_images_worker,
)
from karuku_resizer.ui_text_presenter import (
    build_loading_progress_status_text,
    build_loading_hint_text,
    build_file_load_error_payload,
    build_format_duration,
)


def begin_file_load_session(
    app: Any,
    mode_label: str,
    root_dir: Optional[Path],
    clear_existing_jobs: bool,
    *,
    max_files: int,
) -> None:
    """Initialize shared state for a file-load operation."""
    if clear_existing_jobs:
        app._reset_loaded_jobs()
    if root_dir is not None:
        app.settings["last_input_dir"] = str(root_dir)

    app._is_loading_files = True
    app._file_load_cancel_event = threading.Event()
    app._file_load_queue = queue.Queue(maxsize=8)
    app._file_load_after_id = None
    app._file_load_total_candidates = 0
    app._file_load_loaded_count = 0
    app._file_load_failed_details = []
    app._file_load_failed_paths = []
    app._file_load_limited = False
    app._file_load_limit = max_files
    app._file_scan_pulse = 0.0
    app._file_scan_started_at = 0.0
    app._file_load_started_at = 0.0
    app._file_load_mode_label = mode_label
    app._file_load_root_dir = root_dir

    app._begin_operation_scope(
        stage_text="探索中",
        cancel_text="読み込み中止",
        cancel_command=app._cancel_file_loading,
        initial_progress=0.05,
    )
    app._refresh_status_indicators()


def start_drop_load_async(
    app: Any,
    files: List[Path],
    dirs: List[Path],
    max_files: int,
    *,
    selectable_input_extensions: Sequence[str],
    recursive_extensions: Sequence[str],
) -> None:
    if not files and not dirs:
        return

    limit_text = str(max_files) if max_files > 0 else "無制限"
    if files and max_files > 0 and len(files) > max_files:
        messagebox.showwarning(
            "読み込み上限",
            f"対象画像は {len(files)} 枚ですが、モード上限 {limit_text} 枚で制限して読み込みます。",
        )
        files = files[:max_files]

    root_dir = dirs[0] if len(dirs) == 1 else None
    begin_file_load_session(
        app,
        mode_label="ドラッグ&ドロップ読込",
        root_dir=root_dir,
        clear_existing_jobs=True,
        max_files=max_files,
    )
    if root_dir is None and files:
        app.settings["last_input_dir"] = str(files[0].parent)
    elif root_dir is not None:
        app.settings["last_input_dir"] = str(root_dir)

    app.status_var.set(
        f"ドラッグ&ドロップ読込開始: フォルダー{len(dirs)}件 / ファイル{len(files)}件 / "
        f"上限 {limit_text}枚 / {build_loading_hint_text(cancel_hint='中止のみ可能')}"
    )
    app._file_load_started_at = time.monotonic()

    if dirs:
        worker = threading.Thread(
            target=scan_and_load_drop_items_worker,
            args=(
                files,
                dirs,
                app._file_load_cancel_event,
                app._file_load_queue,
                max_files,
            ),
            kwargs={
                "selectable_exts": selectable_input_extensions,
                "recursive_exts": recursive_extensions,
                "build_file_load_error_payload": build_file_load_error_payload,
            },
            daemon=True,
            name="karuku-dnd-loader",
        )
    else:
        worker = threading.Thread(
            target=load_paths_worker,
            args=(files, app._file_load_cancel_event, app._file_load_queue),
            kwargs={
                "build_file_load_error_payload": build_file_load_error_payload,
            },
            daemon=True,
            name="karuku-dnd-file-loader",
        )
    worker.start()
    app._file_load_after_id = app.after(40, app._poll_file_load_queue)


def start_recursive_load_async(
    app: Any,
    root_dir: Path,
    max_files: int,
    *,
    recursive_extensions: Sequence[str],
) -> None:
    begin_file_load_session(
        app,
        mode_label="再帰読み込み",
        root_dir=root_dir,
        clear_existing_jobs=True,
        max_files=max_files,
    )
    app.status_var.set(
        f"再帰探索開始: {root_dir} / 上限 {str(max_files) if max_files > 0 else '無制限'}枚 / 読み込み中は他操作を無効化（中止可）"
    )
    app._file_load_started_at = time.monotonic()

    worker = threading.Thread(
        target=scan_and_load_images_worker,
        args=(
            root_dir,
            app._file_load_cancel_event,
            app._file_load_queue,
            max_files,
        ),
        kwargs={
            "recursive_exts": recursive_extensions,
            "build_file_load_error_payload": build_file_load_error_payload,
        },
        daemon=True,
        name="karuku-recursive-loader",
    )
    worker.start()
    app._file_load_after_id = app.after(40, app._poll_file_load_queue)


def start_retry_failed_load_async(
    app: Any,
    paths: List[Path],
) -> None:
    unique_paths = list(dict.fromkeys(paths))
    if not unique_paths:
        return

    begin_file_load_session(
        app,
        mode_label="失敗再試行",
        root_dir=app._file_load_root_dir,
        clear_existing_jobs=False,
        max_files=len(unique_paths),
    )
    app.status_var.set(
        f"失敗再試行開始: 対象 {len(unique_paths)}件 / 読み込み中は他操作を無効化（中止可）"
    )
    app._file_load_started_at = time.monotonic()
    worker = threading.Thread(
        target=load_paths_worker,
        args=(unique_paths, app._file_load_cancel_event, app._file_load_queue),
        kwargs={
            "build_file_load_error_payload": build_file_load_error_payload,
        },
        daemon=True,
        name="karuku-retry-loader",
    )
    worker.start()
    app._file_load_after_id = app.after(40, app._poll_file_load_queue)


def poll_file_load_queue(app: Any) -> None:
    if not app._is_loading_files:
        app._file_load_after_id = None
        return

    handled = 0
    while handled < 30:
        try:
            message = app._file_load_queue.get_nowait()
        except queue.Empty:
            break
        handled += 1
        app._handle_file_load_message(message)
        if not app._is_loading_files:
            break

    if app._is_loading_files:
        app._file_load_after_id = app.after(40, app._poll_file_load_queue)
    else:
        app._file_load_after_id = None


def _format_path_for_display(app: Any, path: Path) -> str:
    if app._file_load_root_dir is not None:
        try:
            return path.relative_to(app._file_load_root_dir).as_posix()
        except ValueError:
            pass
    return str(path)


def handle_file_load_message(app: Any, message: Dict[str, Any]) -> None:
    msg_type = str(message.get("type", ""))
    if msg_type == "scan_progress":
        detected = int(message.get("count", 0))
        app._file_scan_pulse = (app._file_scan_pulse + 0.08) % 1.0
        scan_elapsed = time.monotonic() - app._file_load_started_at
        app.progress_bar.set(max(0.05, app._file_scan_pulse))
        app.status_var.set(
            f"{app._file_load_mode_label}: 探索中 {detected} 件検出 / "
            f"経過{build_format_duration(scan_elapsed)} / "
            f"{build_loading_hint_text(cancel_hint='中止のみ可能')}"
        )
        return

    if msg_type == "scan_done":
        app._file_load_total_candidates = int(message.get("total", 0))
        app._file_load_limited = bool(message.get("reached_limit", False))
        if app._file_load_limit <= 0:
            app._file_load_limit = app._file_load_total_candidates
        app._file_load_started_at = time.monotonic()
        app._set_operation_stage("読込中")
        if app._file_load_total_candidates == 0:
            app.progress_bar.set(1.0)
            app.status_var.set(
                f"{app._file_load_mode_label}: 対象画像（jpg/jpeg/png）は0件でした"
            )
        else:
            app.progress_bar.set(0)
            app.status_var.set(
                f"{app._file_load_mode_label}: 読込開始 0/{app._file_load_total_candidates} / "
                f"{build_loading_hint_text(cancel_hint='中止のみ可能')}"
            )
        return

    if msg_type == "loaded":
        path = Path(str(message.get("path", "")))
        image = message.get("image")
        if isinstance(image, Image.Image):
            append_job = getattr(app, "_append_loaded_job", None)
            if callable(append_job):
                append_job(path, image)
        app._file_load_loaded_count += 1
        total = app._file_load_total_candidates
        failed_count = len(app._file_load_failed_details)
        done_count = app._file_load_loaded_count + failed_count
        if total > 0:
            app.progress_bar.set(min(1.0, done_count / total))
            app.status_var.set(
                build_loading_progress_status_text(
                    total=total,
                    loaded=app._file_load_loaded_count,
                    failed_count=failed_count,
                    done_count=done_count,
                    elapsed_seconds=time.monotonic() - app._file_load_started_at,
                    path_text=_format_path_for_display(app, path),
                    failed=False,
                    loading_hint=build_loading_hint_text(cancel_hint="中止のみ可能"),
                )
            )
        else:
            app.status_var.set(
                f"{app._file_load_mode_label}: 読込中 / 処理: {_format_path_for_display(app, path)} / "
                f"{build_loading_hint_text(cancel_hint='中止のみ可能')}"
            )
        return

    if msg_type == "load_error":
        payload = message if isinstance(message, dict) else {}
        path = Path(str(payload.get("path", "")))
        error_detail = payload.get("error")
        if isinstance(error_detail, dict):
            error_text = str(error_detail.get("error") or "")
        else:
            error_text = str(error_detail or "")

        display_path = _format_path_for_display(app, path)
        app._file_load_failed_details.append(f"{display_path}: {error_text}")
        app._file_load_failed_paths.append(path)
        total = app._file_load_total_candidates
        failed_count = len(app._file_load_failed_details)
        done_count = app._file_load_loaded_count + failed_count
        if total > 0:
            app.progress_bar.set(min(1.0, done_count / total))
            app.status_var.set(
                build_loading_progress_status_text(
                    total=total,
                    loaded=app._file_load_loaded_count,
                    failed_count=failed_count,
                    done_count=done_count,
                    elapsed_seconds=time.monotonic() - app._file_load_started_at,
                    path_text=display_path,
                    failed=True,
                    loading_hint=build_loading_hint_text(cancel_hint="中止のみ可能"),
                )
            )
        return

    if msg_type == "fatal":
        error = str(message.get("error", "不明なエラー"))
        app._file_load_failed_details.append(f"致命的エラー: {error}")
        logging.error("Fatal error in recursive loader: %s", error)
        return

    if msg_type == "done":
        canceled = bool(message.get("canceled", False))
        app._finish_recursive_load(canceled=canceled)
