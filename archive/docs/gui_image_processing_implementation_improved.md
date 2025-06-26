# KarukuResize GUI画像処理実装計画（改善版）

## 1. 実装の基本方針

### 1.1 ユーザー中心設計
- **目標**: 技術的な実装よりも、ユーザー体験を最優先する
- **成功基準**: 日本語環境のWindows11で直感的に操作でき、エラーメッセージが理解しやすいこと

### 1.2 段階的実装とテスト
- 小さな機能単位で実装し、各段階でテストを行う
- 1つの機能が完成するごとにユーザーフィードバックを得る

### 1.3 堅牢性と拡張性
- 日本語環境特有の問題に対応する堅牢なエラー処理
- 将来の機能拡張を見据えた設計

## 2. ユーザーストーリーと優先順位

### 2.1 最優先機能（MVP）
1. **単一画像のリサイズ**
   - ユーザーは単一画像を選択し、簡単な設定でリサイズできる
   - 処理中の進捗が表示され、結果が明確にわかる

2. **基本的なエラー処理**
   - ファイルが見つからない場合のエラーメッセージ
   - 権限エラーの適切な処理
   - 処理失敗時の明確なフィードバック

### 2.2 次の優先機能
1. **処理結果の確認**
   - 処理完了後に出力フォルダを開く機能
   - 処理前後のサイズ比較表示

2. **設定の永続化**
   - 最後に使用した設定を次回起動時に復元
   - よく使う設定をプリセットとして保存

### 2.3 追加機能
1. **バッチ処理**
   - 複数画像の一括処理
   - キューによる順次処理と進捗表示

2. **高度な処理オプション**
   - トリミング、回転機能
   - フィルタ適用オプション

## 3. 技術的実装計画

### 3.1 基本画像処理機能（第1フェーズ）

#### 3.1.1 現状の理解
現在は以下のダミー処理が実装されています：
```python
self.after(2000, lambda: self.finish_resize_process(success=True, message="ダミー処理成功！"))
```

#### 3.1.2 実装計画
`start_resize_process()`メソッドを以下のように修正します：

```python
def start_resize_process(self):
    self.add_log_message("リサイズ処理を開始します...")
    if self.resize_start_button:
        self.resize_start_button.configure(state="disabled")
    if self.resize_cancel_button:
        self.resize_cancel_button.configure(state="normal")
    self.update_progress(0.1)

    # 入力検証（既存のコード）
    # ...

    # スレッドで処理を実行
    self.processing_thread = threading.Thread(
        target=self._process_image_thread,
        args=(source_path, dest_path, core_resize_mode, resize_value, keep_aspect_ratio, core_output_format, quality),
        daemon=True
    )
    self.processing_thread.start()

def _process_image_thread(self, source_path, dest_path, resize_mode, resize_value, keep_aspect_ratio, output_format, quality):
    """画像処理をバックグラウンドで実行するスレッド"""
    try:
        # 進捗更新用コールバック関数
        def progress_callback(progress):
            # UIスレッドでの更新を少ない頻度で行う（パフォーマンス向上）
            # 進捗0.3から0.9の間で更新（前後の処理は別に表示）
            scaled_progress = 0.3 + (progress * 0.6)
            self.after(0, lambda: self.update_progress(scaled_progress))

        # 実際の画像処理を呼び出し
        # resize_core.pyに進捗コールバックを追加した場合
        self.after(0, lambda: self.update_progress(0.3))  # 処理開始を30%として表示

        success, output_path, message = resize_and_compress_image(
            source_path,
            resize_mode=resize_mode,
            resize_value=resize_value,
            keep_aspect_ratio=keep_aspect_ratio,
            output_format=output_format,
            quality=quality,
            dest_path=dest_path,
            progress_callback=progress_callback  # 進捗コールバック
        )

        # UIスレッドで結果を表示
        self.after(0, lambda: self._handle_process_result(success, output_path, message))

    except Exception as e:
        # UIスレッドでエラーを表示
        self.after(0, lambda: self._handle_process_error(e))

def _handle_process_result(self, success, output_path, message):
    """処理結果をUIに反映する"""
    if success:
        # 成功時：出力ファイルのサイズ情報を表示
        file_size = Path(output_path).stat().st_size
        readable_size = self._get_readable_file_size(file_size)
        self.add_log_message(f"処理完了: {output_path}")
        self.add_log_message(f"出力ファイルサイズ: {readable_size}")

        # 出力フォルダを開くボタンを表示
        output_dir = Path(output_path).parent
        self.show_open_folder_button(output_dir)

        self.finish_resize_process(success=True, message=message)
    else:
        self.add_log_message(f"処理失敗: {message}")
        self.finish_resize_process(success=False, message=message)

def _handle_process_error(self, error):
    """例外エラーをユーザーフレンドリーなメッセージに変換"""
    error_message = str(error)
    user_message = "エラーが発生しました"

    if isinstance(error, FileNotFoundError):
        user_message = "ファイルが見つかりません。ファイルが存在するか確認してください。"
    elif isinstance(error, PermissionError):
        user_message = "ファイルへのアクセス権限がありません。別の場所を指定するか、管理者権限で実行してください。"
    elif "too long" in error_message.lower():
        user_message = "ファイルパスが長すぎます。より短いパスを使用するか、ファイル名を短くしてください。"

    self.add_log_message(f"エラー: {user_message}")
    self.add_log_message(f"詳細: {error_message}")
    self.finish_resize_process(success=False, message=user_message)
```

