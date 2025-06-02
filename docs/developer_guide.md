# KarukuResize 開発者ガイド

このドキュメントはKarukuResizeの開発者向け技術情報を提供します。

## 技術スタック

KarukuResizeは以下の技術スタックで構築されています：

- **Python**: 3.12以上
- **パッケージ管理**: uv
- **主要依存関係**:
  - Pillow: 画像処理
  - customtkinter: モダンGUI
  - loguru: 高度なロギング
  - tqdm: プログレスバー
- **コード品質ツール**:
  - ruff: 静的解析とフォーマット
  - pre-commit: コミット前チェック

## プロジェクト構造

```
KarukuResize/
├── karukuresize/
│   ├── __init__.py
│   ├── __main__.py
│   ├── core.py       # コア処理ロジック
│   ├── cli.py        # コマンドラインインターフェース
│   └── gui.py        # グラフィカルユーザーインターフェース
├── docs/             # ドキュメント
├── log/              # ログ出力ディレクトリ
├── pyproject.toml    # プロジェクト構成と依存関係
└── README.md         # プロジェクト概要
```

## コアモジュールの概要

### core.py

このモジュールは画像処理の中核機能を提供します：

- 画像のリサイズと圧縮
- ファイルパスの正規化（Windows長パス対応）
- エラーハンドリングとリトライロジック
- ディスク容量チェック
- 処理進捗の保存と再開

## 画像処理アルゴリズム

### リサイズと圧縮の流れ

`resize_and_compress_image`関数は画像のリサイズと圧縮の中核処理を行います。一般的な処理フローは以下の通りです：

1. **入力画像のチェックと前処理**
   - パス正規化（Windows長パス対応）
   - ファイルの存在確認
   - 画像フォーマットの検証
   - EXIFデータの処理（保持、削除、コピー）

2. **リサイズ処理**
   - 原画像のアスペクト比の計算
   - 新しいサイズの計算（幅を基準に高さを比例計算）
   - PILの`Image.resize()`メソッドを使用したリサイズ
   - 高品質なリサイズのために`LANCZOS`レサンプリングフィルターを使用

3. **圧縮品質の最適化**
   - ユーザー指定の品質設定をバランスパラメータで調整
   - 出力フォーマットに応じた品質設定の適用
   - WebP形式の場合はロスレスオプションのサポート

4. **安全なファイル保存**
   - 一時ファイルを使用した原子的な保存処理
   - ファイル操作の失敗時に自動リトライ
   - ファイルサイズの削減率計算
   - 最適化の結果レポート

### リサイズアルゴリズムの詳細

```python
# リサイズ処理の核心部分（簡略化したコード）
# 1. 原画像のサイズを取得
width, height = img.size

# 2. アスペクト比を計算して新しい高さを決定
aspect_ratio = height / width
new_height = int(target_width * aspect_ratio)

# 3. 高品質なリサイズ処理
# LANCZOS（ランチョス）レサンプリングは高品質な画像縮小に適しています
resized_img = img.resize((target_width, new_height), Image.LANCZOS)
```

### 圧縮品質の最適化

KarukuResizeではファイル形式ごとに適切な品質設定を行います：

1. **JPEG形式**
   - 品質設定（quality）: 1-100の範囲
   - 高い値で高品質な画像、低い値で高圧縮率
   - デフォルト設定は85（高品質）
   - 高度な設定：optimize=Trueで追加最適化

2. **PNG形式**
   - ロスレス圧縮を使用
   - 圧縮レベル（compression_level）: 0-9の範囲
   - 高い値で高圧縮率、低い値で高速処理
   - デフォルト設定は6（バランス重視）

3. **WebP形式**
   - ロスレスとロッシーの両モードをサポート
   - ロッシーモード: 品質設定（0-100）
   - ロスレスモード: lossless=Trueで有効化
   - プリセットオプションによる圧縮調整

### バランスパラメータによる調整

ユーザー指定の品質設定をバランスパラメータ（1-10）で微調整します：

```python
# バランスパラメータによる品質調整（簡略化したコード）
def adjust_quality_by_balance(base_quality, balance, output_format):
    # バランス値を1-10の範囲に制限
    balance = max(1, min(balance, 10))

    # バランス値が5の場合は元の設定をそのまま使用
    if balance == 5:
        return base_quality

    if output_format == "JPEG" or output_format == "WEBP":
        # 1: 最高圧縮率優先【10: 最高品質優先
        # バランスが5より低い場合は圧縮率を重視
        if balance < 5:
            # 5から距離に応じて品質を下げる
            quality_reduction = (5 - balance) * 10
            return max(1, base_quality - quality_reduction)
        else:
            # 5から距離に応じて品質を上げる
            quality_increase = (balance - 5) * 5
            return min(100, base_quality + quality_increase)

    # PNGの場合は圧縮レベルを0-9の範囲で調整
    elif output_format == "PNG":
        # バランスの逆転（1→最高圧縮、そのため9）
        return abs(10 - balance)
```

### ファイル保存の安全性確保

一時ファイルを使用した原子的な保存処理でデータ破損を防止します：

1. 一時ファイルにまず保存
2. 保存が成功した場合のみ、最終的な出力先に移動
3. ファイル操作の失敗時に自動リトライロジックを適用

```python
# 安全なファイル保存の例（簡略化したコード）
def save_with_atomic_operation(image, dest_path, **save_options):
    # 一時ファイルパスを生成
    temp_path = str(dest_path) + ".tmp"

    try:
        # 一時ファイルに保存
        image.save(temp_path, **save_options)

        # 保存成功後、最終的なパスに移動
        shutil.move(temp_path, str(dest_path))
        return True

    except Exception as e:
        # エラー発生時は一時ファイルをクリーンアップ
        if os.path.exists(temp_path):
            os.remove(temp_path)
        raise e
```
- エラーハンドリングとリトライロジック
- ディスク容量チェック
- 処理進捗の保存と再開

### cli.py

コマンドラインインターフェースを実装：

- 引数解析
- ログ設定
- ファイル探索と処理
- 進捗表示
- 処理結果レポート

### gui.py

GUIインターフェースを実装：

- マルチタブインターフェース
- 設定コントロール
- ファイル/フォルダ選択
- リアルタイム進捗表示
- マルチスレッド処理

## 開発環境のセットアップ

### 前提条件

- Python 3.12以上
- uvのインストール

### 開発用インストール

```bash
# リポジトリのクローン
git clone https://github.com/yourusername/KarukuResize.git
cd KarukuResize

# 開発モードでインストール
uv add -e .

# 必要な依存関係をインストール
uv add pillow customtkinter tqdm loguru

# 開発ツールをインストール
uv add --dev ruff pre-commit pytest
```

### pre-commitのセットアップ

```bash
# pre-commitフックをインストール
pre-commit install
```
