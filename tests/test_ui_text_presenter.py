from karuku_resizer.ui_text_presenter import (
    build_action_hint_text,
    build_empty_state_text,
    build_settings_summary_text,
    build_session_status_text,
    build_top_action_guide_text,
)


def test_build_top_action_guide_text_states() -> None:
    assert build_top_action_guide_text(is_loading_files=True, is_processing=False) == "画像読み込み中…"
    assert build_top_action_guide_text(is_loading_files=False, is_processing=True) == "処理中 — キャンセル以外の操作はできません"
    assert build_top_action_guide_text(is_loading_files=False, is_processing=False) == ""


def test_build_empty_state_text() -> None:
    normal = build_empty_state_text(is_pro_mode=False, processing_hint="キャンセル")
    assert "1. 画像を選択" in normal
    assert "3. プレビュー後に保存" in normal
    assert "処理中: キャンセル" in normal

    pro = build_empty_state_text(is_pro_mode=True, processing_hint="キャンセル")
    assert "Pro: フォルダー再帰読込" in pro


def test_build_action_hint_text() -> None:
    assert build_action_hint_text(
        is_loading_files=True,
        is_processing=False,
        has_jobs=False,
        has_current_selection=False,
    ) == "読み込み中です。完了または中止後に操作できます。"
    assert build_action_hint_text(
        is_loading_files=False,
        is_processing=True,
        has_jobs=False,
        has_current_selection=False,
    ) == "処理中です。キャンセル以外の操作はできません。"
    assert build_action_hint_text(
        is_loading_files=False,
        is_processing=False,
        has_jobs=False,
        has_current_selection=False,
    ) == "画像が未選択です。まず画像を読み込んでください。"
    assert build_action_hint_text(
        is_loading_files=False,
        is_processing=False,
        has_jobs=True,
        has_current_selection=False,
    ) == "左の一覧から対象画像を選択してください。"
    assert build_action_hint_text(
        is_loading_files=False,
        is_processing=False,
        has_jobs=True,
        has_current_selection=True,
    ) == "準備完了です。プレビュー・保存を実行できます。"


def test_build_settings_summary_text() -> None:
    summary = build_settings_summary_text(
        output_format="JPEG",
        quality="85",
        exif_mode_label="保持",
        remove_gps=True,
        dry_run=True,
        is_pro_mode=True,
        format_id="webp",
        webp_method="4",
        webp_lossless=False,
        avif_speed="2",
    )
    assert summary.startswith("現在: Pro / ")
    assert "Q85" in summary
    assert "EXIF保持（位置情報除去）" in summary
    assert "ドライラン:ON" in summary
    assert "WEBP method 4" in summary


def test_build_session_status_text() -> None:
    status = build_session_status_text(
        is_pro_mode=False,
        dry_run=False,
        total_jobs=3,
        failed_jobs=1,
        unprocessed_jobs=1,
        visible_jobs=2,
        file_filter_label="全件",
        output_dir="/tmp",
    )
    assert "モード Pro OFF" in status
    assert "表示 2/3 (全件)" in status
    assert "未処理 1 / 失敗 1" in status
