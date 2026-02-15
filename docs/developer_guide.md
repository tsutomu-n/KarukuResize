# KarukuResize 開発者ガイド

このドキュメントは、現行コードベースの開発運用に必要な情報をまとめています。

## 開発環境セットアップ

```bash
git clone https://github.com/tsutomu-n/KarukuResize.git
cd KarukuResize
uv sync --group dev
```

任意で pre-commit を有効化:

```bash
uv run pre-commit install
```

## 日常コマンド

```bash
# テスト
uv run pytest -q

# Lint
uv run ruff check src tests

# 型チェック
uvx basedpyright src

# 一括フック実行
uv run pre-commit run --all-files
```

## エントリポイント

- GUI（推奨）: `uv run karuku-resizer`
- GUI（互換）: `uv run karukuresize-gui`
- CLI: `uv run karukuresize-cli`
- ビルド: `uv run karukuresize-build-exe`

## コード構成（主要）

- `src/karuku_resizer/gui_app.py`
  - GUI本体のアプリクラス
- `src/karuku_resizer/ui/`
  - レイアウト・ダイアログなどのUI分割モジュール
- `src/karuku_resizer/image_save_pipeline.py`
  - 保存処理とフォーマット関連ロジック
- `src/karuku_resizer/resize_core.py`
  - CLIおよび一部共通処理
- `src/karuku_resizer/runtime_logging.py`
  - ランタイムログ生成・保持管理
- `src/karuku_resizer/build_exe.py`
  - PyInstallerラッパー

## 開発上の注意

1. `gui_app_backup.py` はバックアップ用途で、実行経路には含めない
2. `resize_core.py` は現状型チェック対象から除外中（`pyrightconfig.json`）
3. ドキュメント更新時は README のリンク整合を必ず確認する
4. Windowsビルド仕様を変更した場合は `docs/BUILDING.md` と `docs/WINDOWS_GUIDE.md` を同時更新する

## テスト方針（現行）

- `tests/` 配下の現行テストのみを対象
- 旧 `tests/legacy` は削除済み
- 変更時は最低限、以下を通す
  - `uv run pytest -q`
  - `uv run ruff check src tests`
  - `uvx basedpyright src`

## ドキュメント運用

- ユーザー向け:
  - `README.md`
  - `docs/QUICK_START.md`
  - `docs/INSTALLATION.md`
  - `docs/WINDOWS_GUIDE.md`
  - `docs/WSL2_GUIDE.md`
  - `docs/BUILDING.md`
- 開発者向け:
  - `docs/developer_guide.md`
  - `docs/api_reference.md`

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
git clone https://github.com/tsutomu-n/KarukuResize.git
cd KarukuResize

# 依存関係を同期（開発依存を含む）
uv sync --group dev
```

### pre-commitのセットアップ

```bash
# pre-commitフックをインストール
pre-commit install
```
