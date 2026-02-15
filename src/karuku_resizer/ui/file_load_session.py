"""Async file-load session helpers for ResizeApp."""

from __future__ import annotations

import logging
import os
import queue
import threading
import time
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Sequence

from PIL import Image, ImageOps


def start_recursive_load_async(app: Any, root_dir: Path) -> None:
    begin_file_load_session(app, mode_label="再帰読み込み", root_dir=root_dir, clear_existing_jobs=True)
    app._is_loading_files = True
    app.status_var.set(f"再帰探索開始: {root_dir} / 読み込み中は他操作を無効化（中止可）")

    worker = threading.Thread(
        target=app._scan_and_load_images_worker,
        args=(root_dir, app._file_load_cancel_event, app._file_load_queue),
        daemon=True,
        name="karuku-recursive-loader",
    )
    worker.start()
    app._file_load_after_id = app.after(40, app._poll_file_load_queue)


def start_retry_failed_load_async(app: Any, paths: List[Path]) -> None:
    unique_paths = list(dict.fromkeys(paths))
    if not unique_paths:
        return

    begin_file_load_session(
        app,
        mode_label="失敗再試行",
        root_dir=app._file_load_root_dir,
        clear_existing_jobs=False,
    )
    app.status_var.set(f"失敗再試行開始: 対象 {len(unique_paths)}件 / 読み込み中は他操作を無効化（中止可）")
    worker = threading.Thread(
        target=app._load_paths_worker,
        args=(unique_paths, app._file_load_cancel_event, app._file_load_queue),
        daemon=True,
        name="karuku-retry-loader",
    )
    worker.start()
    app._file_load_after_id = app.after(40, app._poll_file_load_queue)


def begin_file_load_session(
    app: Any,
    mode_label: str,
    root_dir: Optional[Path],
    clear_existing_jobs: bool,
) -> None:
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
    app._file_scan_pulse = 0.0
    app._file_scan_started_at = time.monotonic()
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


def scan_and_load_images_worker(
    root_dir: Path,
    cancel_event: threading.Event,
    out_queue: "queue.Queue[Dict[str, Any]]",
    *,
    recursive_extensions: Sequence[str],
) -> None:
    try:
        candidates: List[Path] = []
        detected = 0
        for dirpath, _dirnames, filenames in os.walk(root_dir, topdown=True):
            if cancel_event.is_set():
                out_queue.put({"type": "done", "canceled": True})
                return
            base_dir = Path(dirpath)
            for name in filenames:
                if cancel_event.is_set():
                    out_queue.put({"type": "done", "canceled": True})
                    return
                suffix = Path(name).suffix.lower()
                if suffix in recursive_extensions:
                    candidates.append(base_dir / name)
                    detected += 1
                    if detected % 40 == 0:
                        out_queue.put({"type": "scan_progress", "count": detected})

        candidates.sort(key=lambda p: str(p).lower())
        out_queue.put({"type": "scan_done", "total": len(candidates)})

        for index, path in enumerate(candidates, start=1):
            if cancel_event.is_set():
                out_queue.put({"type": "done", "canceled": True})
                return
            try:
                with Image.open(path) as opened:
                    opened.load()
                    img = ImageOps.exif_transpose(opened)
                out_queue.put({"type": "loaded", "path": path, "image": img, "index": index})
            except Exception as exc:
                out_queue.put({"type": "load_error", "path": path, "error": str(exc), "index": index})

        out_queue.put({"type": "done", "canceled": cancel_event.is_set()})
    except Exception as exc:
        out_queue.put({"type": "fatal", "error": str(exc)})
        out_queue.put({"type": "done", "canceled": cancel_event.is_set()})


def load_paths_worker(
    paths: List[Path],
    cancel_event: threading.Event,
    out_queue: "queue.Queue[Dict[str, Any]]",
) -> None:
    try:
        out_queue.put({"type": "scan_done", "total": len(paths)})
        for index, path in enumerate(paths, start=1):
            if cancel_event.is_set():
                out_queue.put({"type": "done", "canceled": True})
                return
            try:
                with Image.open(path) as opened:
                    opened.load()
                    img = ImageOps.exif_transpose(opened)
                out_queue.put({"type": "loaded", "path": path, "image": img, "index": index})
            except Exception as exc:
                out_queue.put({"type": "load_error", "path": path, "error": str(exc), "index": index})

        out_queue.put({"type": "done", "canceled": cancel_event.is_set()})
    except Exception as exc:
        out_queue.put({"type": "fatal", "error": str(exc)})
        out_queue.put({"type": "done", "canceled": cancel_event.is_set()})


def format_duration(seconds: float) -> str:
    whole = max(0, int(seconds))
    if whole < 60:
        return f"{whole}秒"
    minutes, sec = divmod(whole, 60)
    if minutes < 60:
        return f"{minutes}分{sec:02d}秒"
    hours, minutes = divmod(minutes, 60)
    return f"{hours}時間{minutes:02d}分"


def format_path_for_display(app: Any, path: Path) -> str:
    if app._file_load_root_dir is not None:
        try:
            return path.relative_to(app._file_load_root_dir).as_posix()
        except ValueError:
            pass
    return str(path)


def loading_hint_text(*, operation_only_cancel_hint: str) -> str:
    return f"読み込み中は他操作を無効化（{operation_only_cancel_hint}）"


