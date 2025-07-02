"""
設定管理のためのユーティリティモジュール
"""
import json
from pathlib import Path
from typing import Dict, Any, Optional
import os
from dataclasses import dataclass, asdict, field
from datetime import datetime

@dataclass
class ResizeSettings:
    """リサイズ設定"""
    mode: str = "longest_side"  # percentage, width_height, longest_side
    value: int = 1920
    width: int = 1920
    height: int = 1080
    maintain_aspect_ratio: bool = True
    quality: int = 85
    format: str = "jpeg"  # jpeg, png, webp
    webp_lossless: bool = False
    preserve_metadata: bool = True
    
@dataclass
class UISettings:
    """UI設定"""
    theme: str = "light"  # light, dark, system
    language: str = "ja"  # ja, en
    window_width: int = 1000
    window_height: int = 900
    auto_save_settings: bool = True
    confirm_overwrite: bool = True
    show_preview: bool = True
    
@dataclass
class RecentPaths:
    """最近使用したパス"""
    input_files: list = field(default_factory=list)
    output_directories: list = field(default_factory=list)
    max_items: int = 10
    
    def add_input_file(self, path: str):
        """入力ファイルを追加"""
        if path in self.input_files:
            self.input_files.remove(path)
        self.input_files.insert(0, path)
        self.input_files = self.input_files[:self.max_items]
        
    def add_output_directory(self, path: str):
        """出力ディレクトリを追加"""
        if path in self.output_directories:
            self.output_directories.remove(path)
        self.output_directories.insert(0, path)
        self.output_directories = self.output_directories[:self.max_items]

@dataclass
class Settings:
    """アプリケーション設定"""
    resize: ResizeSettings = field(default_factory=ResizeSettings)
    ui: UISettings = field(default_factory=UISettings)
    recent: RecentPaths = field(default_factory=RecentPaths)
    last_saved: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """辞書に変換"""
        data = {
            'resize': asdict(self.resize),
            'ui': asdict(self.ui),
            'recent': asdict(self.recent),
            'last_saved': datetime.now().isoformat()
        }
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Settings':
        """辞書から作成"""
        settings = cls()
        
        if 'resize' in data:
            settings.resize = ResizeSettings(**data['resize'])
        if 'ui' in data:
            settings.ui = UISettings(**data['ui'])
        if 'recent' in data:
            settings.recent = RecentPaths(**data['recent'])
        if 'last_saved' in data:
            settings.last_saved = data['last_saved']
            
        return settings


class SettingsManager:
    """設定マネージャー"""
    
    DEFAULT_FILENAME = "karukuresize_settings.json"
    
    def __init__(self, config_dir: Optional[Path] = None):
        """
        Args:
            config_dir: 設定ファイルの保存ディレクトリ（指定しない場合は標準の場所）
        """
        self.config_dir = config_dir or self._get_default_config_dir()
        self.config_file = self.config_dir / self.DEFAULT_FILENAME
        self.settings = Settings()
        self._ensure_config_dir()
        
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
        
    def load(self) -> Settings:
        """設定を読み込む"""
        try:
            if self.config_file.exists():
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.settings = Settings.from_dict(data)
                    print(f"設定を読み込みました: {self.config_file}")
            else:
                print("設定ファイルが見つかりません。デフォルト設定を使用します。")
                self.settings = Settings()
        except Exception as e:
            print(f"設定の読み込みエラー: {e}")
            self.settings = Settings()
            
        return self.settings
        
    def save(self):
        """設定を保存"""
        try:
            data = self.settings.to_dict()
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            print(f"設定を保存しました: {self.config_file}")
            return True
        except Exception as e:
            print(f"設定の保存エラー: {e}")
            return False
            
    def reset(self):
        """設定をリセット"""
        self.settings = Settings()
        self.save()
        
    def get_resize_settings(self) -> ResizeSettings:
        """リサイズ設定を取得"""
        return self.settings.resize
        
    def update_resize_settings(self, **kwargs):
        """リサイズ設定を更新"""
        for key, value in kwargs.items():
            if hasattr(self.settings.resize, key):
                setattr(self.settings.resize, key, value)
                
    def get_ui_settings(self) -> UISettings:
        """UI設定を取得"""
        return self.settings.ui
        
    def update_ui_settings(self, **kwargs):
        """UI設定を更新"""
        for key, value in kwargs.items():
            if hasattr(self.settings.ui, key):
                setattr(self.settings.ui, key, value)
                
    def add_recent_input(self, path: str):
        """最近使用した入力ファイルを追加"""
        self.settings.recent.add_input_file(path)
        if self.settings.ui.auto_save_settings:
            self.save()
            
    def add_recent_output(self, path: str):
        """最近使用した出力ディレクトリを追加"""
        self.settings.recent.add_output_directory(path)
        if self.settings.ui.auto_save_settings:
            self.save()
            
    def get_recent_inputs(self) -> list:
        """最近使用した入力ファイルを取得"""
        return self.settings.recent.input_files
        
    def get_recent_outputs(self) -> list:
        """最近使用した出力ディレクトリを取得"""
        return self.settings.recent.output_directories
        
    def export_settings(self, filepath: Path):
        """設定をエクスポート"""
        try:
            data = self.settings.to_dict()
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            print(f"設定のエクスポートエラー: {e}")
            return False
            
    def import_settings(self, filepath: Path):
        """設定をインポート"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.settings = Settings.from_dict(data)
                self.save()
            return True
        except Exception as e:
            print(f"設定のインポートエラー: {e}")
            return False