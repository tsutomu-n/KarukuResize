# KarukuResize API リファレンス

## 目次
- [resize_core モジュール](#resize_core-モジュール)
- [resize_images モジュール](#resize_images-モジュール)
- [resize_images_gui モジュール](#resize_images_gui-モジュール)

---

## resize_core モジュール

画像処理の中核となる機能を提供するモジュール。

### 主要関数

#### `resize_and_compress_image()`

画像をリサイズして圧縮します。

```python
def resize_and_compress_image(
    source_path: Union[str, Path],
    dest_path: Union[str, Path],
    target_width: int,
    quality: int,
    format: str = "original",
    exif_handling: str = "keep",
    balance: int = 5,
    webp_lossless: bool = False,
    dry_run: bool = False,
) -> tuple[bool, bool, int | None]
```

**パラメータ:**
- `source_path`: 入力画像のパス
- `dest_path`: 出力画像のパス
- `target_width`: 目標の幅（ピクセル、1以上の整数）
- `quality`: 圧縮品質（1-100の整数）
- `format`: 出力形式（'original', 'jpeg', 'png', 'webp'）
- `exif_handling`: EXIFメタデータの取り扱い（'keep': 維持, 'remove': 削除）
- `balance`: 圧縮と品質のバランス（1-10、未使用）
- `webp_lossless`: WebPロスレス圧縮を使用するか
- `dry_run`: 実際にファイルを保存せずシミュレートする

**戻り値:**
- `tuple[bool, bool, int | None]`: (成功フラグ, スキップフラグ, ファイルサイズKB)
- ドライランモードでは: `tuple[tuple, tuple, int]`: (元のサイズ, 新しいサイズ, 推定ファイルサイズ)

**使用例:**
```python
success, skipped, size_kb = resize_and_compress_image(
    source_path="input.jpg",
    dest_path="output.jpg",
    target_width=1280,
    quality=85
)
```

#### `find_image_files()`

指定ディレクトリから画像ファイルを再帰的に検索します。

```python
def find_image_files(directory: Union[str, Path]) -> list[Path]
```

**パラメータ:**
- `directory`: 検索対象のディレクトリパス

**戻り値:**
- `list[Path]`: 見つかった画像ファイルのパスリスト

**対応フォーマット:**
- JPEG (.jpg, .jpeg)
- PNG (.png)
- WebP (.webp)
- GIF (.gif)
- BMP (.bmp)
- TIFF (.tiff, .tif)

#### `sanitize_filename()`

ファイル名を安全な形式に変換します。

```python
def sanitize_filename(filename: str, max_length: int = 255) -> str
```

**パラメータ:**
- `filename`: 元のファイル名
- `max_length`: 最大長（デフォルト: 255）

**戻り値:**
- `str`: 安全な形式に変換されたファイル名

**機能:**
- Windowsで使用できない文字を置換
- 予約語の処理（CON, AUX, NUL等）
- Unicode正規化（NFD → NFC）
- 最大長の制限

#### `format_file_size()`

ファイルサイズを人間が読みやすい形式にフォーマットします。

```python
def format_file_size(size_bytes: int) -> str
```

**パラメータ:**
- `size_bytes`: バイト単位のサイズ

**戻り値:**
- `str`: フォーマットされたサイズ（例: "1.5 MB"）

#### `get_destination_path()`

ソースパスから出力パスを生成します。

```python
def get_destination_path(
    source_path: Path,
    source_dir: Union[str, Path],
    dest_dir: Union[str, Path]
) -> Path
```

**パラメータ:**
- `source_path`: ソースファイルのパス
- `source_dir`: ソースディレクトリのルート
- `dest_dir`: 出力ディレクトリのルート

**戻り値:**
- `Path`: 出力ファイルのパス（ディレクトリ構造を維持）

#### `normalize_path()`

パスを正規化してPathオブジェクトとして返します。

```python
def normalize_path(path: Union[str, Path]) -> Path
```

**パラメータ:**
- `path`: 正規化するパス

**戻り値:**
- `Path`: 正規化されたPathオブジェクト

**機能:**
- Windows長パス対応（\\\\?\\ プレフィックス）
- Unicode正規化
- 相対パスの解決

### エラーハンドリング関数

#### `get_japanese_error_message()`

エラーコードから日本語のエラーメッセージを取得します。

```python
def get_japanese_error_message(error: Exception) -> str
```

**パラメータ:**
- `error`: 例外オブジェクト

**戻り値:**
- `str`: 日本語のエラーメッセージ

**対応エラー:**
- FileNotFoundError
- PermissionError
- OSError（各種エラーコード）
- IOError
- MemoryError
- その他の一般的なエラー

---

## resize_images モジュール

コマンドラインインターフェース（CLI）を提供するモジュール。

### 主要関数

#### `main()`

CLIのエントリーポイント。

```python
def main() -> int
```

**戻り値:**
- `int`: 終了コード（0: 成功、1: エラー）

### コマンドライン引数

```bash
python resize_images.py [OPTIONS]
```

**必須引数:**
- `-s, --source`: ソースディレクトリのパス
- `-d, --dest`: 出力ディレクトリのパス

**オプション引数:**
- `-w, --width`: リサイズ後の最大幅（デフォルト: 1280）
- `-q, --quality`: JPEG品質（1-100、デフォルト: 85）
- `--dry-run`: 実際に保存せずシミュレート
- `--resume`: 既存ファイルをスキップ
- `--log-level`: ログレベル（DEBUG, INFO, WARNING, ERROR, CRITICAL）
- `--check-disk`: 処理前にディスク容量を確認
- `--debug`: デバッグモードを有効化

### 処理フロー

1. コマンドライン引数の解析
2. 入力検証
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