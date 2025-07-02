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

## インストール

### 前提条件
- Python 3.12以上
- pip または uv（推奨）

### インストール手順

```bash
# リポジトリをクローン
git clone https://github.com/yourusername/KarukuResize.git
cd KarukuResize

# 依存関係をインストール（uvを推奨）
uv pip install -e .

# または通常のpipを使用
pip install -e .
```

## 使い方

### GUIモード

```bash
# インストール後
karukuresize-gui

# モジュールとして実行したい場合 (開発中など)
python -m karuku_resizer.gui_app
```

### コマンドラインモード

```bash
# インストール後
karukuresize-cli -s 入力フォルダ -d 出力フォルダ -w 1280 -q 85

# モジュールとして実行したい場合 (開発中など)
python -m karuku_resizer.resize_core -s 入力フォルダ -d 出力フォルダ -w 1280 -q 85
```

### 主なオプション

| オプション | 説明 | デフォルト |
|-----------|------|-----------|
| `-s, --source` | 入力元のディレクトリパス | 必須 |
| `-d, --dest` | 出力先のディレクトリパス | 必須 |
| `-w, --width` | リサイズ後の最大幅 | 1280 |
| `-q, --quality` | 画像の品質 (1-100) | 85 |
| `--dry-run` | 実際に保存せずシミュレート | False |
| `--resume` | 既存ファイルをスキップ | False |
| `--debug` | デバッグモード | False |

## 機能詳細

### コア機能（共通）
- 複数の画像形式サポート（JPEG, PNG, WEBP, GIF, BMP, TIFF）
- 高度な圧縮アルゴリズム
- アスペクト比の保持
- Windows長パス対応（260文字制限の回避）
- 日本語ファイル名・パス対応
- 詳細なログ記録
- 処理進捗の表示

### CLI機能
- バッチ処理機能（複数ファイルの一括処理）
- コマンドライン引数によるカスタマイズ
- 処理の中断・再開機能
- 処理統計情報の表示（ファイルサイズ削減率など）
- Ctrl+C によるグレースフル終了

### GUI機能
- モダンなインターフェース（CustomTkinter使用）
- **単一画像処理モード**
  - ファイル選択ダイアログ
  - 出力先設定
  - 出力形式選択（JPEG/PNG/WEBP）
  - リサイズモード選択
  - 品質/圧縮率スライダー
  - EXIFデータ処理設定
- **バッチ処理モード**（実装完了！）
  - フォルダ選択ダイアログ
  - 出力形式一括設定
  - リサイズモード（幅/高さ/長辺/短辺/パーセント）
  - 品質設定（JPEG/WEBP）
  - WebP用ロスレスオプション
  - 再帰的処理オプション
- リアルタイムプログレスバー
- 詳細ログ表示
- 処理のキャンセル機能

## 環境別の使い方

### Windows
ネイティブで動作します。GUI・CLI共に完全サポート。

### WSL2
- **CLI推奨** - 最も安定して動作
- **GUI使用時** - [WSL2ガイド](./WSL2_GUIDE.md)参照（Windows側での実行を推奨）

### macOS/Linux
すべての機能が利用可能です。

## 使用例

### Web用に画像を最適化
```bash
karukuresize-cli -s photos -d web_photos -w 1280 -q 85
```

### サムネイル作成
```bash
karukuresize-cli -s images -d thumbnails -w 300 -q 80
```

### 高品質で保存
```bash
karukuresize-cli -s original -d high_quality -w 1920 -q 95
```

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

プルリクエストや機能提案は大歓迎です。コード品質維持のため、pre-commitフックを使用したruffによる自動チェックを導入しています。

### 開発環境のセットアップ

```bash
# 開発モードでインストール
uv pip install -e .

# pre-commitフックをインストール
pre-commit install
```

## ライセンス

MIT License