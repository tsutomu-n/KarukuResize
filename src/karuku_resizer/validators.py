"""
入力値検証のためのユーティリティモジュール
"""
from pathlib import Path
import re
from typing import Union, Optional

class PathValidator:
    """パス検証クラス"""
    
    # Windowsの予約語
    WINDOWS_RESERVED_NAMES = {
        "CON", "PRN", "AUX", "NUL", "COM1", "COM2", "COM3", "COM4",
        "COM5", "COM6", "COM7", "COM8", "COM9", "LPT1", "LPT2", 
        "LPT3", "LPT4", "LPT5", "LPT6", "LPT7", "LPT8", "LPT9"
    }
    
    # 無効な文字（Windows）
    INVALID_CHARS = '<>:"|?*'
    
    @classmethod
    def validate_safe_path(cls, path_str: str) -> Path:
        """安全なパスかを検証"""
        if not path_str:
            raise ValueError("パスが空です")
        
        path = Path(path_str).resolve()
        
        # パストラバーサル攻撃の防止
        try:
            # 正規化されたパスに".."が含まれているかチェック
            if ".." in path.parts:
                raise ValueError("不正なパスです（親ディレクトリへの参照を含んでいます）")
        except ValueError:
            # Windowsで異なるドライブ間の相対パスの場合
            pass
        
        # Windowsの予約語チェック
        for part in path.parts:
            if part.upper() in cls.WINDOWS_RESERVED_NAMES:
                raise ValueError(f"Windowsの予約語は使用できません: {part}")
        
        # 無効な文字チェック（ドライブレターの:は除外）
        path_str = str(path)
        for char in cls.INVALID_CHARS:
            if char == ':':
                # Windowsのドライブレター（例：C:）は許可
                # ドライブレター以外の位置にある:のみチェック
                if path_str.count(':') > 1 or (len(path_str) > 2 and ':' in path_str[2:]):
                    raise ValueError(f"パスに無効な文字が含まれています: {char}")
            elif char in path_str:
                raise ValueError(f"パスに無効な文字が含まれています: {char}")
        
        return path
    
    @classmethod
    def validate_filename(cls, filename: str) -> str:
        """ファイル名の妥当性を検証"""
        if not filename:
            raise ValueError("ファイル名が空です")
        
        # 拡張子を分離
        name_part = Path(filename).stem
        
        # Windowsの予約語チェック
        if name_part.upper() in cls.WINDOWS_RESERVED_NAMES:
            raise ValueError(f"Windowsの予約語は使用できません: {name_part}")
        
        # 無効な文字チェック
        for char in cls.INVALID_CHARS:
            if char in filename:
                raise ValueError(f"ファイル名に無効な文字が含まれています: {char}")
        
        # 長さチェック（Windowsの制限）
        if len(filename) > 255:
            raise ValueError("ファイル名が長すぎます（最大255文字）")
        
        return filename
    
    @classmethod
    def is_image_file(cls, filepath: Union[str, Path]) -> bool:
        """画像ファイルかチェック"""
        valid_extensions = {'.jpg', '.jpeg', '.png', '.webp', '.bmp', '.gif', '.tiff', '.tif'}
        return Path(filepath).suffix.lower() in valid_extensions


class ValueValidator:
    """数値検証クラス"""
    
    LIMITS = {
        "width": (1, 10000),
        "height": (1, 10000),
        "percentage": (1, 500),
        "longest_side": (1, 10000),
        "quality": (1, 100),
        "target_size_kb": (1, 100000),
        "balance": (1, 10)
    }
    
    @classmethod
    def validate_resize_value(cls, value: Union[int, float, str], mode: str) -> int:
        """リサイズ値を検証"""
        # 文字列の場合は数値に変換
        if isinstance(value, str):
            value = value.strip()
            if not value:
                raise ValueError("値が入力されていません")
            try:
                value = float(value)
            except ValueError:
                raise ValueError("数値を入力してください")
        
        # 数値チェック
        if not isinstance(value, (int, float)):
            raise ValueError("数値を入力してください")
        
        # NaNチェック
        if value != value:  # NaN check
            raise ValueError("無効な数値です")
        
        # 範囲チェック
        min_val, max_val = cls.LIMITS.get(mode, (1, 10000))
        
        if not min_val <= value <= max_val:
            raise ValueError(f"{min_val}から{max_val}の範囲で入力してください")
        
        return int(value)
    
    @classmethod
    def validate_quality(cls, value: Union[int, float, str]) -> int:
        """品質値を検証"""
        return cls.validate_resize_value(value, "quality")
    
    @classmethod
    def validate_percentage(cls, value: Union[int, float, str]) -> float:
        """パーセンテージ値を検証"""
        validated = cls.validate_resize_value(value, "percentage")
        return float(validated)
    
    @classmethod
    def validate_positive_integer(cls, value: Union[int, str], name: str = "値") -> int:
        """正の整数を検証"""
        if isinstance(value, str):
            try:
                value = int(value.strip())
            except ValueError:
                raise ValueError(f"{name}は整数を入力してください")
        
        if not isinstance(value, int) or value <= 0:
            raise ValueError(f"{name}は正の整数を入力してください")
        
        return value