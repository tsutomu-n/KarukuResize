# KarukuResize

KarukuResize は、画像のリサイズ・圧縮・保存を GUI / CLI で扱えるツールです。
同じ設定を複数画像にまとめて適用する作業を、個人用途で安定して実行することを目的にしています。

## 主な機能

### GUI
- プレビューを確認しながら保存
- 出力形式の選択（自動 / JPEG / PNG / WEBP / AVIF）
- EXIF の保持 / 編集 / 削除、GPS削除、ドライラン
- 一括適用保存（現在画像の設定を読込済み全画像に適用）
- プロモードでのフォルダ再帰読込（`jpg/jpeg/png`）
- ドラッグ&ドロップ（ファイル / フォルダ）— 受理拡張子: `png/jpg/jpeg/webp/avif`
- 読込中の進捗表示、キャンセル、失敗のみ再試行
- 最近使った設定（最大6件）
- ファイル上限: 簡易モード 120件 / プロモード 600件（設定で変更可）
- プリセット管理（組み込み + ユーザー定義）、起動時自動適用

### CLI
- フォルダ内画像の一括リサイズ
- 再帰探索の ON / OFF
- 対象拡張子の指定
- ドライラン
- JSONサマリ出力（`--json`）
- 失敗一覧JSON保存（`--failures-file`）
- コンソール整形ログ（Rich）＋ファイルログ

## GUI表示仕様（現行）

- Pro OFF（簡易モード）では、プリセットメニューと `一括適用保存` を非表示
- Pro ON（プロモード）では、プリセットメニューと `一括適用保存` を表示
- 上部ガイド（Top Action Guide）は通常時は非表示、読み込み/処理中のみ表示
- 画像読み込みや一括保存の進捗はステータスバーに表示し、キャンセル操作を提供
- D&D時の単体ファイル受理拡張子は `png/jpg/jpeg/webp/avif`、プロモード再帰読込は `jpg/jpeg/png`

## 動作環境

- Python 3.12 以上
- `uv`（推奨）

## セットアップ

```bash
git clone https://github.com/tsutomu-n/KarukuResize.git
cd KarukuResize
uv sync --group dev
```

## 起動方法

### GUI（推奨）

```bash
uv run karuku-resizer
```

互換エイリアス:

```bash
uv run karukuresize-gui
```

モジュール直接実行:

```bash
uv run python -m karuku_resizer.gui_app
```

### CLI

```bash
uv run karukuresize-cli -s input -d output -w 1280 -q 85
```

## GUI クイックフロー

1. `画像を選択`（プロモードでは `画像/フォルダを選択`）
2. サイズ指定（比率 / 幅 / 高さ / 固定）
3. `プレビュー`
4. `保存` または `一括適用保存`

補足:
- プロモード再帰読込の対象は `jpg/jpeg/png`
- D&Dの単体ファイルは `png/jpg/jpeg/webp/avif` を受理
- 一覧の `クリア` で読込済み画像を一括でリセット可能

## 設定ダイアログ（⚙ボタン）

| 項目 | 説明 |
|---|---|
| Proモード | Pro向け機能（フォルダ再帰読込・EXIF編集等）のオン/オフ |
| カラーテーマ | OSに従う / ライト / ダーク |
| 文字サイズ | 通常 / 大きめ |
| プレビュー拡大率 | 画面に合わせる / 100% / 200% / 300% |
| ホバー説明 | ツールチップの表示オン/オフ |
| 既定の出力形式 | 起動時の出力形式 |
| 既定の品質 | 起動時の品質（5〜100） |
| 既定プリセット | 起動時に自動適用するプリセット |
| プロモード入力方式 | フォルダ再帰 / ファイル個別 |
| 既定の保存先フォルダ | 保存ダイアログの初期フォルダ |
| 使い方を開く | ヘルプダイアログを表示 |
| プリセット管理 | プリセットの追加・編集・削除 |

## 実装アーキテクチャ（概要）

