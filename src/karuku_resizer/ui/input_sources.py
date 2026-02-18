"""Input source helpers (drag-and-drop and file selection) for ResizeApp."""

from __future__ import annotations

import logging
import os
import queue
import threading
from pathlib import Path
from tkinter import filedialog, messagebox
from typing import Any, Dict, List, Optional, Sequence, Tuple
from urllib.parse import unquote, urlparse

from PIL import Image, ImageOps


def setup_drag_and_drop(
    app: Any,
    *,
    tkdnd_available: bool,
    tkdnd_cls: Any,
    dnd_files: str,
) -> None:
    if not tkdnd_available or tkdnd_cls is None:
        logging.info("Drag and drop disabled: tkinterdnd2 unavailable")
        return

    if not hasattr(app, "drop_target_register"):
        logging.info("Drag and drop disabled: root widget does not support drop_target_register")
        app._drag_drop_enabled = False
        return

    try:
        tkdnd_cls._require(app)
    except Exception as exc:
        logging.warning("Drag and drop initialization failed: %s", exc)
        return

    targets = [
        app,
        app.main_content,
        app.file_list_frame,
        app.canvas_org,
        app.canvas_resz,
    ]
    registered = 0
    for widget in targets:
        try:
            widget.drop_target_register(dnd_files)
            widget.dnd_bind("<<DropEnter>>", app._on_drop_enter)
            widget.dnd_bind("<<DropPosition>>", app._on_drop_position)
            widget.dnd_bind("<<DropLeave>>", app._on_drop_leave)
            widget.dnd_bind("<<Drop>>", app._on_drop_files)
            registered += 1
        except Exception:
            logging.exception("Failed to register drop target: %s", widget)

    app._drag_drop_enabled = registered > 0
    if app._drag_drop_enabled:
        logging.info("Drag and drop enabled on %d widgets", registered)


def dedupe_paths(paths: List[Path]) -> List[Path]:
    seen: set[str] = set()
    deduped: List[Path] = []
    for path in paths:
        marker = str(path).lower()
        if marker in seen:
            continue
        seen.add(marker)
        deduped.append(path)
    return deduped


def is_selectable_input_file(path: Path, *, selectable_input_extensions: Sequence[str]) -> bool:
    return path.suffix.lower() in selectable_input_extensions


def normalize_dropped_path_text(value: str) -> str:
    text = value.strip()
    if not text:
        return ""
    if text.startswith("file://"):
        parsed = urlparse(text)
        if parsed.scheme == "file":
            normalized = unquote(parsed.path or "")
            if parsed.netloc and parsed.netloc.lower() != "localhost":
                normalized = f"//{parsed.netloc}{normalized}"
            if os.name == "nt" and len(normalized) >= 3 and normalized[0] == "/" and normalized[2] == ":":
                normalized = normalized[1:]
            if normalized:
                text = normalized
    return text


def parse_drop_paths(app: Any, raw_data: Any) -> List[Path]:
    data = str(raw_data or "").strip()
    if not data:
        return []
    try:
        raw_items = list(app.tk.splitlist(data))
    except Exception:
        raw_items = [data]

    expanded_items: List[str] = []
    for item in raw_items:
        text = str(item)
        if "\n" in text:
            expanded_items.extend(line for line in text.splitlines() if line.strip())
        else:
            expanded_items.append(text)

    paths: List[Path] = []
    for item in expanded_items:
        text = str(item).strip()
        if text.startswith("{") and text.endswith("}"):
            text = text[1:-1]
        text = text.strip().strip('"')
        text = normalize_dropped_path_text(text)
        if text:
            paths.append(Path(text))
    return dedupe_paths(paths)


def on_drop_enter(copy_token: str, _event: Any) -> str:
    return str(copy_token)


def on_drop_position(copy_token: str, _event: Any) -> str:
    return str(copy_token)


def on_drop_leave(_event: Any) -> None:
    return


