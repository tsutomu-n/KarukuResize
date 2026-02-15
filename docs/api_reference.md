# KarukuResize API リファレンス

このドキュメントは、現行実装で外部利用しやすいAPIとCLI仕様を簡潔にまとめたものです。

## エントリポイント

`pyproject.toml` の `project.scripts`:

- `karuku-resizer` → `karuku_resizer.gui_app:main`
- `karukuresize-gui` → `karuku_resizer.gui_app:main`（互換）
- `karukuresize-cli` → `karuku_resizer.resize_core:main`
- `karukuresize-build-exe` → `karuku_resizer.build_exe:main`

## `karuku_resizer.resize_core`（CLI/共通）

### CLI引数（`_build_arg_parser`）

| 引数 | 説明 | 既定値 |
|---|---|---|
| `-s, --source` | 入力フォルダ | 必須 |
| `-d, --dest` | 出力フォルダ | 必須 |
| `-w, --width` | リサイズ後の最大幅(px) | `1280` |
| `-q, --quality` | JPEG/WEBP品質 | `85` |
| `-f, --format` | `jpeg/png/webp` | `jpeg` |
| `--recursive/--no-recursive` | 再帰探索 | `--recursive` |
| `--extensions` | 対象拡張子（カンマ区切り） | `jpg,jpeg,png` |
| `--failures-file` | 失敗一覧JSON保存先 | 空文字（無効） |
| `--dry-run` | 保存せずシミュレーション | `False` |
| `--json` | 実行サマリをJSON出力 | `False` |
| `-v, --verbose` | ログ詳細度 | `0` |

### 主な公開関数

- `resize_and_compress_image(...)`
  - 画像1件のリサイズ/保存処理
- `find_image_files(source_dir) -> list[Path]`
  - 画像ファイル探索
- `format_file_size(size_in_bytes) -> str`
  - サイズ表示用フォーマット
- `setup_logging(...)`
  - CLIロギング設定（`src/logs` または `KARUKU_LOG_DIR`）

## `karuku_resizer.runtime_logging`

GUIランタイムログの保存先・保持ポリシー管理。

### 主な公開関数

- `get_default_log_dir(app_name="KarukuResize") -> Path`
  - OS標準ログディレクトリを返す
- `create_run_log_artifacts(...) -> RunLogArtifacts`
  - 実行単位のログ/サマリファイルパスを生成
- `prune_run_files(...) -> list[Path]`
  - 保持ポリシーを超える古いログを削除
- `write_run_summary(summary_path, payload) -> None`
  - 実行サマリJSONを保存

## `karuku_resizer.image_save_pipeline`

GUI保存処理で使う画像保存基盤。

### 主な型/関数

- `SaveOptions`
- `SaveResult`
- `SaveFormat`
- `save_image(...)`
- `resolve_output_format(...)`
- `destination_with_extension(...)`

## 注意

- `src/karuku_resizer/gui_app_backup.py` はバックアップ用で、実行経路のAPIとはみなさない
- CLIとGUIは内部実装を一部共有しているが、入出力仕様はそれぞれのエントリポイントを基準に扱う
3. 画像ファイルの検索
4. 各ファイルの処理（進捗表示付き）
5. 結果サマリーの表示

---

## resize_images_gui モジュール

グラフィカルユーザーインターフェース（GUI）を提供するモジュール。

### 主要クラス

#### `App`

CustomTkinterベースのGUIアプリケーション。

```python
class App(ctk.CTk):
    def __init__(self):
        super().__init__()
```

### 主要メソッド

#### `start_batch_process()`

一括処理を開始します。

```python
def start_batch_process(self) -> None
```

**機能:**
- 入力値の検証
- 処理パラメータの準備
- ワーカースレッドの起動

#### `process_batch_worker()`

バッチ処理のワーカースレッド。

```python
def process_batch_worker(self, params: dict) -> None
```

**パラメータ:**
- `params`: 処理パラメータの辞書
  - `input_folder`: 入力フォルダパス
  - `output_folder`: 出力フォルダパス
  - `resize_mode`: リサイズモード
  - `resize_value`: リサイズ値
  - `keep_aspect_ratio`: アスペクト比維持
  - `enable_compression`: 圧縮有効化
  - `output_format`: 出力フォーマット
  - `jpeg_quality`: JPEG品質
  - `webp_quality`: WebP品質
  - `webp_lossless`: WebPロスレス

#### `cancel_batch_process()`

実行中のバッチ処理を中断します。

```python
def cancel_batch_process(self) -> None
```

### GUIの機能

**タブ構成:**
1. **リサイズタブ**: 単一ファイルの処理
2. **圧縮タブ**: 圧縮のみの処理（未実装）
3. **一括処理タブ**: フォルダ単位のバッチ処理

**リサイズモード:**
- 指定なし
- 幅を指定
- 高さを指定
- 縦横最大
- パーセント指定

**出力フォーマット:**
- オリジナルを維持
- JPEG
- PNG
- WebP

**その他の機能:**
- プログレスバー表示
- 詳細ログ表示
- 処理の中断機能
- 日本語フォント対応
- カスタムライトテーマ

---

## 共通定数・設定

### サポートされる画像形式

```python
SUPPORTED_FORMATS = {".jpg", ".jpeg", ".png", ".webp", ".gif", ".bmp", ".tiff", ".tif"}
```

### Windowsの予約語

```python
WINDOWS_RESERVED_NAMES = {
    "CON", "PRN", "AUX", "NUL",
    "COM1", "COM2", "COM3", "COM4", "COM5", "COM6", "COM7", "COM8", "COM9",
    "LPT1", "LPT2", "LPT3", "LPT4", "LPT5", "LPT6", "LPT7", "LPT8", "LPT9"
}
```

### デフォルト設定

- デフォルト幅: 1280ピクセル
- デフォルト品質: 85
- 最大ファイル名長: 255文字（拡張子を除いて250文字）
