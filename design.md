# KarukuResize GUI設計（現行）

## 概要

KarukuResize は、画像のリサイズ/保存を GUI/CLI で提供するアプリケーションです。  
本ドキュメントは、現行実装（`src/karuku_resizer`）に合わせた GUI 設計の実体をまとめます。

- UI 基盤: `customtkinter`
- 主対象: 日常的な複数画像処理（プレビュー確認、単体保存、一括適用保存）
- 重点: 操作の一貫性、保存失敗時の復旧性、非同期処理中の安全な UI 状態管理

## 設計目標

1. `ResizeApp` は起動・状態管理・イベント配線に集中する  
2. UI 構築責務は `ui_*` モジュールへ分割し、契約を固定する  
3. 文言と表示分岐を専用モジュールへ集約する  
4. 非同期処理の UI 反映はメインスレッド（`after()`）経由で行う  
5. 設定キー互換を維持しつつ、永続化を安定化する

## 全体アーキテクチャ

```
ResizeApp (gui_app.py)
  ├─ UI bootstrap / wiring
  │   └─ ui_bootstrap.py
  ├─ Main layout composition
  │   └─ ui_main_panel.py
  │       ├─ ui_file_list_panel.py
  │       ├─ ui_preview_panel.py
  │       ├─ ui_metadata_panel.py
  │       └─ ui_statusbar.py
  ├─ Top bar / mode visibility
  │   └─ ui_topbar.py
  ├─ Detail controls
  │   └─ ui_detail_controls.py
  ├─ Text / display policy
  │   ├─ ui_text_presenter.py
  │   └─ ui_display_policy.py
  ├─ Async file load session
  │   └─ ui/file_load_session.py (+ ui_file_load_helpers.py)
  ├─ Save pipeline
  │   └─ image_save_pipeline.py (+ ui_save_helpers.py)
  └─ Persistence
      ├─ gui_settings_store.py
      └─ processing_preset_store.py
```

## 主要モジュール責務

### `src/karuku_resizer/gui_app.py`

- `ResizeApp` 本体
- UI状態（ジョブ一覧、選択状態、進捗状態、モード）保持
- 各 `ui_*` モジュールへの委譲とイベント配線
- 設定ダイアログ/プリセットダイアログ呼び出し

### `src/karuku_resizer/ui_bootstrap.py`

- アプリ起動時の UI 初期構築
- TopBar / Detail / MainPanel の結線
- 選択/保存/一括保存/ドラッグ&ドロップ関連の委譲先
- フォント・アイコン・スケーリング・ツールチップ登録補助

### `src/karuku_resizer/ui_main_panel.py`

- MainPanel の統合ビルダー
- `StatusBar` / `FileList` / `Preview` / `Metadata` の組み立て
- `MainPanelState` / `MainPanelCallbacks` / `MainPanelRefs` を契約として提供

### `src/karuku_resizer/ui_topbar.py`

- TopBar 構築と密度切替（`normal` / `compact`）
- Proモードによる可視制御:
  - Pro ON: プリセット、`一括適用保存` を表示
  - Pro OFF: 上記を非表示
- 上部ガイドテキストは通常非表示、状態時のみ表示

### `src/karuku_resizer/ui_text_presenter.py`

- ステータス文言、進捗文言、EXIF表示文言を純関数で生成
- GUI 本体から文言ロジックを分離

### `src/karuku_resizer/ui_display_policy.py`

- 表示ルールの純関数
- 例: `TOPBAR_DENSITY_COMPACT_MAX_WIDTH = 1366` を境界とする密度判定

### `src/karuku_resizer/ui/file_load_session.py`

- 非同期読込セッションの開始/進行/終了
- バックグラウンドワーカーとキューを橋渡し
- `after()` ポーリングで UI スレッド更新を保証

### `src/karuku_resizer/image_save_pipeline.py`

