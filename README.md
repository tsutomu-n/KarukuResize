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
- ドラッグ&ドロップ（ファイル / フォルダ）
- 読込中の進捗表示、キャンセル、失敗のみ再試行
- 最近使った設定（最大6件）

### CLI
- フォルダ内画像の一括リサイズ
- 再帰探索の ON / OFF
- 対象拡張子の指定
- ドライラン
- JSONサマリ出力（`--json`）
- 失敗一覧JSON保存（`--failures-file`）
- コンソール整形ログ（Rich）＋ファイルログ

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

### GUI
- 実行ログとサマリは OS 標準ログディレクトリへ保存
  - Windows: `%LOCALAPPDATA%\\KarukuResize\\logs`
  - Linux: `~/.local/state/karukuresize/logs`

### CLI
- 開発環境（リポジトリ実行）では `src/logs/process_*.log`
- `KARUKU_LOG_DIR` 環境変数で上書き可能
- ローテーション: `10 MB`
- 保持期間: `14 days`
- 圧縮: `zip`

## Windows ビルド

```powershell
uv run karukuresize-build-exe
```

- 生成物: `dist\\KarukuResize.exe`
- EXEアイコン: `assets\\app.ico`
- UI確認推奨: Windows 100% / 125% / 150% DPI（200%は任意）

詳細: `docs/WINDOWS_GUIDE.md`, `docs/BUILDING.md`

## 開発

```bash
uv run pytest -q
uv run ruff check src tests
uv run pre-commit run --all-files
```

## 主要ドキュメント

- `CONTRIBUTING.md`
- `docs/QUICK_START.md`
- `docs/WINDOWS_GUIDE.md`
- `docs/BUILDING.md`
- `docs/WSL2_GUIDE.md`
- `docs/INSTALLATION.md`
- `docs/api_reference.md`

## ライセンス

MIT License
