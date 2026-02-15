# KarukuResize クイックスタート

このガイドは、最短で使い始めるための手順です。

## 1. セットアップ

```bash
git clone https://github.com/tsutomu-n/KarukuResize.git
cd KarukuResize
uv sync --group dev
```

## 2. 起動

### GUI（推奨）

```bash
uv run karuku-resizer
```

互換エイリアス:

```bash
uv run karukuresize-gui
```

### CLI

```bash
uv run karukuresize-cli -s input -d output -w 1280 -q 85
```

## 3. GUI の基本フロー

1. `画像を選択` で画像またはフォルダを読み込む
2. 必要に応じてサイズ指定（比率 / 幅 / 高さ / 固定）
3. `プレビュー`
4. `保存`（単体）または `一括適用保存`（全体）

補足:
- ドラッグ&ドロップでも読み込み可能
- プロモードの再帰読込対象は `jpg/jpeg/png`
- 失敗がある場合は「失敗のみ再試行」が可能

## 4. 一括適用保存の使いどころ

- 現在選択中の設定を、読込済み画像全体に適用したいとき
- 画質やEXIF方針を揃えて一気に保存したいとき
- `ドライラン` で先に結果件数だけ確認したいとき

## 5. CLI 例

```bash
# 再帰なし（直下のみ）
uv run karukuresize-cli -s input -d output --no-recursive

# 対象拡張子を指定
uv run karukuresize-cli -s input -d output --extensions jpg,jpeg,png,webp,avif

# JSON要約と失敗一覧ファイルを出力
uv run karukuresize-cli -s input -d output --json --failures-file failures.json
```

## 6. 困ったとき

- インストール関連: `docs/INSTALLATION.md`
- Windows運用: `docs/WINDOWS_GUIDE.md`
- WSL2運用: `docs/WSL2_GUIDE.md`
- ビルド: `docs/BUILDING.md`
