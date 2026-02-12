# KarukuResize

KarukuResize は、画像のリサイズと保存を GUI / CLI の両方で扱えるツールです。  
個人利用での「まとめて整える」「同じ設定をまとめて適用する」作業を、素早く安全に行うことを目的にしています。

## できること

### GUI
- 画像プレビューを見ながら設定して保存
- 出力形式の選択（自動 / JPEG / PNG / WEBP / AVIF）
- EXIF の保持 / 編集 / 削除、GPS削除、ドライラン
- 一括適用保存（選択中画像の設定を読込済み全画像へ適用）
- プロモードの再帰読込（`jpg / jpeg / png`）
- ドラッグ&ドロップ読込（ファイル / フォルダー）
- 読込中の進捗表示、キャンセル、失敗のみ再試行
- 最近使った設定の再適用（最大6件）

### CLI
- フォルダー内画像の一括リサイズ保存
- 再帰探索の ON / OFF
- 対象拡張子の指定
- ドライラン
- 実行結果JSON出力（`--json`）
- 失敗一覧JSON保存（`--failures-file`）
- Rich による読みやすいログ出力

## 必要環境

- Python 3.12 以上
- `uv`（推奨）

## セットアップ

```bash
git clone https://github.com/tsutomu-n/KarukuResize.git
cd KarukuResize
uv sync --group dev
```

## 起動方法

### GUI

```bash
uv run karukuresize-gui
# または
uv run python -m karuku_resizer.gui_app
```

### CLI

```bash
uv run karukuresize-cli -s input -d output -w 1280 -q 85
```

## GUI クイックフロー

1. `📂 画像を選択`（プロモードでは `📂 画像/フォルダを選択`）
2. サイズを指定（比率 / 幅 / 高さ / 固定）
3. `🔄 プレビュー`
4. `💾 保存`（単体）または `📁 一括適用保存`（全体）

補足:
- プロモード再帰読込の対象は `jpg / jpeg / png`
- D&D単体ファイルは `png / jpg / jpeg / webp / avif` も受理

## CLI オプション

| オプション | 説明 | 既定値 |
|---|---|---|
| `-s, --source` | 入力フォルダー | 必須 |
| `-d, --dest` | 出力フォルダー | 必須 |
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

## Windows ビルド

```powershell
uv run karukuresize-build-exe
```

- 生成物: `dist\KarukuResize.exe`
- EXEアイコンは `assets\app.ico` を使用

詳細は `docs/WINDOWS_GUIDE.md` と `docs/BUILDING.md` を参照してください。

## ドキュメント

- `CONTRIBUTING.md`
- `docs/QUICK_START.md`
- `docs/WINDOWS_GUIDE.md`
- `docs/BUILDING.md`
- `docs/WSL2_GUIDE.md`
- `docs/INSTALLATION.md`
- `docs/api_reference.md`

## 開発

```bash
uv run pytest -q
uv run ruff check src tests
```

## ライセンス

MIT License