- GUIエントリポイント: `src/karuku_resizer/gui_app.py`
- UI組み立て/配線: `src/karuku_resizer/ui_bootstrap.py`
- UI領域分割:
  - `src/karuku_resizer/ui_topbar.py`
  - `src/karuku_resizer/ui_main_panel.py`
  - `src/karuku_resizer/ui_file_list_panel.py`
  - `src/karuku_resizer/ui_preview_panel.py`
  - `src/karuku_resizer/ui_metadata_panel.py`
  - `src/karuku_resizer/ui_statusbar.py`
  - `src/karuku_resizer/ui_detail_controls.py`
- 文言生成: `src/karuku_resizer/ui_text_presenter.py`
- 表示方針: `src/karuku_resizer/ui_display_policy.py`
- 非同期読込セッション: `src/karuku_resizer/ui/file_load_session.py`
- 保存処理パイプライン: `src/karuku_resizer/image_save_pipeline.py`

## CLI オプション

| オプション | 説明 | 既定値 |
|---|---|---|
| `-s, --source` | 入力フォルダ | 必須 |
| `-d, --dest` | 出力フォルダ | 必須 |
| `-w, --width` | リサイズ後の最大幅(px) | `1280` |
| `-q, --quality` | JPEG/WEBP 品質 (1-100) | `85` |
| `-f, --format` | 出力形式 (`jpeg/png/webp`) | `jpeg` |
| `--recursive / --no-recursive` | 再帰探索する / しない | `--recursive` |
| `--extensions` | 対象拡張子（カンマ区切り） | `jpg,jpeg,png` |
| `--failures-file` | 失敗一覧JSONの保存先 | なし |
| `--dry-run` | 実ファイルを作らずシミュレート | `False` |
| `--json` | 実行結果サマリをJSON出力 | `False` |
| `-v, --verbose` | 詳細ログを増やす | `0` |

例:

```bash
# 直下のみ対象
uv run karukuresize-cli -s input -d output --no-recursive

# 対象拡張子を拡張
uv run karukuresize-cli -s input -d output --extensions jpg,jpeg,png,webp,avif

# 失敗一覧を保存しつつJSON要約を標準出力
uv run karukuresize-cli -s input -d output --failures-file failures.json --json
```

## ログ出力

実行ログとサマリは OS 標準ログディレクトリへ保存（GUI / CLI 共通）:

- Windows: `%LOCALAPPDATA%\KarukuResize\logs`
- Linux/macOS: `~/.local/state/karukuresize/logs`（`XDG_STATE_HOME` で上書き可）

保持ポリシー: 最大 `100` ファイル / `30` 日

## GUI設定ファイル

GUI設定は OS 標準設定ディレクトリに保存:

- Windows: `%APPDATA%\\KarukuResize\\settings.json`
- Linux/macOS: `~/.config/karukuresize/settings.json`（`XDG_CONFIG_HOME` で上書き可）

旧 `karuku_settings.json`（カレントディレクトリ）は初回起動時に自動移行されます。

## Windows ビルド

```powershell
uv run karukuresize-build-exe
```

- 生成物: `dist\KarukuResize.exe`
- EXEアイコン: `assets\app.ico`
- UI確認推奨: Windows 100% / 125% / 150% DPI（200%は任意）

詳細: `docs/WINDOWS_GUIDE.md`, `docs/BUILDING.md`

## 開発

```bash
uv run pytest -q
uv run ruff check src tests
uvx basedpyright src
uv run pre-commit run --all-files
```

## 主要ドキュメント

- `design.md`
- `CONTRIBUTING.md`
- `docs/QUICK_START.md`
- `docs/WINDOWS_GUIDE.md`
- `docs/BUILDING.md`
- `docs/WSL2_GUIDE.md`
- `docs/INSTALLATION.md`
- `docs/api_reference.md`
- `docs/developer_guide.md`

## ライセンス

Apache License 2.0
