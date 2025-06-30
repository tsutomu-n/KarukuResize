"""
リサイズタブのViewModel
"""
from typing import Optional, Dict, Any, List
import threading
from pathlib import Path
import sys

# プロジェクトルートをPythonパスに追加
project_root = Path(__file__).parent.parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from .base_view_model import BaseViewModel
from ...models.resize_settings import ResizeSettings, BatchSettings, ProcessingResult
from ...services.image_service import ImageService
from ..utils.constants import ResizeMode, OutputFormat, PROCESSING, ProcessingMode


class ResizeViewModel(BaseViewModel):
    """リサイズ機能のViewModel"""
    
    def __init__(self, image_service: Optional[ImageService] = None):
        super().__init__()
        self.image_service = image_service or ImageService()
        self._settings = ResizeSettings()
        self._batch_settings = BatchSettings()
        self._current_thread: Optional[threading.Thread] = None
        self._processing_results: List[ProcessingResult] = []
        
    def initialize(self) -> None:
        """初期化処理"""
        # デフォルト設定を適用
        self.processing_mode = ProcessingMode.SINGLE
        self.resize_mode = ResizeMode.LONGEST_SIDE
        self.resize_value = PROCESSING.DEFAULT_RESIZE_VALUE
        self.quality = PROCESSING.DEFAULT_QUALITY
        self.output_format = OutputFormat.ORIGINAL
        self.maintain_aspect_ratio = True
        self.preserve_metadata = True
        self._is_initialized = True
        
    def cleanup(self) -> None:
        """クリーンアップ処理"""
        self.cancel_processing()
        self.unbind_all()
    
    # プロパティ定義
    @property
    def processing_mode(self) -> str:
        """処理モード（単一/バッチ）"""
        return self._get_property("processing_mode", ProcessingMode.SINGLE)
    
    @processing_mode.setter
    def processing_mode(self, value: str) -> None:
        self._set_property("processing_mode", value)
        self._update_settings()
    
    @property
    def input_path(self) -> str:
        """入力パス（ファイルまたはディレクトリ）"""
        return self._get_property("input_path", "")
    
    @input_path.setter
    def input_path(self, value: str) -> None:
        self._set_property("input_path", value)
        self._validate_input()
    
    @property
    def output_directory(self) -> str:
        """出力ディレクトリ"""
        return self._get_property("output_directory", "")
    
    @output_directory.setter
    def output_directory(self, value: str) -> None:
        self._set_property("output_directory", value)
    
    @property
    def resize_mode(self) -> str:
        """リサイズモード"""
        return self._get_property("resize_mode", ResizeMode.NONE)
    
    @resize_mode.setter
    def resize_mode(self, value: str) -> None:
        self._set_property("resize_mode", value)
        self._update_settings()
    
    @property
    def resize_value(self) -> int:
        """リサイズ値"""
        return self._get_property("resize_value", 0)
    
    @resize_value.setter
    def resize_value(self, value: int) -> None:
        self._set_property("resize_value", max(0, value))
        self._update_settings()
    
    @property
    def quality(self) -> int:
        """品質（1-100）"""
        return self._get_property("quality", PROCESSING.DEFAULT_QUALITY)
    
    @quality.setter
    def quality(self, value: int) -> None:
        value = max(PROCESSING.MIN_QUALITY, min(PROCESSING.MAX_QUALITY, value))
        self._set_property("quality", value)
        self._update_settings()
    
    @property
    def output_format(self) -> str:
        """出力フォーマット"""
        return self._get_property("output_format", OutputFormat.ORIGINAL)
    
    @output_format.setter
    def output_format(self, value: str) -> None:
        self._set_property("output_format", value)
        self._update_settings()
    
    @property
    def maintain_aspect_ratio(self) -> bool:
        """アスペクト比を維持"""
        return self._get_property("maintain_aspect_ratio", True)
    
    @maintain_aspect_ratio.setter
    def maintain_aspect_ratio(self, value: bool) -> None:
        self._set_property("maintain_aspect_ratio", value)
        self._update_settings()
    
    @property
    def preserve_metadata(self) -> bool:
        """メタデータを保持"""
        return self._get_property("preserve_metadata", True)
    
    @preserve_metadata.setter
    def preserve_metadata(self, value: bool) -> None:
        self._set_property("preserve_metadata", value)
        self._update_settings()
    
    @property
    def webp_lossless(self) -> bool:
        """WebPロスレス設定"""
        return self._get_property("webp_lossless", False)
    
    @webp_lossless.setter
    def webp_lossless(self, value: bool) -> None:
        self._set_property("webp_lossless", value)
        self._update_settings()
    
    @property
    def prefix(self) -> str:
        """ファイル名プレフィックス"""
        return self._get_property("prefix", "")
    
    @prefix.setter
    def prefix(self, value: str) -> None:
        self._set_property("prefix", value)
        self._update_settings()
    
    @property
    def suffix(self) -> str:
        """ファイル名サフィックス"""
        return self._get_property("suffix", "_resized")
    
    @suffix.setter
    def suffix(self, value: str) -> None:
        self._set_property("suffix", value)
        self._update_settings()
    
    @property
    def can_process(self) -> bool:
        """処理可能かどうか"""
        return (
            bool(self.input_path) and
            Path(self.input_path).exists() and
            bool(self.output_directory) and
            Path(self.output_directory).exists() and
            not self.is_busy
        )
    
    @property
    def processing_results(self) -> List[ProcessingResult]:
        """処理結果のリスト"""
        return self._processing_results.copy()
    
    # メソッド
    def start_processing(self) -> None:
        """画像処理を開始"""
        if not self.can_process:
            self.error_message = "入力ファイルまたは出力先が無効です"
            return
        
        self.is_busy = True
        self.error_message = ""
        self.reset_progress()
        self._processing_results.clear()
        self.image_service.reset_cancel()
        
        self._current_thread = threading.Thread(
            target=self._process_images,
            daemon=True
        )
        self._current_thread.start()
    
    def cancel_processing(self) -> None:
        """処理をキャンセル"""
        if self._current_thread and self._current_thread.is_alive():
            self.image_service.cancel_processing()
            self.status_message = "処理をキャンセルしています..."
    
    def apply_preset(self, preset_data: Dict[str, Any]) -> None:
        """プリセットを適用"""
        self.resize_mode = preset_data.get("resize_mode", ResizeMode.NONE)
        self.resize_value = preset_data.get("resize_value", 0)
        self.quality = preset_data.get("quality", PROCESSING.DEFAULT_QUALITY)
        self.output_format = preset_data.get("output_format", OutputFormat.ORIGINAL)
        self.maintain_aspect_ratio = preset_data.get("maintain_aspect_ratio", True)
        self.preserve_metadata = preset_data.get("preserve_metadata", True)
        self.webp_lossless = preset_data.get("webp_lossless", False)
        self.prefix = preset_data.get("prefix", "")
        self.suffix = preset_data.get("suffix", "_resized")
        
        self.log_message("プリセットを適用しました")
    
    def validate(self) -> bool:
        """入力の検証"""
        if not self.input_path:
            self.error_message = "入力を選択してください"
            return False
        
        if not Path(self.input_path).exists():
            self.error_message = "入力パスが存在しません"
            return False
        
        if not self.output_directory:
            self.error_message = "出力先を選択してください"
            return False
        
        if not Path(self.output_directory).exists():
            self.error_message = "出力先ディレクトリが存在しません"
            return False
        
        # 設定の検証
        settings = self._get_current_settings()
        is_valid, error_msg = settings.validate()
        if not is_valid:
            self.error_message = error_msg
            return False
        
        self.clear_error()
        return True
    
    # プライベートメソッド
    def _process_images(self) -> None:
        """画像処理の実行"""
        try:
            if self.processing_mode == ProcessingMode.SINGLE:
                self._process_single_image()
            else:
                self._process_batch_images()
                
        except Exception as e:
            self.error_message = str(e)
            self.log_message(f"エラーが発生しました: {e}", "error")
        finally:
            self.is_busy = False
            self.progress = 1.0
    
    def _process_single_image(self) -> None:
        """単一画像の処理"""
        self.status_message = "画像を処理しています..."
        self.log_message(f"処理開始: {Path(self.input_path).name}")
        
        result = self.image_service.process_image(
            self.input_path,
            self.output_directory,
            self._get_current_settings(),
            lambda p: setattr(self, 'progress', p)
        )
        
        self._processing_results.append(result)
        
        if result.success:
            self.status_message = "処理が完了しました"
            self.log_message(
                f"処理完了: {result.output_path.name} "
                f"(サイズ: {result.size_reduction_percent:.1f}%削減)"
            )
            self._notify("processing_completed", result)
        else:
            self.error_message = result.error_message or "処理に失敗しました"
            self.log_message(f"処理失敗: {result.error_message}", "error")
    
    def _process_batch_images(self) -> None:
        """バッチ画像処理"""
        self.status_message = "画像を収集しています..."
        self.log_message(f"バッチ処理開始: {self.input_path}")
        
        def on_progress(current: int, total: int):
            self.progress = current / total if total > 0 else 0
            self.status_message = f"処理中... ({current}/{total})"
        
        def on_result(result: ProcessingResult):
            self._processing_results.append(result)
            if result.success:
                self.log_message(f"完了: {result.source_path.name}")
            else:
                self.log_message(f"失敗: {result.source_path.name} - {result.error_message}", "warning")
        
        results = self.image_service.process_batch(
            self.input_path,
            self.output_directory,
            self._get_current_settings(),
            on_progress,
            on_result
        )
        
        # 結果サマリー
        success_count = sum(1 for r in results if r.success)
        fail_count = len(results) - success_count
        
        self.status_message = f"処理完了: 成功 {success_count}件, 失敗 {fail_count}件"
        self.log_message(f"バッチ処理完了: 成功 {success_count}件, 失敗 {fail_count}件")
        
        self._notify("batch_completed", results)
    
    def _validate_input(self) -> None:
        """入力の検証"""
        if self.input_path and not Path(self.input_path).exists():
            self.error_message = "指定されたパスが見つかりません"
        else:
            self.clear_error()
    
    def _update_settings(self) -> None:
        """設定を更新"""
        settings = self._get_current_settings()
        if self.processing_mode == ProcessingMode.SINGLE:
            self._settings = settings
        else:
            self._batch_settings = settings
    
    def _get_current_settings(self) -> ResizeSettings:
        """現在の設定を取得"""
        if self.processing_mode == ProcessingMode.BATCH:
            settings = BatchSettings()
        else:
            settings = ResizeSettings()
        
        settings.resize_mode = self.resize_mode
        settings.resize_value = self.resize_value
        settings.quality = self.quality
        settings.output_format = self.output_format
        settings.maintain_aspect_ratio = self.maintain_aspect_ratio
        settings.preserve_metadata = self.preserve_metadata
        settings.webp_lossless = self.webp_lossless
        settings.prefix = self.prefix
        settings.suffix = self.suffix
        
        return settings