# コード実態（GUI / 保存パイプライン）

## 1. GUI層（`src/karuku_resizer/gui_app.py`）

### 1.1 設定モデル
- `SettingsManager._default_settings()` で永続化キーを定義。
- 主要キー（現在）:
  - `ui_mode`
  - `quality`
  - `output_format`
  - `webp_method`
  - `webp_lossless`
  - `avif_speed`
  - `exif_mode`
  - `remove_gps`
  - `dry_run`
  - `verbose_logging`
- 参照: `src/karuku_resizer/gui_app.py:163`

### 1.2 モード制御
- `UI_MODE_LABEL_TO_ID` で `簡易/simple`, `プロ/pro` をマッピング。
- `_apply_ui_mode()` で、プロ時のみ詳細フレーム（advanced/codec）を表示。
- 参照: `src/karuku_resizer/gui_app.py:108`, `src/karuku_resizer/gui_app.py:403`

### 1.3 詳細設定の構成
- `_setup_settings_layers()`:
  - 設定サマリ
  - 簡易/プロセグメント
  - 詳細設定表示トグル
- `_setup_output_controls()`:
  - 出力形式、品質、EXIF、GPS削除、ドライラン
  - 詳細ログ、EXIF差分
  - WEBP method/lossless, AVIF speed
- 参照: `src/karuku_resizer/gui_app.py:316`, `src/karuku_resizer/gui_app.py:620`

### 1.4 EXIFプレビュー機能（既存）
- `_show_exif_preview_dialog()` で現在選択画像の保存時EXIF反映計画をダイアログ表示。
- 参照: `src/karuku_resizer/gui_app.py:1353`

### 1.5 設定保存復元
- `_restore_settings()` で読み込み反映。
- `_save_current_settings()` で終了時保存。
- 参照: `src/karuku_resizer/gui_app.py:1143`, `src/karuku_resizer/gui_app.py:1215`

## 2. 保存パイプライン（`src/karuku_resizer/image_save_pipeline.py`）

### 2.1 正規化と形式対応
- `normalize_quality`: 5..100、5刻みに丸め。
- `normalize_webp_method`: 0..6。
- `normalize_avif_speed`: 0..10。
- `supported_output_formats`: 実行環境サポート検出。
- 参照: `src/karuku_resizer/image_save_pipeline.py:92`, `src/karuku_resizer/image_save_pipeline.py:102`, `src/karuku_resizer/image_save_pipeline.py:109`, `src/karuku_resizer/image_save_pipeline.py:114`

### 2.2 エンコーダ引数
- `build_encoder_save_kwargs()`:
  - JPEG: quality(<=95), optimize, progressive
  - PNG: quality->compress_level 変換
  - WEBP: quality/method/lossless
  - AVIF: quality/speed
- 参照: `src/karuku_resizer/image_save_pipeline.py:308`

### 2.3 EXIF処理
- `preview_exif_plan()`: 保存前計画を計算。
- `_build_exif_bytes()`: keep/remove/edit + GPS削除の実体。
- `save_image()`: EXIF付与失敗時にフォールバック保存。
- 参照: `src/karuku_resizer/image_save_pipeline.py:151`, `src/karuku_resizer/image_save_pipeline.py:357`, `src/karuku_resizer/image_save_pipeline.py:191`

## 3. 現状評価（本計画観点）
1. カラースキームは内部的にtuple色対応済みだが、ユーザーが選ぶUIは未提供。
2. メタデータの編集・差分確認はあるが、常時プレビュー領域への表示は未提供。
3. 実装の主戦場は `gui_app.py` に集約可能で、既存パイプライン改修は最小で済む見込み。