- 保存フォーマット解決、エンコーダ引数構築、EXIF処理
- 一時ファイル経由の atomic 保存
- エラー分類（再試行可否・ガイダンス）を `SaveResult` に集約

## UI 構造（論理）

```
ResizeApp
  ├─ TopBar
  │   ├─ 選択/ヘルプ/設定
  │   ├─ モード/サイズ入力
  │   ├─ プリセット（Pro ON）
  │   └─ プレビュー/保存/一括保存（一括は Pro ON）
  ├─ Detail Controls（折りたたみ）
  ├─ Main Panel
  │   ├─ File List + フィルタ + クリア
  │   ├─ Preview（原寸 / リサイズ後）
  │   └─ Metadata（Pro ON時中心）
  └─ StatusBar（進捗 + キャンセル + セッション要約）
```

## データモデル

### `ImageJob`（`gui_app.py`）

- `path`, `image`, `resized`
- メタデータ表示状態（`metadata_loaded`, `metadata_text`, `metadata_error`）
- 最終処理状態（`last_process_state`, `last_error_detail`）

### `BatchSaveStats`（`gui_app.py`）

- 成功/失敗/ドライラン件数
- EXIF適用件数、EXIFフォールバック件数、GPS削除件数
- 失敗詳細（表示・再試行用）

### `SaveOptions` / `SaveResult`（`image_save_pipeline.py`）

- 保存パラメータと結果を明示的に表現
- 失敗原因の分類と再試行判断に利用

## 非同期読込フロー

1. UIイベント（選択/D&D）で読込セッション開始  
2. ワーカースレッドが探索/読込してキューへメッセージ投入  
3. UIスレッドが `after()` でキューをポーリング  
4. メッセージに応じて UI 更新（進捗、一覧、エラー）  
5. 完了時にセッション終了、必要に応じて「失敗のみ再試行」を提供

この構造により、読込中の UI フリーズを避けつつ、更新は常にメインスレッドで実行します。

## 表示/モード仕様

- UIモード:
  - `simple`（Pro OFF）
  - `pro`（Pro ON）
- Pro OFF:
  - プリセット UI と一括保存を非表示
  - EXIFモード選択は `保持/削除` 中心
- Pro ON:
  - プリセット管理、一括適用保存、再帰読込などを有効化
- Top guide:
  - 通常時は非表示
  - 読込中/処理中のみ表示

## 設定永続化

`src/karuku_resizer/gui_settings_store.py` が `settings.json` を管理します。

- Windows: `%APPDATA%\\KarukuResize\\settings.json`
- Linux/macOS: `~/.config/karukuresize/settings.json`（`XDG_CONFIG_HOME` 対応）

代表キー:

- `ui_mode`, `appearance_mode`, `ui_scale_mode`
- `mode`, `ratio_value`, `width_value`, `height_value`
- `quality`, `output_format`, `webp_method`, `webp_lossless`, `avif_speed`
- `exif_mode`, `remove_gps`, `exif_*`
- `zoom_preference`, `default_output_dir`, `default_preset_id`
- `pro_input_mode`, `recent_processing_settings`

## エラー処理方針

- 読込/保存の失敗は例外を握りつぶさず、ユーザーへ要点を表示
- 保存失敗時は `SaveResult` の分類（権限、パス長、ロック、容量等）を提示
- バッチ処理は個別失敗で全体停止せず継続し、失敗のみ再試行を可能にする
- 実行ログ・サマリは `runtime_logging.py` の保持ポリシーで管理

## 契約と依存ルール

- UI領域モジュールは `dataclass` + `Protocol` 契約を優先
- UIモジュール間の直接依存は最小化し、`gui_app.py` / `ui_bootstrap.py` 経由で配線
- 文言生成は `ui_text_presenter.py`、表示判定は `ui_display_policy.py` に集約

## 検証コマンド（推奨）

```bash
PYTHONPATH=src uv run ruff check src tests
PYTHONPATH=src uv run pytest -q
uvx basedpyright src
```

