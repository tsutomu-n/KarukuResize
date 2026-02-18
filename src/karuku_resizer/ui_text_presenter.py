"""Pure text builders for GUI status/guide labels."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Optional


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


def build_trim_preview_text(value: Optional[str], max_len: int = 40) -> str:
    if value is None:
        return ""
    text = value.strip()
    if len(text) <= max_len:
        return text
    return f"{text[: max_len - 3]}..."


def build_exif_preview_message(
    *,
    job_name: str,
    exif_mode_label: str,
    source_tag_count: int,
    source_has_gps: bool,
    exif_will_be_attached: bool,
    exif_mode: str,
    gps_removed: bool,
    edited_fields: list[str],
    edit_values: Optional[Dict[str, str]],
    skipped_reason: Optional[str],
    has_multiple_jobs: bool,
) -> str:
    """Build preview text for EXIF differences."""
    lines = [
        f"対象: {job_name}",
        f"モード: {exif_mode_label}",
        f"元EXIFタグ数: {source_tag_count}",
        f"元GPS情報: {'あり' if source_has_gps else 'なし'}",
    ]

    if exif_mode == "remove":
        lines.append("保存時: EXIFを付与しません（全削除）")
    elif exif_will_be_attached:
        lines.append("保存時: EXIFを付与します")
    else:
        lines.append("保存時: EXIFは付与されません")

    if exif_mode != "remove":
        lines.append(f"GPS: {'削除予定' if gps_removed else '保持予定'}")

    if edited_fields:
        lines.append("編集予定項目:")
        label_map = {
            "Artist": "撮影者",
            "Copyright": "著作権",
            "DateTimeOriginal": "撮影日時",
            "UserComment": "コメント",
        }
        for key in edited_fields:
            value = build_trim_preview_text((edit_values or {}).get(key))
            lines.append(f"- {label_map.get(key, key)}: {value}")
    elif exif_mode == "edit":
        lines.append("編集予定項目: なし（入力値が空）")

    if skipped_reason:
        lines.append(f"備考: {skipped_reason}")
    if has_multiple_jobs:
        lines.append("注記: 一括保存時は画像ごとに元EXIFが異なるため結果が変わる可能性があります。")

    return "\n".join(lines)


def build_save_failure_hint(result: Any) -> str:
    if result.error_guidance:
        return f"対処: {result.error_guidance}"
    if result.error_category == "sharing_violation":
        return "対処: 他のアプリや同期機能で開かれた状態の可能性があります。閉じてから再試行してください。"
    if result.error_category == "path_too_long":
        return "対処: 保存先のパス文字数を短くしてください。"
    if result.error_category == "permission_denied":
        return "対処: 保存先ファイル/フォルダの権限を確認してください。"
    if result.error_category == "no_space":
        return "対処: 空き容量不足が疑われます。保存先を変更してください。"
    return "対処: 保存先を変更して再試行してください。"


def build_exif_status_text(result: Any) -> str:
    if result.exif_mode == "remove":
        exif_text = "EXIF: 削除"
    elif result.exif_fallback_without_metadata:
        exif_text = "EXIF: 付与不可（フォールバック保存）"
    elif result.exif_attached:
        exif_text = "EXIF: 付与"
    elif result.exif_requested and result.exif_skipped_reason:
        exif_text = f"EXIF: 未付与（{result.exif_skipped_reason}）"
    elif result.had_source_exif:
        exif_text = "EXIF: なし"
    else:
        exif_text = "EXIF: 元データなし"

    gps_text = " / GPS削除" if result.gps_removed else ""
    edit_text = f" / 編集:{len(result.edited_fields)}項目" if result.edited_fields else ""
    return f"{exif_text}{gps_text}{edit_text}"


def build_readable_os_error(error: BaseException, default_message: str = "読み込みに失敗しました") -> str:
    from karuku_resizer.resize_core import analyze_os_error

    if isinstance(error, OSError):
        analyzed = analyze_os_error(error)
        return analyzed if analyzed else default_message
    if isinstance(error, Exception):
        return str(error)
    return default_message


def build_load_error_detail(path: Path, error: BaseException, *, default_message: str = "読み込みに失敗しました") -> str:
    detail = build_readable_os_error(error, default_message=default_message)
    if not detail:
        detail = "読み込みに失敗しました"

    source_path = str(path)
    error_path = getattr(error, "filename", None) or getattr(error, "filename2", None)
    if error_path:
        source_path = str(error_path)

    if source_path:
        detail = f"{source_path}: {detail}"

    if isinstance(error, OSError):
        win_error = getattr(error, "winerror", None)
        errno = getattr(error, "errno", None)
        if isinstance(win_error, int) and win_error == 32:
            return f"{detail}（ファイル使用中の可能性）"
        if isinstance(win_error, int) and win_error == 206:
            return f"{detail}（パス長エラー）"
        if win_error in {3, 2} or errno == 2:
            return f"{detail}（ファイルが存在しない）"
        if win_error in {5} or errno in {5, 13}:
            return f"{detail}（アクセス拒否）"

    return detail


def build_file_load_error_payload(path: Path, error: BaseException, index: int) -> Dict[str, Any]:
    return {
        "type": "load_error",
        "path": path,
        "error": build_load_error_detail(path=path, error=error),
        "index": index,
    }


def build_format_duration(seconds: float) -> str:
    whole = max(0, int(seconds))
    if whole < 60:
        return f"{whole}秒"
    minutes, sec = divmod(whole, 60)
    if minutes < 60:
        return f"{minutes}分{sec:02d}秒"
    hours, minutes = divmod(minutes, 60)
    return f"{hours}時間{minutes:02d}分"


def build_loading_hint_text(*, cancel_hint: str = "中止のみ可能") -> str:
    return f"読み込み中は他操作を無効化（{cancel_hint}）"


def build_loading_progress_status_text(
    total: int,
    loaded: int,
    failed_count: int,
    done_count: int,
    elapsed_seconds: float,
    path_text: str,
    failed: bool,
    *,
    loading_hint: str,
) -> str:
    remaining_text = "算出中"
    speed_text = "速度算出中"
    if elapsed_seconds > 0 and total > 0 and done_count > 0:
        speed = done_count / max(0.001, elapsed_seconds)
        if speed > 0:
            remaining_sec = max(0.0, (total - done_count) / speed)
            remaining_text = build_format_duration(remaining_sec)
            speed_text = f"{speed:.1f}件/秒"

    prefix = f"読込中 {done_count}/{total} (成功{loaded} 失敗{failed_count})"
    if path_text:
        action = "失敗" if failed else "処理"
        prefix += f" / {action}: {path_text}"
    return f"{prefix} / 残り約{remaining_text} / {speed_text} / {loading_hint}"


def build_batch_run_mode_text(dry_run: bool) -> str:
    return "ドライラン（実ファイルは作成しません）" if dry_run else "保存"


def build_batch_progress_status_text(
    done_count: int,
    total_count: int,
    processed_count: int,
    failed_count: int,
    elapsed_sec: float,
    current_file_name: str,
    *,
    mode_text: str,
) -> str:
    if done_count <= 0 or total_count <= 0:
        return f"保存中: 0/{total_count}"
    speed = done_count / max(0.001, elapsed_sec)
    remaining_sec = max(0.0, (total_count - done_count) / max(speed, 0.001))
    remaining_text = build_format_duration(remaining_sec)
    return (
        f"保存中 {done_count}/{total_count} (成功{processed_count} 失敗{failed_count}) "
        f"/ 対象: {current_file_name} / 残り約{remaining_text} / {speed:.1f}件/秒"
    )


def build_batch_completion_message(
    total_files: int,
    processed_count: int,
    failed_count: int,
    exif_applied_count: int,
    exif_fallback_count: int,
    gps_removed_count: int,
    reference_job_name: str,
    reference_target: tuple[int, int],
    reference_format_label: str,
    dry_run: bool,
    batch_cancelled: bool,
    dry_run_count: int,
) -> str:
    if batch_cancelled:
        return (
            f"一括処理がキャンセルされました。"
            f"({processed_count}/{total_files}件完了)"
        )
    mode_text = "ドライラン" if dry_run else "保存"
    msg = (
        f"一括処理完了。{processed_count}/{total_files}件を{mode_text}しました。"
        f"\n失敗: {failed_count}件 / EXIF付与: {exif_applied_count}件 / EXIFフォールバック: {exif_fallback_count}件 / GPS削除: {gps_removed_count}件"
    )
    msg += (
        f"\n基準: {reference_job_name} / "
        f"{reference_target[0]}x{reference_target[1]} / {reference_format_label}"
    )
    if dry_run:
        msg += f"\nドライラン件数: {dry_run_count}件"
        msg += "\nドライランのため、実ファイルは作成していません。"
    return msg