def on_drop_files(
    app: Any,
    event: Any,
    *,
    copy_token: str,
    selectable_input_extensions: Sequence[str],
) -> str:
    if app._is_loading_files:
        messagebox.showinfo("処理中", "現在、画像読み込み処理中です。完了またはキャンセル後に再実行してください。")
        return str(copy_token)

    dropped_paths = parse_drop_paths(app, getattr(event, "data", ""))
    if not dropped_paths:
        messagebox.showwarning("ドラッグ&ドロップ", "ドロップされたパスを解釈できませんでした。")
        return str(copy_token)

    handle_dropped_paths(
        app,
        dropped_paths,
        selectable_input_extensions=selectable_input_extensions,
    )
    return str(copy_token)


def handle_dropped_paths(
    app: Any,
    dropped_paths: List[Path],
    *,
    selectable_input_extensions: Sequence[str],
) -> None:
    files: List[Path] = []
    dirs: List[Path] = []
    ignored_count = 0
    for path in dropped_paths:
        try:
            if not path.exists():
                ignored_count += 1
                continue
            if path.is_dir():
                dirs.append(path)
            elif path.is_file() and is_selectable_input_file(path, selectable_input_extensions=selectable_input_extensions):
                files.append(path)
            else:
                ignored_count += 1
        except OSError:
            ignored_count += 1

    files = dedupe_paths(files)
    dirs = dedupe_paths(dirs)
    if not files and not dirs:
        messagebox.showwarning("ドラッグ&ドロップ", "画像ファイルまたはフォルダーが見つかりませんでした。")
        return

    if dirs and not app._is_pro_mode():
        switch_to_pro = messagebox.askyesno(
            "ドラッグ&ドロップ",
            "フォルダーが含まれています。\n"
            "プロモードへ切り替えて再帰読み込みしますか？",
        )
        if switch_to_pro:
            app.ui_mode_var.set("プロ")
            app._apply_ui_mode()
            app._update_settings_summary()
        else:
            dirs = []

    if not files and not dirs:
        messagebox.showwarning("ドラッグ&ドロップ", "フォルダーを扱うにはプロモードに切り替えてください。")
        return

    if dirs:
        app.settings["pro_input_mode"] = "recursive"
    elif app._is_pro_mode():
        app.settings["pro_input_mode"] = "files"

    start_drop_load_async(app, files=files, dirs=dirs)
    if ignored_count > 0:
        app.status_var.set(f"{app.status_var.get()} / 対象外 {ignored_count}件をスキップ")


def start_drop_load_async(app: Any, files: List[Path], dirs: List[Path]) -> None:
    if not files and not dirs:
        return

    root_dir = dirs[0] if len(dirs) == 1 else None
    app._begin_file_load_session(
        mode_label="ドラッグ&ドロップ読込",
        root_dir=root_dir,
        clear_existing_jobs=True,
    )
    if root_dir is None and files:
        app.settings["last_input_dir"] = str(files[0].parent)
    elif root_dir is not None:
        app.settings["last_input_dir"] = str(root_dir)

    app.status_var.set(
        f"ドラッグ&ドロップ読込開始: フォルダー{len(dirs)}件 / ファイル{len(files)}件 / "
        f"{app._loading_hint_text()}"
    )

    if dirs:
        worker = threading.Thread(
            target=app._scan_and_load_drop_items_worker,
            args=(files, dirs, app._file_load_cancel_event, app._file_load_queue),
            daemon=True,
            name="karuku-dnd-loader",
        )
    else:
        worker = threading.Thread(
            target=app._load_paths_worker,
            args=(files, app._file_load_cancel_event, app._file_load_queue),
            daemon=True,
            name="karuku-dnd-file-loader",
        )
    worker.start()
    app._file_load_after_id = app.after(40, app._poll_file_load_queue)


