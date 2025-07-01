"""
プリセット管理サービス
"""
from pathlib import Path
from typing import Optional, List, Dict, Any
import sys

# プロジェクトルートをPythonパスに追加
project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from preset_manager import PresetManager, PresetData


class PresetService:
    """プリセット管理を行うサービスクラス"""
    
    def __init__(self, preset_file: Optional[str] = None):
        self.preset_manager = PresetManager(preset_file)
        self.preset_manager.load()
    
    def get_all_presets(self) -> List[PresetData]:
        """すべてのプリセットを取得"""
        return self.preset_manager.get_all_presets()
    
    def get_preset_names(self) -> List[str]:
        """プリセット名のリストを取得"""
        return self.preset_manager.get_preset_names()
    
    def get_preset(self, name: str) -> Optional[PresetData]:
        """指定された名前のプリセットを取得"""
        return self.preset_manager.get_preset(name)
    
    def add_preset(self, preset: PresetData) -> None:
        """プリセットを追加"""
        self.preset_manager.add_preset(preset)
        self.preset_manager.save()
    
    def update_preset(self, name: str, preset: PresetData) -> None:
        """プリセットを更新"""
        self.preset_manager.update_preset(name, preset)
        self.preset_manager.save()
    
    def delete_preset(self, name: str) -> None:
        """プリセットを削除"""
        self.preset_manager.delete_preset(name)
        self.preset_manager.save()
    
    def create_preset_from_settings(
        self,
        name: str,
        description: str,
        settings: Dict[str, Any]
    ) -> PresetData:
        """設定からプリセットを作成"""
        preset = PresetData(
            name=name,
            description=description,
            resize_mode=settings.get("resize_mode", "longest_side"),
            resize_value=settings.get("resize_value", 1920),
            maintain_aspect_ratio=settings.get("maintain_aspect_ratio", True),
            output_format=settings.get("output_format", "original"),
            quality=settings.get("quality", 85),
            webp_lossless=settings.get("webp_lossless", False),
            preserve_metadata=settings.get("preserve_metadata", True),
            enable_compression=settings.get("enable_compression", True),
            target_size_kb=settings.get("target_size_kb"),
            balance=settings.get("balance", 5),
            prefix=settings.get("prefix", ""),
            suffix=settings.get("suffix", "_resized"),
            is_builtin=False
        )
        return preset
    
    def get_builtin_presets(self) -> List[PresetData]:
        """組み込みプリセットを取得"""
        return [preset for preset in self.preset_manager.get_all_presets() if preset.is_builtin]
    
    def get_custom_presets(self) -> List[PresetData]:
        """カスタムプリセットを取得"""
        return [preset for preset in self.preset_manager.get_all_presets() if not preset.is_builtin]
    
    def reset_to_defaults(self) -> None:
        """デフォルトに戻す（カスタムプリセットをすべて削除）"""
        custom_presets = self.get_custom_presets()
        for preset in custom_presets:
            self.preset_manager.delete_preset(preset.name)
        self.preset_manager.save()
    
    def export_presets(self, file_path: str) -> None:
        """プリセットをファイルにエクスポート"""
        import json
        
        presets_data = {
            "version": "1.0",
            "presets": [preset.to_dict() for preset in self.get_all_presets()]
        }
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(presets_data, f, ensure_ascii=False, indent=2)
    
    def import_presets(self, file_path: str, overwrite: bool = False) -> int:
        """プリセットをファイルからインポート"""
        import json
        
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        imported_count = 0
        presets_data = data.get("presets", [])
        
        for preset_dict in presets_data:
            preset = PresetData.from_dict(preset_dict)
            preset.is_builtin = False  # インポートしたプリセットは常にカスタム
            
            existing = self.preset_manager.get_preset(preset.name)
            if existing and not overwrite:
                continue
            
            if existing:
                self.preset_manager.update_preset(preset.name, preset)
            else:
                self.preset_manager.add_preset(preset)
            
            imported_count += 1
        
        self.preset_manager.save()
        return imported_count