#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
UIパラメータ抽出モジュール

UIウィジェットから処理パラメータを統一的に抽出します。
重複コードを削減し、パラメータ取得ロジックを一元化します。
"""

from typing import Dict, Any, Optional
from pathlib import Path
import customtkinter as ctk
from ..image_processing_config import ImageProcessingConfig


class UIParameterExtractor:
    """UIから処理パラメータを抽出するクラス"""
    
    def __init__(self, config: ImageProcessingConfig):
        """
        Args:
            config: 画像処理設定オブジェクト
        """
        self.config = config
    
    def get_resize_value(self, resize_mode: str, width_entry: ctk.CTkEntry, 
                        default_width: Optional[int] = None) -> Optional[int]:
        """
        統一されたリサイズ値取得メソッド
        
        Args:
            resize_mode: リサイズモード ("none" or "width")
            width_entry: 幅入力フィールド
            default_width: デフォルト幅（省略時は設定値を使用）
            
        Returns:
            リサイズ値（リサイズしない場合はNone）
        """
        if resize_mode != "width":
            return None
        
        if default_width is None:
            default_width = self.config.resize_width
        
        try:
            entry_value = width_entry.get().strip()
            if entry_value:
                value = int(entry_value)
                # 妥当性チェック
                if value > 0:
                    return value
            return default_width
        except (ValueError, AttributeError):
            return default_width
    
    def get_target_size_kb(self, target_size_entry: ctk.CTkEntry) -> int:
        """
        目標ファイルサイズを取得
        
        Args:
            target_size_entry: 目標サイズ入力フィールド
            
        Returns:
            目標ファイルサイズ（KB）、0は無制限
        """
        try:
            entry_value = target_size_entry.get().strip()
            if entry_value:
                value = int(entry_value)
                return max(0, value)  # 負の値は0に
            return 0
        except (ValueError, AttributeError):
            return 0
    
    def get_quality_value(self, quality_slider: ctk.CTkSlider) -> int:
        """
        品質値を取得
        
        Args:
            quality_slider: 品質スライダー
            
        Returns:
            品質値（1-100）
        """
        try:
            value = int(quality_slider.get())
            return max(1, min(100, value))  # 1-100の範囲に制限
        except (ValueError, AttributeError):
            return self.config.DEFAULT_QUALITY
    
    def get_output_format(self, format_var: ctk.StringVar) -> str:
        """
        出力フォーマットを取得
        
        Args:
            format_var: フォーマット選択変数
            
        Returns:
            出力フォーマット文字列
        """
        format_map = {
            "元の形式": "original",
            "JPEG": "jpeg",
            "PNG": "png",
            "WebP": "webp"
        }
        
        try:
            selected = format_var.get()
            return format_map.get(selected, "original")
        except AttributeError:
            return "original"
    
    def get_resize_mode(self, resize_var: ctk.StringVar) -> str:
        """
        リサイズモードを取得
        
        Args:
            resize_var: リサイズモード選択変数
            
        Returns:
            リサイズモード文字列
        """
        mode_map = {
            "変更しない": "none",
            "幅を指定": "width"
        }
        
        try:
            selected = resize_var.get()
            return mode_map.get(selected, "none")
        except AttributeError:
            return "none"
    
    def get_processing_params(self, ui_widgets: Dict[str, Any]) -> Dict[str, Any]:
        """
        処理用パラメータを統一取得
        
        Args:
            ui_widgets: UIウィジェットの辞書
                - quality_slider: 品質スライダー
                - format_var: フォーマット選択変数
                - resize_var: リサイズモード選択変数
                - width_entry: 幅入力フィールド
                - target_size_entry: 目標サイズ入力フィールド（オプション）
                
        Returns:
            処理パラメータの辞書
        """
        # 基本パラメータの取得
        quality = self.get_quality_value(ui_widgets.get("quality_slider"))
        output_format = self.get_output_format(ui_widgets.get("format_var"))
        resize_mode = self.get_resize_mode(ui_widgets.get("resize_var"))
        
        # リサイズ値の取得
        resize_value = self.get_resize_value(
            resize_mode,
            ui_widgets.get("width_entry"),
            self.config.resize_width
        )
        
        # 目標サイズの取得（オプション）
        target_size_kb = 0
        if "target_size_entry" in ui_widgets:
            target_size_kb = self.get_target_size_kb(ui_widgets["target_size_entry"])
        
        # resize_core用のパラメータに変換
        actual_resize_mode = "none" if resize_mode == "none" else "width"
        
        return {
            "resize_mode": actual_resize_mode,
            "resize_value": resize_value,
            "quality": quality,
            "output_format": output_format,
            "target_size_kb": target_size_kb,
            # UI表示用の元の値も保持
            "original_resize_mode": resize_mode,
            "original_format": ui_widgets.get("format_var", ctk.StringVar()).get() if "format_var" in ui_widgets else "元の形式"
        }
    
    def update_config_from_ui(self, ui_widgets: Dict[str, Any]):
        """
        UIの値から設定を更新
        
        Args:
            ui_widgets: UIウィジェットの辞書
        """
        params = self.get_processing_params(ui_widgets)
        
        self.config.quality = params["quality"]
        self.config.output_format = params["output_format"]
        self.config.resize_mode = params["original_resize_mode"]
        self.config.resize_width = params["resize_value"] or self.config.DEFAULT_WIDTH
        self.config.target_size_kb = params["target_size_kb"]
    
    def validate_input_output_paths(self, input_path: Optional[str], 
                                  output_path: Optional[str] = None) -> tuple[bool, str]:
        """
        入出力パスの妥当性を検証
        
        Args:
            input_path: 入力ファイルパス
            output_path: 出力ファイルパス（オプション）
            
        Returns:
            (検証成功, エラーメッセージ)
        """
        if not input_path:
            return False, "入力ファイルが選択されていません"
        
        input_path_obj = Path(input_path)
        if not input_path_obj.exists():
            return False, f"入力ファイルが存在しません: {input_path}"
        
        if not input_path_obj.is_file():
            return False, f"入力パスがファイルではありません: {input_path}"
        
        # 画像ファイルかチェック
        valid_extensions = {'.jpg', '.jpeg', '.png', '.webp', '.bmp', '.gif'}
        if input_path_obj.suffix.lower() not in valid_extensions:
            return False, f"サポートされていないファイル形式です: {input_path_obj.suffix}"
        
        # 出力パスの検証（指定されている場合）
        if output_path:
            output_path_obj = Path(output_path)
            output_dir = output_path_obj.parent
            
            if not output_dir.exists():
                try:
                    output_dir.mkdir(parents=True, exist_ok=True)
                except Exception as e:
                    return False, f"出力ディレクトリの作成に失敗しました: {e}"
        
        return True, ""
