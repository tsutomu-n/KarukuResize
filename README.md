# KarukuResize

「軽く」画像をリサイズする高機能ツール

## 概要

KarukuResizeは画像のリサイズと圧縮を簡単に行えるマルチインターフェースツールです。GUIとCLIの両方に対応しています。日本語環境での使用に最適化され、Windows環境での長パス対応など実用的な機能を多数備えています。

## 特徴

- **使いやすいGUIインターフェース** - 直感的な操作で画像処理が可能
- **パワフルなコマンドラインツール** - バッチ処理やスクリプト自動化に最適
- **複数フォーマットサポート** - JPEG, PNG, WEBP, GIF, BMP, TIFFなどの主要フォーマットに対応
- **アスペクト比の維持** - 画像の縦横比を保ちながらリサイズ可能
- **詳細なログ出力** - 処理状況と結果を分かりやすく表示
- **Windows長パス対応** - 260文字制限を回避した安全なファイル処理
- **日本語ファイル名対応** - 絵文字を含む特殊文字も適切に処理
- **高度なエラーハンドリング** - 詳細な日本語エラーメッセージと自動リトライ機能


### 1. リポジトリの準備
```cmd
:: 現在のディレクトリをリネーム（バックアップとして）
cd C:\path\to\your\projects
ren karukuresize karukuresize-backup

:: 新しいディレクトリを作成
mkdir KarukuResize
cd KarukuResize

:: 必要なディレクトリ構造を作成
mkdir log docs
```

### 2. プロジェクト構造の再編成
```cmd
:: コアモジュールディレクトリの作成
mkdir karukuresize
type nul > karukuresize\__init__.py

:: 既存のコードをコピー
copy C:\path\to\your\projects\karukuresize-backup\resize_core.py karukuresize\core.py
copy C:\path\to\your\projects\karukuresize-backup\resize_images.py karukuresize\cli.py
copy C:\path\to\your\projects\karukuresize-backup\resize_images_gui.py karukuresize\gui.py

:: ドキュメントをコピー
xcopy C:\path\to\your\projects\karukuresize-backup\docs\* docs\ /E /I

:: 設定ファイルをコピー
copy C:\path\to\your\projects\karukuresize-backup\pyproject.toml .
```

### 3. コードの修正

#### 3.1 pyproject.toml の修正
```toml
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "karukuresize"
version = "0.1.0"
description = "「軽く」画像をリサイズする高機能ツール"
readme = "README.md"
requires-python = ">=3.12"
authors = [
    {name = "Your Name", email = "your.email@example.com"},
]
dependencies = [
    "pillow",
    "customtkinter",
    "tqdm",
    "loguru",
]

[project.scripts]
karukuresize = "karukuresize.cli:main"
karukuresize-gui = "karukuresize.gui:main"

[tool.hatch.build.targets.wheel]
packages = ["karukuresize"]
```

#### 3.2 core.py のインポート修正
```python
# karukuresize/core.py のインポート文を修正
# 必要に応じてパスの修正
```

#### 3.3 cli.py のインポート修正
```python
# karukuresize/cli.py のインポート文を修正
# 以下のように変更
# from resize_core import ... の行を
from karukuresize.core import ...

# import resize_core as core の行を
import karukuresize.core as core
```

#### 3.4 gui.py のインポート修正
```python
# karukuresize/gui.py のインポート文を修正
# 以下のように変更
# from resize_core import ... の行を
from karukuresize.core import ...
```

#### 3.5 エントリーポイントスクリプトの作成
```python
# karukuresize/__main__.py を作成
#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
KarukuResize - 「軽く」画像をリサイズする高機能ツール
"""

import sys
from karukuresize import cli

if __name__ == "__main__":
    sys.exit(cli.main())
```

### 4. インストールと動作確認
```cmd
:: 開発モードでインストール
cd C:\path\to\your\projects\KarukuResize
uv install -e .

:: CLIの動作確認
python -m karukuresize.cli --help

:: GUIの動作確認
python -m karukuresize.gui
```

## 使い方

### GUIモード

```cmd
:: インストール済みの場合
karukuresize-gui

:: または直接実行
python -m karukuresize.gui
```

