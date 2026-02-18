"""Helpers for drag-and-drop parsing and background file load workers."""

from __future__ import annotations

import queue
import os
import logging
import threading
from pathlib import Path
from typing import Any, Callable, Dict, List, Sequence

from PIL import Image, ImageOps


def dedupe_paths(paths: List[Path]) -> List[Path]:
    """Deduplicate paths preserving order."""
    seen: set[str] = set()
    deduped: List[Path] = []
    for path in paths:
        marker = str(path).lower()
        if marker in seen:
            continue
        seen.add(marker)
        deduped.append(path)
    return deduped


def is_selectable_input_file(path: Path, *, selectable_exts: Sequence[str]) -> bool:
    """Return True when path has selectable image extension."""
    return path.suffix.lower() in set(selectable_exts)


def normalize_dropped_path_text(value: str) -> str:
    """Normalize one drag-and-drop text item."""
    text = value.strip()
    if not text:
        return ""

    if text.startswith("file://"):
        from urllib.parse import unquote, urlparse

        parsed = urlparse(text)
        if parsed.scheme == "file":
            normalized = unquote(parsed.path or "")
            if parsed.netloc and parsed.netloc.lower() != "localhost":
                normalized = f"//{parsed.netloc}{normalized}"
            if (
                os.name == "nt"
                and len(normalized) >= 3
                and normalized[0] == "/"
                and normalized[2] == ":"
            ):
                normalized = normalized[1:]
            if normalized:
                text = normalized
    return text


def parse_drop_paths(split_texts: Callable[[str], Sequence[str]], raw_data: Any) -> List[Path]:
    """Parse drag-and-drop payload into file path list."""
    data = str(raw_data or "").strip()
    if not data:
        return []

    try:
        raw_items = list(split_texts(data))
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


def scan_and_load_drop_items_worker(
    dropped_files: List[Path],
    dropped_dirs: List[Path],
    cancel_event: threading.Event,
    out_queue: "queue.Queue[Dict[str, Any]]",
    *,
    max_files: int,
    selectable_exts: Sequence[str],
    recursive_exts: Sequence[str],
    build_file_load_error_payload: Callable[[Path, BaseException, int], Dict[str, Any]],
) -> None:
    """Background worker: load dropped file candidates and recursive folders."""
    try:
        candidates: List[Path] = []
        seen: set[str] = set()
        reached_limit = False
        scan_errors: List[str] = []

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
            if path.exists() and path.is_file() and is_selectable_input_file(path, selectable_exts=selectable_exts):
                _add_candidate(path)
                detected += 1
                if detected % 40 == 0:
                    out_queue.put({"type": "scan_progress", "count": detected})
                if max_files > 0 and detected >= max_files:
                    reached_limit = True
                    break

            if reached_limit:
                break

        for root_dir in dropped_dirs:
            if cancel_event.is_set():
                out_queue.put({"type": "done", "canceled": True})
                return
            if reached_limit:
                break

            def _onerror(exc: OSError) -> None:
                source = str(getattr(exc, "filename", str(root_dir)))
                message = f"{Path(source)}: {exc}"
                scan_errors.append(message)

            for dirpath, _dirnames, filenames in os.walk(root_dir, topdown=True, onerror=_onerror):
                if cancel_event.is_set():
                    out_queue.put({"type": "done", "canceled": True})
                    return
                base_dir = Path(dirpath)
                for name in filenames:
                    if cancel_event.is_set():
                        out_queue.put({"type": "done", "canceled": True})
                        return
                    if Path(name).suffix.lower() in set(recursive_exts):
                        _add_candidate(base_dir / name)
                        detected += 1
                        if detected % 40 == 0:
                            out_queue.put({"type": "scan_progress", "count": detected})
                        if max_files > 0 and detected >= max_files:
                            reached_limit = True
                            break
                if reached_limit:
                    break

        if scan_errors:
            for message in scan_errors[:10]:
                logging.warning("Recursive scan (drag&drop) warning: %s", message)

        candidates.sort(key=lambda p: str(p).lower())
        out_queue.put(
            {
                "type": "scan_done",
                "total": len(candidates),
                "reached_limit": reached_limit,
            }
        )

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
                out_queue.put(build_file_load_error_payload(path, exc, index))

        out_queue.put({"type": "done", "canceled": cancel_event.is_set()})
    except Exception as exc:
        out_queue.put({"type": "fatal", "error": str(exc)})
        out_queue.put({"type": "done", "canceled": cancel_event.is_set()})


def scan_and_load_images_worker(
    root_dir: Path,
    cancel_event: threading.Event,
    out_queue: "queue.Queue[Dict[str, Any]]",
    max_files: int,
    *,
    recursive_exts: Sequence[str],
    build_file_load_error_payload: Callable[[Path, BaseException, int], Dict[str, Any]],
) -> None:
    """Background worker: scan directory recursively and load supported images."""
    try:
        candidates: List[Path] = []
        detected = 0
        reached_limit = False
        scan_errors: List[str] = []

        def _onerror(exc: OSError) -> None:
            source = str(getattr(exc, "filename", str(root_dir)))
            message = f"{Path(source)}: {exc}"
            scan_errors.append(message)

        for dirpath, _dirnames, filenames in os.walk(root_dir, topdown=True, onerror=_onerror):
            if cancel_event.is_set():
                out_queue.put({"type": "done", "canceled": True})
                return
            base_dir = Path(dirpath)
            for name in filenames:
                if cancel_event.is_set():
                    out_queue.put({"type": "done", "canceled": True})
                    return
                suffix = Path(name).suffix.lower()
                if suffix in set(recursive_exts):
                    candidates.append(base_dir / name)
                    detected += 1
                    if detected % 40 == 0:
                        out_queue.put({"type": "scan_progress", "count": detected})
                    if max_files > 0 and detected >= max_files:
                        reached_limit = True
                        break
            if reached_limit:
                break

        if scan_errors:
            for message in scan_errors[:10]:
                logging.warning("Recursive scan warning: %s", message)

        candidates.sort(key=lambda p: str(p).lower())
        out_queue.put(
            {
                "type": "scan_done",
                "total": len(candidates),
                "reached_limit": reached_limit,
            }
        )

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
                out_queue.put(build_file_load_error_payload(path, exc, index))

        out_queue.put({"type": "done", "canceled": cancel_event.is_set()})
    except Exception as exc:
        out_queue.put({"type": "fatal", "error": str(exc)})
        out_queue.put({"type": "done", "canceled": cancel_event.is_set()})


def load_paths_worker(
    paths: List[Path],
    cancel_event: threading.Event,
    out_queue: "queue.Queue[Dict[str, Any]]",
    *,
    build_file_load_error_payload: Callable[[Path, BaseException, int], Dict[str, Any]],
) -> None:
    """Background worker: load explicit image paths."""
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
                out_queue.put(build_file_load_error_payload(path, exc, index))

        out_queue.put({"type": "done", "canceled": cancel_event.is_set()})
    except Exception as exc:
        out_queue.put({"type": "fatal", "error": str(exc)})
        out_queue.put({"type": "done", "canceled": cancel_event.is_set()})
