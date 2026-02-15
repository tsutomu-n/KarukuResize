# KarukuResize インストールガイド

このドキュメントは、KarukuResize をローカル環境に導入するための手順をまとめています。

## 前提

- Python 3.12 以上
- Git
- `uv`（推奨）

## 1. リポジトリを取得

```bash
git clone https://github.com/tsutomu-n/KarukuResize.git
cd KarukuResize
```

## 2. 依存関係を同期（開発運用）

```bash
uv sync --group dev
```

この方法は、開発・テスト・ビルドで必要な依存関係をまとめて導入できます。

## 3. コマンドエントリを使いたい場合

`uv run` を使わずに `karuku-resizer` / `karukuresize-cli` を直接使いたい場合は editable install を行います。

```bash
uv pip install -e .
```

## 4. 動作確認

```bash
# GUI
uv run karuku-resizer

# CLI
uv run karukuresize-cli -s input -d output -w 1280 -q 85 --dry-run
```

## 5. OSごとの補足

### Windows
- GUI運用・ビルドともにネイティブ Windows を推奨。
- 詳細は `docs/WINDOWS_GUIDE.md` を参照。

### WSL2
- CLI中心の運用を推奨。
- GUIを使う場合は Windows 側で実行する運用が安定。
- 詳細は `docs/WSL2_GUIDE.md` を参照。

## よくある問題

### `uv: command not found`

`uv` を導入してから再実行してください。

### `No pyproject.toml found`

コマンドを実行しているディレクトリがプロジェクトルート (`KarukuResize/`) か確認してください。

### LinuxでGUIが起動しない

`tkinter` 関連パッケージ不足の可能性があります。例:

```bash
sudo apt-get update
sudo apt-get install -y python3-tk
```

## 次に読むドキュメント

- すぐ使う: `docs/QUICK_START.md`
- ビルド: `docs/BUILDING.md`