### コマンドラインモード

```cmd
:: インストール済みの場合
karukuresize -s 入力フォルダ -d 出力フォルダ -w 1280 -q 85

:: または直接実行
python -m karukuresize.cli -s 入力フォルダ -d 出力フォルダ
```

### 主なオプション

- `-s`, `--source`: 入力元のディレクトリパス
- `-d`, `--dest`: 出力先のディレクトリパス
- `-w`, `--width`: リサイズ後の最大幅 (デフォルト: 1280)
- `-q`, `--quality`: 画像の品質 (0-100、デフォルト: 85)
- `--dry-run`: 実際にファイルを保存せずシミュレートする
- `--resume`: 既存の出力ファイルがあればスキップする
- `--log-level`: ログレベルを設定 (DEBUG, INFO, WARNING, ERROR, CRITICAL)
- `--check-disk`: 処理前にディスク容量を確認する
- `--debug`: デバッグモードを有効にする（詳細なエラー情報を表示）

## 機能詳細

### コア機能（共通）
- 複数の画像形式サポート（JPEG, PNG, WEBP, GIF, BMP, TIFF）
- 高度な圧縮アルゴリズム
- アスペクト比の保持または変更
- Windows長パス対応（260文字制限の回避）
- 日本語ファイル名・パス対応
- 詳細なログ記録
- 処理進捗の表示

### CLI機能（resize_images.py）
- バッチ処理機能（複数ファイルの一括処理）
- コマンドライン引数によるカスタマイズ
- 処理の中断・再開機能
- 処理統計情報の表示（ファイルサイズ削減率など）
- Ctrl+C によるグレースフル終了

### GUI機能（resize_images_gui.py）
- モダンなインターフェース（customtkinter使用）
- 単一画像処理モード
  - ファイル選択ダイアログ
  - 出力先設定
  - 出力形式選択（JPEG/PNG/WEBP）
  - リサイズモード選択
  - 品質/圧縮率スライダー
  - EXIFデータ処理設定
- バッチ処理モード
  - フォルダ選択ダイアログ
  - 出力形式一括設定
  - リサイズモード（幅/高さ/長辺/短辺/パーセント）
  - 品質設定（JPEG/WEBP）
  - WebP用ロスレスオプション
  - 再帰的処理オプション
- リアルタイムプログレスバー
- 詳細ログ表示
- 処理のキャンセル機能

### 特殊機能
- 処理の進捗保存と再開
- 自動エラーリトライ機能
- パス正規化（絵文字などのUnicode文字を含むパスも処理）
- 安全なファイル名変換
- ディスク容量チェック
- 圧縮と品質のバランス調整
- 詳細なエラー分析と日本語エラーメッセージ

## 🚀 クイックスタート

```bash
# 1. インストール
uv pip install -e .

# 2. CLI実行
karukuresize-cli -s input -d output -w 1280 -q 85

# 3. GUI実行
karukuresize-gui
```

詳細は[クイックスタートガイド](./QUICK_START.md)をご覧ください。

## 📚 ドキュメント

- [インストールガイド](./INSTALLATION.md) - 詳細なインストール手順
- [クイックスタート](./QUICK_START.md) - すぐに使い始めるためのガイド
- [WSL2ガイド](./WSL2_GUIDE.md) - WSL2での使用方法
- [Windowsガイド](./WINDOWS_GUIDE.md) - Windows 11での使用方法
- [開発者ガイド](./docs/developer_guide.md) - 開発者向けの技術情報
- [APIリファレンス](./docs/api_reference.md) - 関数とクラスの詳細仕様

## 🧪 テスト

```bash
# すべてのテストを実行
pytest

# カバレッジ付きで実行
pytest --cov=resize_core --cov-report=html
```

## 開発

プルリクエストや機能提案は大歓迎です。コード品質維持のため、pre-commitフックを使用したruffとruff-formatによる自動チェックを導入しています。

### 開発環境のセットアップ

```cmd
:: 開発モードでインストール
cd C:\path\to\your\projects\KarukuResize
uv pip install -e .

:: pre-commitフックをインストール
pre-commit install
```

## ライセンス

MIT License
