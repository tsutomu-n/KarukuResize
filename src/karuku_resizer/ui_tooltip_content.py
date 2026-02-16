"""GUI tooltip copy deck for ResizeApp.

UI改修時に文言だけを独立して更新できるよう、ホバー解説を集約する。
"""

from __future__ import annotations

TOP_AND_PRESET_TOOLTIPS = {
    "select_button": "画像またはフォルダを読み込みます。プロモードではフォルダ再帰読込が使えます。",
    "help_button": "使い方を表示します。",
    "settings_button": "設定画面を開きます。",
    "preset_menu": "保存済みの処理設定（プリセット）を選択します。",
    "preset_apply_button": "選択中のプリセットを現在の入力欄へ反映します。",
    "preset_save_button": "現在の設定を新しいプリセットとして保存します。",
    "preset_manage_button": "プリセットの名称変更・削除を行います。",
}

SIZE_MODE_TOOLTIPS = [
    "元画像の縦横比を保ったまま、比率(%)で拡大縮小します。",
    "幅を固定し、高さは縦横比から自動計算します。",
    "高さを固定し、幅は縦横比から自動計算します。",
    "幅と高さを固定して変換します。縦横比は維持しません。",
]

ENTRY_AND_ACTION_TOOLTIPS = {
    "ratio_entry": "比率(%)を数値で入力します（例: 50, 100, 150）。",
    "entry_w_single": "幅(px)を数値で入力します。",
    "entry_h_single": "高さ(px)を数値で入力します。",
    "entry_w_fixed": "固定幅(px)を入力します。",
    "entry_h_fixed": "固定高(px)を入力します。",
    "preview_button": "現在の設定で変換後プレビューを表示します。",
    "save_button": "選択中の画像1枚だけ保存します。",
    "batch_button": "現在設定を読み込み済み画像すべてに適用して保存します。",
    "zoom_cb": "プレビューの表示倍率を変更します。",
}

ADVANCED_CONTROL_TOOLTIPS = {
    "ui_mode_segment": "画面モード（簡易/プロ）を切り替えます。",
    "details_toggle_button": "詳細設定パネルの表示/非表示を切り替えます。",
    "metadata_toggle_button": "メタデータ表示を切り替えます。",
    "output_format_menu": "出力形式を選択します。",
    "quality_menu": "圧縮品質を選択します。",
    "exif_mode_menu": "EXIFの扱いを選択します。",
    "remove_gps_check": "EXIF内のGPS情報を削除します。",
    "dry_run_check": "保存せずに処理結果を確認します。",
    "verbose_log_check": "詳細ログを有効化します。",
    "exif_preview_button": "EXIF変更内容を確認します。",
    "open_log_folder_button": "ログ保存フォルダを開きます。",
    "webp_method_menu": "WEBP方式を選択します。",
    "webp_lossless_check": "WEBPを可逆圧縮で保存します。",
    "avif_speed_menu": "AVIF速度を選択します。",
    "cancel_button": "実行中の処理を中断します。",
}

UI_MODE_VALUE_TOOLTIPS = {
    "簡易": "基本項目のみ表示するモードです。",
    "プロ": "再帰読込や詳細設定を使う上級モードです。",
}

FILE_FILTER_VALUE_TOOLTIPS = {
    "全件": "読み込み済みの全画像を一覧表示します。",
    "失敗": "直近処理で失敗した画像のみ一覧表示します。",
    "未処理": "まだ処理していない画像のみ一覧表示します。",
}
