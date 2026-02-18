"""Helpers for save/output path and option construction."""

from __future__ import annotations

import hashlib
import os
import re
import tempfile
from pathlib import Path
from typing import Any, Callable, Iterable, Optional, Sequence

from karuku_resizer.image_save_pipeline import ExifEditValues, SaveOptions, SaveFormat


def build_save_options(
    app: Any,
    output_format: SaveFormat,
    *,
    exif_mode: str,
    exif_edit_values: Optional[ExifEditValues] = None,
) -> Optional[SaveOptions]:
    pro_mode = app._is_pro_mode()
    edit_values = exif_edit_values
    if exif_mode == "edit" and edit_values is None:
        edit_values = app._current_exif_edit_values(show_warning=True, strict=True)
        if edit_values is None:
            return None
    return SaveOptions(
        output_format=output_format,
        quality=app._current_quality(),
        dry_run=app.dry_run_var.get(),
        exif_mode=exif_mode,  # type: ignore[arg-type]
        remove_gps=app.remove_gps_var.get(),
        exif_edit=edit_values if exif_mode == "edit" else None,
        verbose=app.verbose_log_var.get() if pro_mode else False,
        webp_method=app._current_webp_method() if pro_mode else 6,
        webp_lossless=app.webp_lossless_var.get() if pro_mode else False,
        avif_speed=app._current_avif_speed() if pro_mode else 6,
    )


def build_batch_save_options(
    app: Any,
    reference_output_format: SaveFormat,
    *,
    exif_mode: str,
) -> Optional[SaveOptions]:
    batch_exif_edit_values = (
        app._current_exif_edit_values(show_warning=True, strict=True) if exif_mode == "edit" else None
    )
    if exif_mode == "edit" and batch_exif_edit_values is None:
        return None
    return build_save_options(
        app,
        reference_output_format,
        exif_mode=exif_mode,
        exif_edit_values=batch_exif_edit_values,
    )


def preflight_output_directory(
    output_path: Path,
    *,
    create_if_missing: bool,
    readable_os_error: Callable[[BaseException, str], str],
) -> Optional[str]:
    try:
        parent = output_path.parent
        if parent is None:
            return "保存先フォルダの取得に失敗しました。"

        if output_path.exists() and output_path.is_dir():
            return (
                f"保存先「{output_path.name}」は既存のフォルダです。"
                "ファイル名を変更してください。"
            )

        if not parent.exists():
            if not create_if_missing:
                return f"保存先フォルダ「{parent}」が存在しません。"
            parent.mkdir(parents=True, exist_ok=True)

        if not parent.is_dir():
            return f"保存先「{parent}」はフォルダではありません。"
        if os.path.exists(parent) and not os.access(parent, os.W_OK):
            return f"保存先フォルダ「{parent}」に書き込み権限がありません。"

        with tempfile.NamedTemporaryFile(prefix=".krkrw_", dir=parent, delete=True) as probe:
            probe.write(b"")
        return None
    except Exception as exc:
        return readable_os_error(exc, "保存先の事前チェックに失敗しました。")


def preflight_output_directory_only(
    directory: Path,
    *,
    create_if_missing: bool,
    readable_os_error: Callable[[BaseException, str], str],
) -> Optional[str]:
    return preflight_output_directory(
        directory / ".__karuku_dir_probe__",
        create_if_missing=create_if_missing,
        readable_os_error=readable_os_error,
    )


def normalize_windows_output_filename(
    output_path: Path,
    *,
    reserved_names: Iterable[str],
) -> tuple[Path, Optional[str]]:
    if os.name != "nt":
        return output_path, None

    filename = output_path.name
    stem = output_path.stem
    suffix = output_path.suffix
    stem_clean = re.sub(r'[\\/:*?"<>|]+', "_", stem).strip(" .")
    if not stem_clean:
        stem_clean = "image"

    if stem_clean.upper() in set(reserved_names):
        stem_clean = f"{stem_clean}_"

    if stem_clean == stem and filename == output_path.name:
        return output_path, None

    normalized = output_path.with_name(f"{stem_clean}{suffix}")
    return normalized, "Windowsのファイル名規則により保存先名を調整しました。"


def is_windows_path_length_risky(output_path: Path) -> bool:
    if os.name != "nt":
        return False
    candidate = str(output_path)
    if candidate.startswith("\\\\?\\"):
        candidate = candidate[4:]
    return len(candidate) > 220


def build_single_save_filetypes(
    available_formats: Sequence[str],
) -> list[tuple[str, str]]:
    filetypes = [("JPEG", "*.jpg *.jpeg"), ("PNG", "*.png")]
    normalized = {str(fmt).strip().lower() for fmt in available_formats}
    if "webp" in normalized:
        filetypes.append(("WEBP", "*.webp"))
    if "avif" in normalized:
        filetypes.append(("AVIF", "*.avif"))
    filetypes.append(("All files", "*.*"))
    return filetypes


def build_unique_batch_base_path(
    output_dir: Path,
    stem: str,
    output_format: SaveFormat,
    *,
    destination_with_extension_func,
    dry_run: bool,
) -> Path:
    safe_stem = re.sub(r'[\\/:*?"<>|]+', "_", str(stem).strip())
    safe_stem = safe_stem.strip(" .")
    if not safe_stem:
        safe_stem = "image"
    if len(safe_stem) > 72:
        digest = hashlib.sha1(safe_stem.encode("utf-8")).hexdigest()[:8]
        safe_stem = f"{safe_stem[:60]}_{digest}"
    base = output_dir / f"{safe_stem}_resized"
    if dry_run:
        return base

    candidate = base
    suffix_index = 1
    while destination_with_extension_func(candidate, output_format).exists():
        candidate = output_dir / f"{stem}_resized_{suffix_index}"
        suffix_index += 1
    return candidate
