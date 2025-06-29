"""
設定管理サービス
"""
from pathlib import Path
from typing import Optional, Dict, Any, List
import json
import sys

# プロジェクトルートをPythonパスに追加
project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from settings_manager import SettingsManager, AppSettings, ResizeSettings, BatchSettings


class SettingsService:
    """設定管理を行うサービスクラス"""
    
    def __init__(self, settings_file: Optional[str] = None):
        self.settings_manager = SettingsManager(settings_file)
    
    def load_settings(self) -> AppSettings:
        """設定を読み込む"""
        return self.settings_manager.load()
    
    def save_settings(self, settings: AppSettings) -> None:
        """設定を保存"""
        self.settings_manager.save(settings)
    
    def get_resize_settings(self) -> ResizeSettings:
        """リサイズ設定を取得"""
        app_settings = self.load_settings()
        return app_settings.resize
    
    def save_resize_settings(self, resize_settings: ResizeSettings) -> None:
        """リサイズ設定を保存"""
        app_settings = self.load_settings()
        app_settings.resize = resize_settings
        self.save_settings(app_settings)
    
    def get_batch_settings(self) -> BatchSettings:
        """バッチ設定を取得"""
        app_settings = self.load_settings()
        return app_settings.batch
    
    def save_batch_settings(self, batch_settings: BatchSettings) -> None:
        """バッチ設定を保存"""
        app_settings = self.load_settings()
        app_settings.batch = batch_settings
        self.save_settings(app_settings)
    
    def get_recent_inputs(self) -> List[str]:
        """最近使用した入力を取得"""
        app_settings = self.load_settings()
        return app_settings.recent_inputs
    
    def add_recent_input(self, path: str) -> None:
        """最近使用した入力に追加"""
        self.settings_manager.add_recent_input(path)
    
    def get_recent_outputs(self) -> List[str]:
        """最近使用した出力先を取得"""
        app_settings = self.load_settings()
        return app_settings.recent_outputs
    
    def add_recent_output(self, path: str) -> None:
        """最近使用した出力先に追加"""
        self.settings_manager.add_recent_output(path)
    
    def clear_recent_files(self) -> None:
        """最近使用したファイルをクリア"""
        app_settings = self.load_settings()
        app_settings.recent_inputs = []
        app_settings.recent_outputs = []
        self.save_settings(app_settings)
    
    def get_window_settings(self) -> Dict[str, Any]:
        """ウィンドウ設定を取得"""
        app_settings = self.load_settings()
        return {
            "window_width": app_settings.window_width,
            "window_height": app_settings.window_height,
            "window_x": app_settings.window_x,
            "window_y": app_settings.window_y
        }
    
    def save_window_settings(
        self,
        width: int,
        height: int,
        x: Optional[int] = None,
        y: Optional[int] = None
    ) -> None:
        """ウィンドウ設定を保存"""
        app_settings = self.load_settings()
        app_settings.window_width = width
        app_settings.window_height = height
        if x is not None:
            app_settings.window_x = x
        if y is not None:
            app_settings.window_y = y
        self.save_settings(app_settings)
    
    def get_ui_settings(self) -> Dict[str, Any]:
        """UI設定を取得"""
        # UISettingsがsettings_managerに存在する場合
        if hasattr(self.settings_manager, 'settings') and hasattr(self.settings_manager.settings, 'ui'):
            return self.settings_manager.settings.ui
        # 存在しない場合はデフォルト値を返す
        return {"theme": "light"}
    
    def save_ui_settings(self, ui_settings: Any) -> None:
        """UI設定を保存"""
        app_settings = self.load_settings()
        # UISettingsが存在する場合
        if hasattr(app_settings, 'ui'):
            app_settings.ui = ui_settings
        self.save_settings(app_settings)
    
    def export_settings(self, file_path: str) -> None:
        """設定をファイルにエクスポート"""
        app_settings = self.load_settings()
        
        export_data = {
            "version": "1.0",
            "settings": {
                "resize": {
                    "mode": app_settings.resize.mode,
                    "value": app_settings.resize.value,
                    "maintain_aspect_ratio": app_settings.resize.maintain_aspect_ratio,
                    "output_format": app_settings.resize.output_format,
                    "quality": app_settings.resize.quality,
                    "enable_compression": app_settings.resize.enable_compression,
                    "target_size_kb": app_settings.resize.target_size_kb,
                    "balance": app_settings.resize.balance,
                    "prefix": app_settings.resize.prefix,
                    "suffix": app_settings.resize.suffix,
                    "overwrite": app_settings.resize.overwrite,
                    "exif_handling": app_settings.resize.exif_handling
                },
                "batch": {
                    "recursive": app_settings.batch.recursive,
                    "extensions": list(app_settings.batch.extensions),
                    "max_files": app_settings.batch.max_files,
                    "skip_errors": app_settings.batch.skip_errors,
                    "create_subdirectory": app_settings.batch.create_subdirectory,
                    "subdirectory_name": app_settings.batch.subdirectory_name
                }
            }
        }
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, ensure_ascii=False, indent=2)
    
    def import_settings(self, file_path: str) -> None:
        """設定をファイルからインポート"""
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        settings_data = data.get("settings", {})
        app_settings = self.load_settings()
        
        # リサイズ設定
        if "resize" in settings_data:
            resize_data = settings_data["resize"]
            for key, value in resize_data.items():
                if hasattr(app_settings.resize, key):
                    setattr(app_settings.resize, key, value)
        
        # バッチ設定
        if "batch" in settings_data:
            batch_data = settings_data["batch"]
            for key, value in batch_data.items():
                if hasattr(app_settings.batch, key):
                    if key == "extensions":
                        value = set(value)
                    setattr(app_settings.batch, key, value)
        
        self.save_settings(app_settings)
    
    def reset_to_defaults(self) -> None:
        """デフォルト設定に戻す"""
        default_settings = AppSettings()
        self.save_settings(default_settings)