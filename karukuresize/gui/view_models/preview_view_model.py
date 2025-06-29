"""
プレビュータブのViewModel
"""
from typing import Optional, Tuple
from pathlib import Path
import threading
from PIL import Image
import io
import sys

# プロジェクトルートをPythonパスに追加
project_root = Path(__file__).parent.parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from .base_view_model import BaseViewModel
from ...models.resize_settings import ResizeSettings, ProcessingResult
from ...services.image_service import ImageService
from resize_core import resize_and_compress_image


class PreviewViewModel(BaseViewModel):
    """プレビュー機能のViewModel"""
    
    def __init__(self, image_service: Optional[ImageService] = None):
        super().__init__()
        self.image_service = image_service or ImageService()
        self._preview_thread: Optional[threading.Thread] = None
        self._cancel_preview = False
        
    def initialize(self) -> None:
        """初期化処理"""
        self._is_initialized = True
        
    def cleanup(self) -> None:
        """クリーンアップ処理"""
        self.cancel_preview_generation()
        self.unbind_all()
    
    # プロパティ
    @property
    def source_image_path(self) -> str:
        """ソース画像のパス"""
        return self._get_property("source_image_path", "")
    
    @source_image_path.setter
    def source_image_path(self, value: str) -> None:
        self._set_property("source_image_path", value)
        # パスが変更されたら自動的に画像を読み込む
        if value and Path(value).exists():
            self.load_source_image(value)
    
    @property
    def source_image(self) -> Optional[Image.Image]:
        """ソース画像"""
        return self._get_property("source_image", None)
    
    @property
    def preview_image(self) -> Optional[Image.Image]:
        """プレビュー画像"""
        return self._get_property("preview_image", None)
    
    @property
    def source_image_info(self) -> dict:
        """ソース画像の情報"""
        return self._get_property("source_image_info", {})
    
    @property
    def preview_image_info(self) -> dict:
        """プレビュー画像の情報"""
        return self._get_property("preview_image_info", {})
    
    @property
    def is_generating_preview(self) -> bool:
        """プレビュー生成中フラグ"""
        return self._get_property("is_generating_preview", False)
    
    @is_generating_preview.setter
    def is_generating_preview(self, value: bool) -> None:
        self._set_property("is_generating_preview", value)
    
    @property
    def zoom_level(self) -> float:
        """ズームレベル"""
        return self._get_property("zoom_level", 1.0)
    
    @zoom_level.setter
    def zoom_level(self, value: float) -> None:
        # 0.1 - 4.0の範囲に制限
        value = max(0.1, min(4.0, value))
        self._set_property("zoom_level", value)
    
    # メソッド
    def load_source_image(self, image_path: str) -> None:
        """ソース画像を読み込む"""
        path = Path(image_path)
        if not path.exists():
            self.error_message = "画像ファイルが見つかりません"
            return
        
        try:
            # 画像を読み込む
            image = Image.open(path)
            
            # RGBA画像の場合はRGBに変換
            if image.mode == 'RGBA':
                background = Image.new('RGB', image.size, (255, 255, 255))
                background.paste(image, mask=image.split()[3])
                image = background
            
            # 画像情報を収集
            info = {
                "path": str(path),
                "size": image.size,
                "file_size": path.stat().st_size,
                "format": image.format or path.suffix[1:].upper(),
                "mode": image.mode,
                "has_exif": bool(image.getexif())
            }
            
            # プロパティを更新
            self._set_property("source_image", image)
            self._set_property("source_image_info", info)
            
            self.log_message(f"画像を読み込みました: {path.name}")
            self.clear_error()
            
            # 画像読み込み完了を通知
            self._notify("source_image_loaded", image)
            
        except Exception as e:
            self.error_message = f"画像の読み込みに失敗しました: {str(e)}"
            self.log_message(f"画像読み込みエラー: {e}", "error")
    
    def generate_preview(self, settings: ResizeSettings) -> None:
        """プレビュー画像を生成"""
        if not self.source_image or self.is_generating_preview:
            return
        
        self.is_generating_preview = True
        self._cancel_preview = False
        
        self._preview_thread = threading.Thread(
            target=self._generate_preview_worker,
            args=(settings,),
            daemon=True
        )
        self._preview_thread.start()
    
    def cancel_preview_generation(self) -> None:
        """プレビュー生成をキャンセル"""
        self._cancel_preview = True
        if self._preview_thread and self._preview_thread.is_alive():
            self._preview_thread.join(timeout=1.0)
    
    def _generate_preview_worker(self, settings: ResizeSettings) -> None:
        """プレビュー生成のワーカースレッド"""
        try:
            if not self.source_image_path:
                return
            
            # メモリ上でプレビューを生成
            temp_output = io.BytesIO()
            
            # 元の画像を一時的に保存
            source_image = self.source_image
            temp_input = io.BytesIO()
            source_image.save(temp_input, format='PNG')
            temp_input.seek(0)
            
            # リサイズ処理
            result = resize_and_compress_image(
                source_image=source_image,
                output_buffer=temp_output,
                resize_mode=settings.resize_mode,
                resize_value=settings.resize_value,
                quality=settings.quality,
                output_format=settings.output_format if settings.output_format != "original" else None,
                exif_handling="keep" if settings.preserve_metadata else "remove",
                lanczos_filter=settings.lanczos_filter,
                progressive=settings.progressive,
                optimize=settings.optimize
            )
            
            # メモリベース処理の戻り値を処理
            if len(result) == 2:
                success, error_msg = result
            else:
                # 互換性のためのフォールバック
                success = result[0]
                error_msg = None if success else "処理に失敗しました"
            
            if self._cancel_preview:
                return
            
            if success:
                # プレビュー画像を読み込む
                temp_output.seek(0)
                preview_image = Image.open(temp_output)
                
                # 画像情報を収集
                info = {
                    "size": preview_image.size,
                    "estimated_file_size": len(temp_output.getvalue()),
                    "format": settings.output_format.upper() if settings.output_format != "original" else self.source_image_info.get("format", ""),
                    "mode": preview_image.mode,
                    "settings": settings.to_dict()
                }
                
                # プロパティを更新
                self._set_property("preview_image", preview_image)
                self._set_property("preview_image_info", info)
                
                self.log_message("プレビューを生成しました")
                
                # プレビュー生成完了を通知
                self._notify("preview_generated", preview_image)
                
            else:
                self.error_message = f"プレビュー生成に失敗しました: {error_msg}"
                
        except Exception as e:
            self.error_message = f"プレビュー生成エラー: {str(e)}"
            self.log_message(f"プレビュー生成エラー: {e}", "error")
            
        finally:
            self.is_generating_preview = False
    
    def reset_zoom(self) -> None:
        """ズームをリセット"""
        self.zoom_level = 1.0
    
    def zoom_in(self) -> None:
        """ズームイン"""
        current = self.zoom_level
        # ズームレベルのステップ
        zoom_steps = [0.1, 0.25, 0.5, 0.75, 1.0, 1.5, 2.0, 3.0, 4.0]
        for step in zoom_steps:
            if step > current:
                self.zoom_level = step
                break
    
    def zoom_out(self) -> None:
        """ズームアウト"""
        current = self.zoom_level
        # ズームレベルのステップ（逆順）
        zoom_steps = [4.0, 3.0, 2.0, 1.5, 1.0, 0.75, 0.5, 0.25, 0.1]
        for step in zoom_steps:
            if step < current:
                self.zoom_level = step
                break
    
    def fit_to_window(self) -> None:
        """ウィンドウに合わせる"""
        # このメソッドはViewから呼ばれ、Viewがウィンドウサイズに基づいて
        # 適切なズームレベルを設定する
        self._notify("fit_to_window_requested", None)
    
    def get_size_reduction_info(self) -> dict:
        """サイズ削減情報を取得"""
        if not self.source_image_info or not self.preview_image_info:
            return {}
        
        original_size = self.source_image_info.get("file_size", 0)
        preview_size = self.preview_image_info.get("estimated_file_size", 0)
        
        if original_size == 0:
            return {}
        
        reduction_bytes = original_size - preview_size
        reduction_percent = (reduction_bytes / original_size) * 100
        
        return {
            "original_size": original_size,
            "preview_size": preview_size,
            "reduction_bytes": reduction_bytes,
            "reduction_percent": reduction_percent
        }