# KarukuResize

「軽く」画像をリサイズする高機能ツール

## 概要

KarukuResizeは画像のリサイズと圧縮を簡単に行えるマルチインターフェースツールです。GUIとCLIの両方に対応しています。

## 特徴

- **使いやすいGUIインターフェース** - 直感的な操作で画像処理が可能
- **パワフルなコマンドラインツール** - バッチ処理やスクリプト自動化に最適
- **複数フォーマットサポート** - JPEG, PNG, WEBPなどの主要フォーマットに対応
- **アスペクト比の維持** - 画像の縦横比を保ちながらリサイズ可能
- **詳細なログ出力** - 処理状況と結果を分かりやすく表示

## KarukuResizeへの移行手順

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

## 開発

プルリクエストや機能提案は大歓迎です。

## ライセンス

MIT License
