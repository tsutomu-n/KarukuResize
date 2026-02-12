# KarukuResize クイックスタート

このガイドは「すぐ使う」ための最短手順です。

## 1. セットアップ

### 共通
- Python 3.12 以上
- `uv`（推奨）または `pip`

```bash
# プロジェクトルートで実行
uv sync --group dev
```

## 2. 起動

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

## 3. GUIの基本フロー

1. `📂 画像を選択`（プロモードは `📂 画像/フォルダを選択`）
2. またはウィンドウへ直接ドラッグ&ドロップ（ファイル/フォルダー）
3. サイズ指定（比率/幅/高さ/固定）
4. `🔄 プレビュー`
5. `💾 保存`（単体）または `📁 一括適用保存`（読込済み全体）

## 4. プロモードの再帰読込

1. `プロ` に切り替え
2. `📂 画像/フォルダを選択`
3. ダイアログで `はい` を選ぶとフォルダ再帰読込
4. 対象拡張子: `jpg / jpeg / png`
5. ドラッグ&ドロップ時の単体ファイルは `png / jpg / jpeg / webp / avif` を受理

補足:
- 前回の入力方式（再帰/個別）は記憶されます。
- 読込中は他操作を無効化し、`読み込み中止` が使えます。
- 進捗、成功/失敗件数、残り時間目安を表示します。
- 失敗がある場合は完了時に「失敗のみ再試行」が可能です。

## 5. 一括適用保存のポイント

- 選択中画像の設定を基準に、読込済み画像すべてへ適用します。
- `ドライラン` ON 時はファイルを作成せず結果のみ確認できます。
- 失敗があっても全体処理は継続し、完了時に失敗詳細を表示します。

## 6. よく使うCLIコマンド

```bash
# 高品質
uv run karukuresize-cli -s input -d output -w 1920 -q 95

# 軽量化優先
uv run karukuresize-cli -s input -d output -w 800 -q 75

# 保存しない確認
uv run karukuresize-cli -s input -d output -w 1280 --dry-run
```

## 7. 問題が起きたとき

- GUIが起動しない:
  - `uv sync --group dev` を再実行
  - `uv run python -m karuku_resizer.gui_app` でエラー詳細確認
- WSL2でGUIが不安定:
  - Windows側でGUIを起動（`docs/WINDOWS_GUIDE.md` を参照）
- ビルドしたい:
  - `docs/BUILDING.md` を参照
