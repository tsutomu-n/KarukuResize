# KarukuResize ビルドガイド

このドキュメントは、PyInstaller を使って実行ファイルを作成する手順をまとめています。

## 前提

- Python 3.12 以上
- `uv`
- Git

```bash
git clone https://github.com/tsutomu-n/KarukuResize.git
cd KarukuResize
uv sync --group dev
```

## 標準ビルド（推奨）

```bash
uv run karukuresize-build-exe
```

このコマンドは `src/karuku_resizer/build_exe.py` を実行し、PyInstallerで onefile ビルドします。

生成物:
- Windows: `dist/KarukuResize.exe`
- macOS/Linux: `dist/KarukuResize`

## Spec ファイルを使う場合

```bash
uv run pyinstaller KarukuResize.spec
```

`KarukuResize.spec` はリポジトリ管理対象です。
必要に応じて `datas` / `hiddenimports` / `icon` を調整してください。

## アイコン

- 既定のEXEアイコン: `assets/app.ico`
- 変更する場合は `assets/app.ico` を差し替えて再ビルド

## ビルド後の最小確認

1. アプリが起動する
2. 画像読み込み → プレビュー → 保存が実行できる
3. 一括適用保存が完了する
4. エラー発生時に内容を確認できる

## トラブルシュート

### `PyInstaller is not installed`

```bash
uv sync --group dev
```

### `Spec file "KarukuResize.spec" not found`

実行ディレクトリがプロジェクトルートか確認してください。

### `tkinterdnd2` 関連のビルドエラー

`src/karuku_resizer/tools/hook-tkinterdnd2.py` が存在するか確認し、`karukuresize-build-exe` を使ってビルドしてください。

## CI

GitHub Actions の `build.yml` でマルチOSビルドが設定されています。
タグ push または workflow dispatch でビルドできます。

## ライセンス

ビルド成果物はソースコードと同じく Apache License 2.0 に従います。