def scan_and_load_drop_items_worker(
    dropped_files: List[Path],
    dropped_dirs: List[Path],
    cancel_event: threading.Event,
    out_queue: "queue.Queue[Dict[str, Any]]",
    *,
    selectable_input_extensions: Sequence[str],
    recursive_extensions: Sequence[str],
) -> None:
    try:
        candidates: List[Path] = []
        seen: set[str] = set()

        def _add_candidate(path: Path) -> None:
            marker = str(path).lower()
            if marker in seen:
                return
            seen.add(marker)
            candidates.append(path)

        detected = 0
        for path in dropped_files:
            if cancel_event.is_set():
                out_queue.put({"type": "done", "canceled": True})
                return
            if path.exists() and path.is_file() and path.suffix.lower() in selectable_input_extensions:
                _add_candidate(path)
                detected += 1
                if detected % 40 == 0:
                    out_queue.put({"type": "scan_progress", "count": detected})

        for root_dir in dropped_dirs:
            if cancel_event.is_set():
                out_queue.put({"type": "done", "canceled": True})
                return
            for dirpath, _dirnames, filenames in os.walk(root_dir, topdown=True):
                if cancel_event.is_set():
                    out_queue.put({"type": "done", "canceled": True})
                    return
                base_dir = Path(dirpath)
                for name in filenames:
                    if cancel_event.is_set():
                        out_queue.put({"type": "done", "canceled": True})
                        return
                    if Path(name).suffix.lower() in recursive_extensions:
                        _add_candidate(base_dir / name)
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


def select_files(app: Any) -> None:
    if app._is_loading_files:
        messagebox.showinfo("処理中", "現在、画像読み込み処理中です。完了またはキャンセル後に再実行してください。")
        return

    initial_dir = app.settings.get("last_input_dir", "")
    if app._is_pro_mode():
        paths, remembered_dir, started_async = select_files_in_pro_mode(app, initial_dir)
        if started_async:
            return
    else:
        paths, remembered_dir = select_files_in_simple_mode(initial_dir)
    if not paths:
        return

    if remembered_dir is not None:
        app.settings["last_input_dir"] = str(remembered_dir)

    app._load_selected_paths(paths)
    app._populate_listbox()


def select_files_in_simple_mode(initial_dir: str) -> Tuple[List[Path], Optional[Path]]:
    selected = filedialog.askopenfilenames(
        title="画像を選択",
        initialdir=initial_dir,
        filetypes=[("画像", "*.png *.jpg *.jpeg *.webp *.avif"), ("すべて", "*.*")],
    )
    if not selected:
        return [], None
    paths = [Path(p) for p in selected]
    return paths, paths[0].parent


def select_files_in_pro_mode(app: Any, initial_dir: str) -> Tuple[List[Path], Optional[Path], bool]:
    saved_mode = normalized_pro_input_mode(str(app.settings.get("pro_input_mode", "recursive")))
    default_mode_text = "フォルダー再帰" if saved_mode == "recursive" else "ファイル個別"
    choice = messagebox.askyesnocancel(
        "画像選択（プロ）",
        "はい: フォルダーを再帰読み込み\n"
        "いいえ: ファイルを個別選択\n"
        f"キャンセル: 中止\n\n既定: {default_mode_text}",
        default="yes" if saved_mode == "recursive" else "no",
    )
    if choice is None:
        return [], None, False
    if choice is False:
        app.settings["pro_input_mode"] = "files"
        paths, remembered_dir = select_files_in_simple_mode(initial_dir)
        return paths, remembered_dir, False

    app.settings["pro_input_mode"] = "recursive"
    root_dir_str = filedialog.askdirectory(
        title="対象フォルダーを選択（再帰）",
        initialdir=initial_dir,
    )
    if not root_dir_str:
        return [], None, False

    root_dir = Path(root_dir_str)
    app._start_recursive_load_async(root_dir)
    return [], root_dir, True


def normalized_pro_input_mode(value: str) -> str:
    normalized = value.strip().lower()
    if normalized in {"recursive", "files"}:
        return normalized
    return "recursive"
