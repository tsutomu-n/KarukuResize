#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
画像処理設定管理モジュール

画像処理に関する全ての設定を一元管理します。
デフォルト値の定義と設定の永続化をサポートします。
"""

import json
from pathlib import Path
from typing import Dict, Any, Optional
from dataclasses import dataclass, asdict


@dataclass
class ImageProcessingConfig:
    """画像処理設定を管理するデータクラス"""
    
    # デフォルト値の定義
    DEFAULT_WIDTH: int = 800
    DEFAULT_QUALITY: int = 85
    DEFAULT_FORMAT: str = "original"
    DEFAULT_RESIZE_MODE: str = "none"
    DEFAULT_TARGET_SIZE_KB: int = 0
    
    # 設定値
    quality: int = 85
    output_format: str = "original"
    resize_mode: str = "none"
    resize_width: int = 800
    target_size_kb: int = 0
    
    # UI関連設定
    last_input_path: Optional[str] = None
    last_output_path: Optional[str] = None
    window_geometry: Optional[Dict[str, int]] = None
    
    def __post_init__(self):
        """初期化後の検証"""
        self.validate()
    
    def validate(self):
        """設定値の妥当性を検証"""
        if not 1 <= self.quality <= 100:
            self.quality = self.DEFAULT_QUALITY
            
        if self.output_format not in ["original", "jpeg", "png", "webp"]:
            self.output_format = self.DEFAULT_FORMAT
            
        if self.resize_mode not in ["none", "width"]:
            self.resize_mode = self.DEFAULT_RESIZE_MODE
            
        if self.resize_width <= 0:
            self.resize_width = self.DEFAULT_WIDTH
            
        if self.target_size_kb < 0:
            self.target_size_kb = self.DEFAULT_TARGET_SIZE_KB
    
    def reset_to_defaults(self):
        """設定をデフォルト値にリセット"""
        self.quality = self.DEFAULT_QUALITY
        self.output_format = self.DEFAULT_FORMAT
        self.resize_mode = self.DEFAULT_RESIZE_MODE
        self.resize_width = self.DEFAULT_WIDTH
        self.target_size_kb = self.DEFAULT_TARGET_SIZE_KB
    
    def to_dict(self) -> Dict[str, Any]:
        """設定を辞書形式に変換"""
        return {
            "quality": self.quality,
            "output_format": self.output_format,
            "resize_mode": self.resize_mode,
            "resize_width": self.resize_width,
            "target_size_kb": self.target_size_kb,
            "last_input_path": self.last_input_path,
            "last_output_path": self.last_output_path,
            "window_geometry": self.window_geometry
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ImageProcessingConfig':
        """辞書から設定を復元"""
        config = cls()
        
        # 安全に値を設定
        if "quality" in data:
            config.quality = data["quality"]
        if "output_format" in data:
            config.output_format = data["output_format"]
        if "resize_mode" in data:
            config.resize_mode = data["resize_mode"]
        if "resize_width" in data:
            config.resize_width = data["resize_width"]
        if "target_size_kb" in data:
            config.target_size_kb = data["target_size_kb"]
        if "last_input_path" in data:
            config.last_input_path = data["last_input_path"]
        if "last_output_path" in data:
            config.last_output_path = data["last_output_path"]
        if "window_geometry" in data:
            config.window_geometry = data["window_geometry"]
            
        config.validate()
        return config
    
    def save_to_file(self, filepath: Path):
        """設定をファイルに保存"""
        filepath = Path(filepath)
        filepath.parent.mkdir(parents=True, exist_ok=True)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(self.to_dict(), f, indent=2, ensure_ascii=False)
    
    @classmethod
    def load_from_file(cls, filepath: Path) -> 'ImageProcessingConfig':
        """ファイルから設定を読み込み"""
        filepath = Path(filepath)
        
        if not filepath.exists():
            return cls()  # デフォルト設定を返す
            
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return cls.from_dict(data)
        except (json.JSONDecodeError, KeyError, ValueError):
            # 読み込みエラーの場合はデフォルト設定を返す
            return cls()
    
    def get_format_for_core(self) -> str:
        """resize_core用のフォーマット文字列を取得"""
        return self.output_format if self.output_format != "original" else "original"
    
    def get_resize_params(self) -> Dict[str, Any]:
        """リサイズ用パラメータを取得"""
        return {
            "resize_mode": "none" if self.resize_mode == "none" else "width",
            "resize_value": self.resize_width if self.resize_mode == "width" else None
        }


class ConfigManager:
    """設定の保存と読み込みを管理するクラス"""
    
    def __init__(self, config_path: Optional[Path] = None):
        """
        Args:
            config_path: 設定ファイルのパス（省略時はホームディレクトリ/.karukuresize/config.json）
        """
        if config_path is None:
            self.config_path = Path.home() / ".karukuresize" / "config.json"
        else:
            self.config_path = Path(config_path)
        
        self.config = self.load()
    
    def load(self) -> ImageProcessingConfig:
        """設定を読み込み"""
        return ImageProcessingConfig.load_from_file(self.config_path)
    
    def save(self):
        """現在の設定を保存"""
        self.config.save_to_file(self.config_path)
    
    def reset(self):
        """設定をリセット"""
        self.config.reset_to_defaults()
        self.save()