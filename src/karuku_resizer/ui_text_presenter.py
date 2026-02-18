"""Pure text builders for GUI status/guide labels."""

from __future__ import annotations


def build_top_action_guide_text(*, is_loading_files: bool, is_processing: bool) -> str:
    """Build top action guide text."""
    if is_loading_files:
        return "画像読み込み中…"
    if is_processing:
        return "処理中 — キャンセル以外の操作はできません"
    return ""


def build_empty_state_text(*, is_pro_mode: bool, processing_hint: str = "処理中: オプションは実行不可") -> str:
    """Build the initial empty-state hint text."""
    lines = [
        "1. 画像を選択",
        "2. サイズを指定",
        "3. プレビュー後に保存",
    ]
    if is_pro_mode:
        lines.append("Pro: フォルダー再帰読込")
    lines.append(f"処理中: {processing_hint}")
    return "\n".join(lines)


def build_settings_summary_text(
    *,
    output_format: str,
    quality: str,
    exif_mode_label: str,
    remove_gps: bool,
    dry_run: bool,
    is_pro_mode: bool,
    format_id: str,
    webp_method: str,
    webp_lossless: bool,
    avif_speed: str,
) -> str:
    """Build summary label text shown in settings header."""
    exif_label = "保持（位置情報除去）" if remove_gps and exif_mode_label == "保持" else exif_mode_label
    parts = [output_format, f"Q{quality}", f"EXIF{exif_label}"]

    if is_pro_mode:
        parts.insert(0, "Pro")

    if dry_run:
        parts.append("ドライラン:ON")

    if is_pro_mode and format_id == "webp":
        parts.append(f"WEBP method {webp_method}")
        if webp_lossless:
            parts.append("lossless")
    elif is_pro_mode and format_id == "avif":
        parts.append(f"AVIF speed {avif_speed}")

    return "現在: " + " / ".join(parts)


def build_session_status_text(
    *,
    is_pro_mode: bool,
    dry_run: bool,
    total_jobs: int,
    failed_jobs: int,
    unprocessed_jobs: int,
    visible_jobs: int,
    file_filter_label: str,
    output_dir: str,
) -> str:
    """Build status line shown on session row."""
    mode = "Pro ON" if is_pro_mode else "Pro OFF"
    dry_run_text = "ON" if dry_run else "OFF"
    return (
        f"セッション: モード {mode} / 表示 {visible_jobs}/{total_jobs} ({file_filter_label}) / "
        f"未処理 {unprocessed_jobs} / 失敗 {failed_jobs} / ドライラン {dry_run_text} / 保存先 {output_dir}"
    )


def build_action_hint_text(*, is_loading_files: bool, is_processing: bool, has_jobs: bool, has_current_selection: bool) -> str:
    """Build footer action hint text."""
    if is_loading_files:
        return "読み込み中です。完了または中止後に操作できます。"
    if is_processing:
        return "処理中です。キャンセル以外の操作はできません。"
    if not has_jobs:
        return "画像が未選択です。まず画像を読み込んでください。"
    if not has_current_selection:
        return "左の一覧から対象画像を選択してください。"
    return "準備完了です。プレビュー・保存を実行できます。"