### 3.2 進捗表示とリソース管理（第2フェーズ）

#### 3.2.1 進捗表示の改善
`resize_core.py`の`resize_and_compress_image`関数に進捗コールバックを追加します：

```python
def resize_and_compress_image(source_path, resize_mode, resize_value, keep_aspect_ratio=True,
                             output_format="original", quality=85, dest_path=None,
                             progress_callback=None):
    """画像のリサイズと圧縮を行う（進捗コールバック対応版）"""

    try:
        # 処理開始
        if progress_callback:
            progress_callback(0.0)  # 0%

        # 画像を開く
        img = Image.open(source_path)

        if progress_callback:
            progress_callback(0.2)  # 20%

        # リサイズ処理
        # ...

        if progress_callback:
            progress_callback(0.5)  # 50%

        # 保存処理
        # ...

        if progress_callback:
            progress_callback(0.9)  # 90%

        # 成功情報を返す
        # ...

        if progress_callback:
            progress_callback(1.0)  # 100%

        return True, dest_path, "処理完了"

    except Exception as e:
        return False, None, str(e)
```

#### 3.2.2 メモリと一時ファイルの管理
大きな画像処理時のメモリ管理を改善します：

```python
def resize_and_compress_image(...):
    try:
        # 大きな画像ファイルの場合、メモリ使用量を制限
        with Image.open(source_path) as img:
            # メモリ消費を抑えるため、処理中は最小限のデータだけ保持
            original_format = img.format
            # ...処理...

            # 処理後は明示的に変数をクリア
            del img
            # 必要に応じてガベージコレクションを呼び出し
            import gc
            gc.collect()

        return True, dest_path, "処理完了"
    except Exception as e:
        return False, None, str(e)
```

### 3.3 エラー処理と国際化（第3フェーズ）

#### 3.3.1 強化されたエラー処理
日本語環境特有の問題を検出して対応します：

```python
def sanitize_filename(filename):
    """Windows環境でも安全なファイル名に変換（拡張版）"""
    # 基本的な禁止文字の置換
    unsafe_chars = '<>:"/\\|?*\\0'
    safe_name = filename
    for char in unsafe_chars:
        safe_name = safe_name.replace(char, '_')

    # 長すぎるファイル名の処理（Windowsの260文字制限対応）
    if len(safe_name) > 200:  # 余裕を持たせる
        name, ext = os.path.splitext(safe_name)
        safe_name = name[:200-len(ext)] + ext

    # 先頭と末尾のスペースやピリオドを削除（Windowsでの問題回避）
    safe_name = safe_name.strip('. ')

    # 予約語をチェック
    reserved_names = {'CON', 'PRN', 'AUX', 'NUL',
                     'COM1', 'COM2', 'COM3', 'COM4', 'COM5', 'COM6', 'COM7', 'COM8', 'COM9',
                     'LPT1', 'LPT2', 'LPT3', 'LPT4', 'LPT5', 'LPT6', 'LPT7', 'LPT8', 'LPT9'}
    name_without_ext = os.path.splitext(safe_name)[0].upper()
    if name_without_ext in reserved_names:
        name, ext = os.path.splitext(safe_name)
        safe_name = f"{name}_file{ext}"

    return safe_name
```

#### 3.3.2 国際化対応の基盤整備
メッセージを分離して将来の多言語対応を容易にします：

```python
# messages.py
class Messages:
    """メッセージ定義（将来の国際化対応）"""

    # 日本語メッセージ
    JA = {
        'app_title': "画像処理ツール",
        'resize_tab': "リサイズ",
        'compress_tab': "圧縮",
        'batch_tab': "一括処理",
        'input_file': "入力ファイル:",
        'output_dir': "出力先フォルダ:",
        'select_button': "選択...",
        'start_button': "処理開始",
        'cancel_button': "中断",
        'error_prefix': "エラー: ",
        # ...他のメッセージ...
    }

    # 将来的に他の言語を追加
    # EN = { ... }

    @classmethod
    def get(cls, key, lang='JA'):
        """指定された言語のメッセージを取得"""
        lang_dict = getattr(cls, lang, cls.JA)
        return lang_dict.get(key, f"Missing: {key}")
```

### 3.4 設定の永続化とプリセット（第4フェーズ）

