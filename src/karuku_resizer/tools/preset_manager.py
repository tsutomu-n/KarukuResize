"""
プリセット管理システムのモジュール
"""
import json
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict, field
from datetime import datetime
import os

@dataclass
class PresetData:
    """プリセットデータ"""
    name: str
    description: str = ""
    resize_mode: str = "longest_side"  # none, width, height, longest_side, percentage
    resize_value: int = 1920
    maintain_aspect_ratio: bool = True
    output_format: str = "original"  # original, jpeg, png, webp
    quality: int = 85
    webp_lossless: bool = False
    preserve_metadata: bool = True
    enable_compression: bool = True
    target_size_kb: Optional[int] = None
    balance: int = 5
    prefix: str = ""
    suffix: str = "_resized"
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())
    is_builtin: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        """辞書に変換"""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'PresetData':
        """辞書から作成"""
        return cls(**data)


class PresetManager:
    """プリセットマネージャー"""
    
    DEFAULT_FILENAME = "presets.json"
    
    # 組み込みプリセット
    BUILTIN_PRESETS = [
        PresetData(
            name="Web用（高品質）",
            description="Webサイト用の高品質画像",
            resize_mode="longest_side",
            resize_value=1920,
            output_format="jpeg",
            quality=85,
            is_builtin=True
        ),
        PresetData(
            name="Web用（軽量）",
            description="読み込み速度重視のWeb画像",
            resize_mode="longest_side",
            resize_value=1200,
            output_format="jpeg",
            quality=70,
            balance=3,
            is_builtin=True
        ),
        PresetData(
            name="サムネイル",
            description="小さなサムネイル画像",
            resize_mode="longest_side",
            resize_value=300,
            output_format="jpeg",
            quality=80,
            is_builtin=True
        ),
        PresetData(
            name="SNS用（Instagram）",
            description="Instagram投稿用（正方形）",
            resize_mode="width",
            resize_value=1080,
            maintain_aspect_ratio=False,
            output_format="jpeg",
            quality=90,
            is_builtin=True
        ),
        PresetData(
            name="SNS用（Twitter）",
            description="Twitter投稿用",
            resize_mode="longest_side",
            resize_value=2048,
            output_format="jpeg",
            quality=85,
            is_builtin=True
        ),
        PresetData(
            name="メール添付用",
            description="メール添付に適したサイズ",
            resize_mode="longest_side",
            resize_value=1024,
            output_format="jpeg",
            quality=75,
            target_size_kb=500,
            is_builtin=True
        ),
        PresetData(
            name="印刷用（高解像度）",
            description="高品質印刷用",
            resize_mode="none",
            output_format="original",
            quality=95,
            preserve_metadata=True,
            is_builtin=True
        ),
        PresetData(
            name="アーカイブ用",
            description="長期保存用（ロスレス圧縮）",
            resize_mode="none",
            output_format="png",
            quality=100,
            preserve_metadata=True,
            is_builtin=True
        ),
        PresetData(
            name="WebP変換（高品質）",
            description="次世代フォーマットへの変換",
            resize_mode="none",
            output_format="webp",
            quality=90,
            webp_lossless=False,
            is_builtin=True
        ),
        PresetData(
            name="バッチ処理用",
            description="大量処理用の標準設定",
            resize_mode="percentage",
            resize_value=75,
            output_format="original",
            quality=80,
            suffix="_batch",
            is_builtin=True
        )
    ]
    
    def __init__(self, config_dir: Optional[Path] = None):
        """
        Args:
            config_dir: プリセットファイルの保存ディレクトリ
        """
        self.config_dir = config_dir or self._get_default_config_dir()
        self.preset_file = self.config_dir / self.DEFAULT_FILENAME
        self.presets: Dict[str, PresetData] = {}
        self._ensure_config_dir()
        self._load_builtin_presets()
        
    def _get_default_config_dir(self) -> Path:
        """デフォルトの設定ディレクトリを取得"""
        if os.name == 'nt':  # Windows
            app_data = os.environ.get('APPDATA', '')
            if app_data:
                return Path(app_data) / 'KarukuResize'
            else:
                return Path.home() / '.karukuresize'
        else:  # Unix/Linux/Mac
            config_home = os.environ.get('XDG_CONFIG_HOME', '')
            if config_home:
                return Path(config_home) / 'karukuresize'
            else:
                return Path.home() / '.config' / 'karukuresize'
                
    def _ensure_config_dir(self):
        """設定ディレクトリを作成"""
        self.config_dir.mkdir(parents=True, exist_ok=True)
        
    def _load_builtin_presets(self):
        """組み込みプリセットを読み込む"""
        for preset in self.BUILTIN_PRESETS:
            self.presets[preset.name] = preset
            
    def load(self):
        """ユーザープリセットを読み込む"""
        try:
            if self.preset_file.exists():
                with open(self.preset_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    
                # ユーザープリセットのみ読み込む（組み込みは上書きしない）
                for name, preset_dict in data.items():
                    if not preset_dict.get('is_builtin', False):
                        self.presets[name] = PresetData.from_dict(preset_dict)
                        
                print(f"プリセットを読み込みました: {self.preset_file}")
        except Exception as e:
            print(f"プリセットの読み込みエラー: {e}")
            
    def save(self):
        """ユーザープリセットを保存"""
        try:
            # ユーザープリセットのみ保存
            user_presets = {
                name: preset.to_dict()
                for name, preset in self.presets.items()
                if not preset.is_builtin
            }
            
            with open(self.preset_file, 'w', encoding='utf-8') as f:
                json.dump(user_presets, f, ensure_ascii=False, indent=2)
                
            print(f"プリセットを保存しました: {self.preset_file}")
            return True
        except Exception as e:
            print(f"プリセットの保存エラー: {e}")
            return False
            
    def add_preset(self, preset: PresetData) -> bool:
        """プリセットを追加"""
        if preset.name in self.presets and self.presets[preset.name].is_builtin:
            print(f"組み込みプリセット '{preset.name}' は上書きできません")
            return False
            
        preset.is_builtin = False
        preset.updated_at = datetime.now().isoformat()
        self.presets[preset.name] = preset
        return self.save()
        
    def update_preset(self, name: str, preset: PresetData) -> bool:
        """プリセットを更新"""
        if name in self.presets and self.presets[name].is_builtin:
            print(f"組み込みプリセット '{name}' は更新できません")
            return False
            
        if name in self.presets:
            # 名前が変更された場合
            if name != preset.name:
                del self.presets[name]
                
            preset.is_builtin = False
            preset.updated_at = datetime.now().isoformat()
            self.presets[preset.name] = preset
            return self.save()
        return False
        
    def delete_preset(self, name: str) -> bool:
        """プリセットを削除"""
        if name in self.presets:
            if self.presets[name].is_builtin:
                print(f"組み込みプリセット '{name}' は削除できません")
                return False
                
            del self.presets[name]
            return self.save()
        return False
        
    def get_preset(self, name: str) -> Optional[PresetData]:
        """プリセットを取得"""
        return self.presets.get(name)
        
    def get_all_presets(self) -> List[PresetData]:
        """全プリセットを取得"""
        return list(self.presets.values())
        
    def get_preset_names(self) -> List[str]:
        """プリセット名のリストを取得"""
        # 組み込みプリセットを先に、ユーザープリセットを後に
        builtin_names = [name for name, p in self.presets.items() if p.is_builtin]
        user_names = [name for name, p in self.presets.items() if not p.is_builtin]
        
        builtin_names.sort()
        user_names.sort()
        
        return builtin_names + user_names
        
    def export_preset(self, name: str, filepath: Path) -> bool:
        """プリセットをエクスポート"""
        if name not in self.presets:
            return False
            
        try:
            preset_data = self.presets[name].to_dict()
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(preset_data, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            print(f"プリセットのエクスポートエラー: {e}")
            return False
            
    def import_preset(self, filepath: Path) -> Optional[PresetData]:
        """プリセットをインポート"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            preset = PresetData.from_dict(data)
            preset.is_builtin = False  # インポートしたプリセットは常にユーザープリセット
            
            # 名前が重複する場合は番号を付ける
            original_name = preset.name
            counter = 1
            while preset.name in self.presets:
                preset.name = f"{original_name} ({counter})"
                counter += 1
                
            self.add_preset(preset)
            return preset
            
        except Exception as e:
            print(f"プリセットのインポートエラー: {e}")
            return None
            
    def duplicate_preset(self, name: str, new_name: str) -> Optional[PresetData]:
        """プリセットを複製"""
        if name not in self.presets:
            return None
            
        original = self.presets[name]
        duplicate = PresetData.from_dict(original.to_dict())
        duplicate.name = new_name
        duplicate.is_builtin = False
        duplicate.created_at = datetime.now().isoformat()
        duplicate.updated_at = datetime.now().isoformat()
        
        if self.add_preset(duplicate):
            return duplicate
        return None