def loading_progress_status_text(
    app: Any,
    *,
    operation_only_cancel_hint: str,
    latest_path: Optional[Path] = None,
    failed: bool = False,
) -> str:
    total = app._file_load_total_candidates
    loaded = app._file_load_loaded_count
    failed_count = len(app._file_load_failed_details)
    done_count = loaded + failed_count
    path_text = ""
    if latest_path is not None:
        path_text = format_path_for_display(app, latest_path)

    remaining_text = "算出中"
    speed_text = "速度算出中"
    if app._file_load_started_at > 0 and total > 0 and done_count > 0:
        elapsed = max(0.001, time.monotonic() - app._file_load_started_at)
        speed = done_count / elapsed
        if speed > 0:
            remaining_sec = max(0.0, (total - done_count) / speed)
            remaining_text = format_duration(remaining_sec)
            speed_text = f"{speed:.1f}件/秒"

    prefix = f"{app._file_load_mode_label}: 読込中 {done_count}/{total} (成功{loaded} 失敗{failed_count})"
    if path_text:
        action = "失敗" if failed else "処理"
        prefix += f" / {action}: {path_text}"
    return f"{prefix} / 残り約{remaining_text} / {speed_text} / {loading_hint_text(operation_only_cancel_hint=operation_only_cancel_hint)}"


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


def handle_file_load_message(
    app: Any,
    message: Dict[str, Any],
    *,
    operation_only_cancel_hint: str,
    image_job_cls: Any,
) -> None:
    msg_type = str(message.get("type", ""))
    if msg_type == "scan_progress":
        detected = int(message.get("count", 0))
        app._file_scan_pulse = (app._file_scan_pulse + 0.08) % 1.0
        app.progress_bar.set(max(0.05, app._file_scan_pulse))
        elapsed_text = format_duration(time.monotonic() - app._file_scan_started_at)
        app.status_var.set(
            f"{app._file_load_mode_label}: 探索中 {detected} 件検出 / 経過{elapsed_text} / "
            f"{loading_hint_text(operation_only_cancel_hint=operation_only_cancel_hint)}"
        )
        return

    if msg_type == "scan_done":
        app._file_load_total_candidates = int(message.get("total", 0))
        app._file_load_started_at = time.monotonic()
        app._set_operation_stage("読込中")
        if app._file_load_total_candidates == 0:
            app.progress_bar.set(1.0)
            app.status_var.set(f"{app._file_load_mode_label}: 対象画像（jpg/jpeg/png）は0件でした")
        else:
            app.progress_bar.set(0)
            app.status_var.set(
                f"{app._file_load_mode_label}: 読込開始 0/{app._file_load_total_candidates} / "
                f"{loading_hint_text(operation_only_cancel_hint=operation_only_cancel_hint)}"
            )
        return

    if msg_type == "loaded":
        path = Path(str(message.get("path", "")))
        image = message.get("image")
        if isinstance(image, Image.Image):
            app.jobs.append(image_job_cls(path, image))
        app._file_load_loaded_count += 1
        total = app._file_load_total_candidates
        done_count = app._file_load_loaded_count + len(app._file_load_failed_details)
        if total > 0:
            app.progress_bar.set(min(1.0, done_count / total))
            app.status_var.set(
                loading_progress_status_text(
                    app,
                    operation_only_cancel_hint=operation_only_cancel_hint,
                    latest_path=path,
                    failed=False,
                )
            )
        else:
            app.status_var.set(
                f"{app._file_load_mode_label}: 読込中 / 処理: {format_path_for_display(app, path)} / "
                f"{loading_hint_text(operation_only_cancel_hint=operation_only_cancel_hint)}"
            )
        return

    if msg_type == "load_error":
        path = Path(str(message.get("path", "")))
        error = str(message.get("error", "読み込み失敗"))
        display_path = format_path_for_display(app, path)
        app._file_load_failed_details.append(f"{display_path}: {error}")
        app._file_load_failed_paths.append(path)
        total = app._file_load_total_candidates
        done_count = app._file_load_loaded_count + len(app._file_load_failed_details)
        if total > 0:
            app.progress_bar.set(min(1.0, done_count / total))
            app.status_var.set(
                loading_progress_status_text(
                    app,
                    operation_only_cancel_hint=operation_only_cancel_hint,
                    latest_path=path,
                    failed=True,
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


def finish_recursive_load(app: Any, canceled: bool) -> None:
    retry_paths = list(app._file_load_failed_paths)
    app._is_loading_files = False
    if app._file_load_after_id is not None:
        try:
            app.after_cancel(app._file_load_after_id)
        except Exception:
            pass
        app._file_load_after_id = None

    app._end_operation_scope()

    if app.jobs:
        app._populate_listbox()
    else:
        app._clear_preview_panels()

    total = app._file_load_total_candidates
    loaded = app._file_load_loaded_count
    failed = len(app._file_load_failed_details)
    if canceled:
        msg = f"{app._file_load_mode_label}を中止しました。成功: {loaded}件 / 失敗: {failed}件 / 対象: {total}件"
    else:
        msg = f"{app._file_load_mode_label}完了。成功: {loaded}件 / 失敗: {failed}件 / 対象: {total}件"
    app.status_var.set(msg)

    retry_callback: Optional[Callable[[], None]] = None
    if (not canceled) and retry_paths:

        def _retry_failed_only() -> None:
            app._start_retry_failed_load_async(retry_paths)

        retry_callback = _retry_failed_only

    app._show_operation_result_dialog(
        title="読込結果",
        summary_text=msg,
        failed_details=app._file_load_failed_details,
        retry_callback=retry_callback,
    )
    app._refresh_status_indicators()


def cancel_file_loading(app: Any) -> None:
    if not app._is_loading_files:
        return
    app._file_load_cancel_event.set()
    app._set_operation_stage("キャンセル中")
    app.status_var.set(f"{app._file_load_mode_label}: キャンセル中...")
    app._refresh_status_indicators()