```python
import json

class ConfigManager:
    """設定の保存と読み込みを管理"""

    def __init__(self, config_file="settings.json"):
        self.config_file = config_file
        self.default_config = {
            'last_input_dir': "",
            'last_output_dir': "",
            'resize_mode': "パーセント",
            'resize_value': "50",
            'keep_aspect_ratio': True,
            'output_format': "元のフォーマットを維持",
            'quality': 85,
            'presets': []
        }

    def load_config(self):
        """設定を読み込む"""
        try:
            if Path(self.config_file).exists():
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            return self.default_config.copy()
        except Exception:
            return self.default_config.copy()

    def save_config(self, config):
        """設定を保存する"""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=2)
            return True
        except Exception:
            return False

    def save_current_settings(self, app):
        """現在の設定を保存"""
        config = self.load_config()

        # GUIから現在の設定を取得
        if app.resize_input_file_entry.get():
            config['last_input_dir'] = str(Path(app.resize_input_file_entry.get()).parent)
        if app.resize_output_dir_entry.get():
            config['last_output_dir'] = app.resize_output_dir_entry.get()

        config['resize_mode'] = app.resize_mode_var.get()
        config['resize_value'] = app.resize_value_entry.get()
        config['keep_aspect_ratio'] = bool(app.resize_aspect_ratio_var.get())
        config['output_format'] = app.resize_output_format_var.get()
        config['quality'] = app.resize_quality_var.get()

        self.save_config(config)

    def apply_settings(self, app):
        """保存された設定をGUIに適用"""
        config = self.load_config()

        # ディレクトリ設定
        if config['last_output_dir']:
            app.resize_output_dir_entry.delete(0, "end")
            app.resize_output_dir_entry.insert(0, config['last_output_dir'])

        # リサイズ設定
        app.resize_mode_var.set(config['resize_mode'])
        app.on_resize_mode_change(config['resize_mode'])

        app.resize_value_entry.delete(0, "end")
        app.resize_value_entry.insert(0, config['resize_value'])

        app.resize_aspect_ratio_var.set(config['keep_aspect_ratio'])

        app.resize_output_format_var.set(config['output_format'])
        app.on_output_format_change(config['output_format'])

        app.resize_quality_var.set(config['quality'])
        app.update_quality_label(config['quality'])
```

## 4. 改善されたテスト計画

### 4.1 単体テスト
各コンポーネントごとに独立したテストを実施します：

1. **`sanitize_filename`関数のテスト**
   - 日本語ファイル名、絵文字を含む名前、長いパス名などでテスト
   - Windowsの予約語を含む名前のテスト
   - 境界ケース（最大長、空の文字列など）のテスト

2. **画像処理関数のテスト**
   - 各リサイズモード（パーセント、幅、高さ）のテスト
   - 出力フォーマット変換のテスト
   - 極端なサイズ（非常に大きい/小さい）の画像処理テスト

### 4.2 結合テスト
GUIと処理ロジックの連携をテストします：

1. **GUIからの画像処理フロー**
   - 正常系：ファイル選択から処理完了までの一連の流れ
   - 異常系：無効なファイル、アクセス権限エラーなどの処理

2. **スレッド処理と進捗表示**
   - 処理中のUI応答性テスト
   - キャンセル機能のテスト

### 4.3 ユーザー受け入れテスト
実際のユーザーに近い環境でテストします：

1. **Windows11日本語環境での動作確認**
   - 日本語パスを含むファイル操作
   - 長いパス名の処理
   - 様々なDPI設定での表示確認

2. **実際のユースケース**
   - 写真の一括リサイズ
   - 高解像度画像の処理性能

## 5. 改善された実装スケジュール

### フェーズ1: 基本機能実装（3日）
- Day 1: 基本的な画像処理機能の統合
- Day 2: スレッド処理と進捗表示の実装
- Day 3: 基本的なエラー処理と初期テスト

### フェーズ2: ユーザー体験向上（2日）
- Day 4: 結果確認機能と設定の永続化
- Day 5: エラーメッセージの改善とユーザーテスト

### フェーズ3: 拡張機能（3日）
- Day 6: バッチ処理機能の実装
- Day 7: 高度な処理オプションの追加
- Day 8: プリセット機能と国際化基盤の整備

### フェーズ4: 最終調整（2日）
- Day 9: パフォーマンス最適化とリソース管理
- Day 10: 最終テストとドキュメント作成

## 6. 実装優先順位と段階的リリース

### 第1リリース（MVP）
- 単一画像の基本リサイズ機能
- シンプルなエラー処理
- スレッド処理による非ブロッキングUI

### 第2リリース
- 設定の永続化
- 処理結果確認機能
- 拡張されたエラー処理

### 第3リリース
- バッチ処理機能
- プリセット機能
- パフォーマンス最適化

### 最終リリース
- 高度な処理オプション
- 国際化対応
- 完全なドキュメント
