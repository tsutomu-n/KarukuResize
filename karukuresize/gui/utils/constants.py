"""
UI定数とアプリケーション設定
"""
from dataclasses import dataclass
from typing import Tuple, Dict


@dataclass(frozen=True)
class WindowConfig:
    """ウィンドウ設定"""
    DEFAULT_WIDTH: int = 1000
    DEFAULT_HEIGHT: int = 900
    MIN_WIDTH: int = 900
    MIN_HEIGHT: int = 800
    TITLE: str = "画像処理ツール"


@dataclass(frozen=True)
class FontConfig:
    """フォント設定"""
    SIZE_NORMAL: int = 15
    SIZE_BUTTON: int = 15
    SIZE_HEADING: int = 18
    SIZE_SMALL: int = 13
    WEIGHT_NORMAL: str = "normal"
    WEIGHT_BOLD: str = "bold"


@dataclass(frozen=True)
class ColorTheme:
    """カラーテーマ設定"""
    BG_PRIMARY: str = "#F8F9FA"
    BG_SECONDARY: str = "#E9ECEF"
    TEXT_PRIMARY: str = "#212529"
    TEXT_SECONDARY: str = "#6C757D"
    ACCENT: str = "#6C63FF"
    ACCENT_HOVER: str = "#5A52D5"
    SUCCESS: str = "#28A745"
    ERROR: str = "#DC3545"
    WARNING: str = "#FFC107"
    BORDER_COLOR: str = "#E9ECEF"


@dataclass(frozen=True)
class ProcessingConfig:
    """処理設定"""
    MAX_BATCH_SIZE: int = 1000
    THREAD_POOL_SIZE: int = 4
    PROGRESS_UPDATE_INTERVAL: float = 0.1
    DEFAULT_QUALITY: int = 85
    MIN_QUALITY: int = 1
    MAX_QUALITY: int = 100
    DEFAULT_RESIZE_VALUE: int = 1920


# インスタンス化
WINDOW = WindowConfig()
FONT = FontConfig()
THEME = ColorTheme()
PROCESSING = ProcessingConfig()


# リサイズモードの定義
class ResizeMode:
    """リサイズモードの定数"""
    NONE = "none"
    WIDTH = "width"
    HEIGHT = "height"
    LONGEST_SIDE = "longest_side"
    PERCENTAGE = "percentage"
    
    DISPLAY_NAMES: Dict[str, str] = {
        NONE: "リサイズなし",
        WIDTH: "幅を指定",
        HEIGHT: "高さを指定",
        LONGEST_SIDE: "縦横最大",
        PERCENTAGE: "パーセント"
    }
    
    @classmethod
    def get_display_name(cls, mode: str) -> str:
        """モードの表示名を取得"""
        return cls.DISPLAY_NAMES.get(mode, mode)
    
    @classmethod
    def from_display_name(cls, display_name: str) -> str:
        """表示名から実際の値を取得"""
        for mode, name in cls.DISPLAY_NAMES.items():
            if name == display_name:
                return mode
        return cls.NONE


# 出力フォーマットの定義
class OutputFormat:
    """出力フォーマットの定数"""
    ORIGINAL = "original"
    JPEG = "jpeg"
    PNG = "png"
    WEBP = "webp"
    
    DISPLAY_NAMES: Dict[str, str] = {
        ORIGINAL: "オリジナル",
        JPEG: "JPEG",
        PNG: "PNG",
        WEBP: "WEBP"
    }
    
    @classmethod
    def get_display_name(cls, format_type: str) -> str:
        """フォーマットの表示名を取得"""
        return cls.DISPLAY_NAMES.get(format_type, format_type)
    
    @classmethod
    def from_display_name(cls, display_name: str) -> str:
        """表示名から実際の値を取得"""
        for fmt, name in cls.DISPLAY_NAMES.items():
            if name == display_name:
                return fmt
        return cls.ORIGINAL


# EXIFハンドリングモード
class ExifMode:
    """EXIF処理モードの定数"""
    KEEP = "keep"
    REMOVE = "remove"
    
    DISPLAY_NAMES: Dict[str, str] = {
        KEEP: "保持",
        REMOVE: "削除"
    }


# ファイルタイプの定義
IMAGE_FILETYPES = [
    ("画像ファイル", "*.jpg *.jpeg *.png *.gif *.bmp *.tiff *.webp"),
    ("すべてのファイル", "*.*")
]


# サポートされる画像拡張子
SUPPORTED_IMAGE_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.webp', '.bmp', '.gif', '.tiff'}


# 処理モード
class ProcessingMode:
    """処理モードの定数"""
    SINGLE = "single"
    BATCH = "batch"
    
    DISPLAY_NAMES: Dict[str, str] = {
        SINGLE: "単一ファイル",
        BATCH: "フォルダ一括処理"
    }


# UI設定
@dataclass(frozen=True)
class UIConfig:
    """UI関連の設定"""
    CORNER_RADIUS: int = 10
    BORDER_WIDTH: int = 1
    BUTTON_HEIGHT: int = 32
    ENTRY_HEIGHT: int = 32
    PADDING_SMALL: int = 5
    PADDING_MEDIUM: int = 10
    PADDING_LARGE: int = 20
    LOG_HEIGHT: int = 140
    PROGRESS_BAR_HEIGHT: int = 8


UI = UIConfig()