"""
リサイズ設定のデータモデル
"""
from dataclasses import dataclass, field
from typing import Optional
from pathlib import Path


@dataclass
class ResizeSettings:
    """画像リサイズの設定"""
    # リサイズ設定
    resize_mode: str = "none"
    resize_value: int = 0
    maintain_aspect_ratio: bool = True
    
    # 品質設定
    quality: int = 85
    output_format: str = "original"
    
    # ファイル設定
    prefix: str = ""
    suffix: str = "_resized"
    overwrite: bool = False
    
    # メタデータ設定
    preserve_metadata: bool = True
    
    # 高度な設定
    lanczos_filter: bool = True
    optimize: bool = True
    progressive: bool = False
    webp_lossless: bool = False
    
    def validate(self) -> tuple[bool, Optional[str]]:
        """設定の妥当性を検証"""
        if self.resize_mode != "none" and self.resize_value <= 0:
            return False, "リサイズ値は正の数値である必要があります"
        
        if self.quality < 1 or self.quality > 100:
            return False, "品質は1〜100の範囲で指定してください"
        
        if self.output_format not in ["original", "jpeg", "png", "webp"]:
            return False, "サポートされていない出力形式です"
        
        return True, None
    
    def to_dict(self) -> dict:
        """辞書形式に変換"""
        return {
            "resize_mode": self.resize_mode,
            "resize_value": self.resize_value,
            "maintain_aspect_ratio": self.maintain_aspect_ratio,
            "quality": self.quality,
            "output_format": self.output_format,
            "prefix": self.prefix,
            "suffix": self.suffix,
            "overwrite": self.overwrite,
            "preserve_metadata": self.preserve_metadata,
            "lanczos_filter": self.lanczos_filter,
            "optimize": self.optimize,
            "progressive": self.progressive,
            "webp_lossless": self.webp_lossless
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'ResizeSettings':
        """辞書から作成"""
        return cls(
            resize_mode=data.get("resize_mode", "none"),
            resize_value=data.get("resize_value", 0),
            maintain_aspect_ratio=data.get("maintain_aspect_ratio", True),
            quality=data.get("quality", 85),
            output_format=data.get("output_format", "original"),
            prefix=data.get("prefix", ""),
            suffix=data.get("suffix", "_resized"),
            overwrite=data.get("overwrite", False),
            preserve_metadata=data.get("preserve_metadata", True),
            lanczos_filter=data.get("lanczos_filter", True),
            optimize=data.get("optimize", True),
            progressive=data.get("progressive", False),
            webp_lossless=data.get("webp_lossless", False)
        )


@dataclass
class BatchSettings(ResizeSettings):
    """バッチ処理の設定"""
    # バッチ処理固有の設定
    recursive: bool = False
    extensions: set = field(default_factory=lambda: {'.jpg', '.jpeg', '.png', '.webp', '.bmp', '.gif'})
    max_files: int = 1000
    skip_errors: bool = True
    create_subdirectory: bool = False
    subdirectory_name: str = "resized"
    
    def validate(self) -> tuple[bool, Optional[str]]:
        """バッチ設定の検証"""
        # 基本設定の検証
        is_valid, error_msg = super().validate()
        if not is_valid:
            return is_valid, error_msg
        
        # バッチ固有の検証
        if self.max_files < 1:
            return False, "最大ファイル数は1以上である必要があります"
        
        if not self.extensions:
            return False, "処理する拡張子を指定してください"
        
        return True, None


@dataclass
class ProcessingResult:
    """処理結果"""
    success: bool
    source_path: Path
    output_path: Optional[Path] = None
    error_message: Optional[str] = None
    processing_time: float = 0.0
    original_size: int = 0
    output_size: int = 0
    
    @property
    def size_reduction_percent(self) -> float:
        """サイズ削減率を計算"""
        if self.original_size == 0:
            return 0.0
        return ((self.original_size - self.output_size) / self.original_size) * 100
    
    def to_dict(self) -> dict:
        """辞書形式に変換"""
        return {
            "success": self.success,
            "source_path": str(self.source_path),
            "output_path": str(self.output_path) if self.output_path else None,
            "error_message": self.error_message,
            "processing_time": self.processing_time,
            "original_size": self.original_size,
            "output_size": self.output_size,
            "size_reduction_percent": self.size_reduction_percent
        }