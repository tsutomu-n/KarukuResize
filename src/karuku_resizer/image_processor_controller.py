#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
画像処理コントローラーモジュール

画像処理のビジネスロジックを管理し、UIから分離します。
プレビューと実圧縮の処理を統一的に扱います。
"""

import io
import threading
from pathlib import Path
from typing import Dict, Any, Optional, Tuple, Callable
from PIL import Image
import time

from resize_core import resize_and_compress_image, format_file_size
from image_processing_config import ImageProcessingConfig
from ui_parameter_extractor import UIParameterExtractor


class ProcessingResult:
    """処理結果を格納するクラス"""
    
    def __init__(self, success: bool, message: str = "", **kwargs):
        self.success = success
        self.message = message
        self.data = kwargs
    
    @property
    def error_message(self) -> str:
        """エラーメッセージを取得"""
        return self.message if not self.success else ""
    
    def __bool__(self) -> bool:
        """成功/失敗を真偽値で返す"""
        return self.success


class ImageProcessorController:
    """画像処理のビジネスロジックを管理するコントローラー"""
    
    def __init__(self, config: ImageProcessingConfig, param_extractor: UIParameterExtractor):
        """
        Args:
            config: 画像処理設定
            param_extractor: パラメータ抽出器
        """
        self.config = config
        self.param_extractor = param_extractor
        self._processing_thread = None
        self._cancel_requested = False
    
    def process_preview(self, image_path: str, ui_widgets: Dict[str, Any],
                       detailed: bool = False, 
                       progress_callback: Optional[Callable[[str], None]] = None) -> ProcessingResult:
        """
        プレビュー処理を実行
        
        Args:
            image_path: 入力画像パス
            ui_widgets: UIウィジェットの辞書
            detailed: 詳細プレビュー（目標サイズ対応）
            progress_callback: 進捗通知コールバック
            
        Returns:
            ProcessingResult: 処理結果
        """
        try:
            # パラメータを取得
            params = self.param_extractor.get_processing_params(ui_widgets)
            
            # 画像を読み込み
            with Image.open(image_path) as source_image:
                original_size = Path(image_path).stat().st_size
                
                # 出力フォーマットを決定
                output_format = self._determine_output_format(image_path, params["output_format"])
                
                # 目標サイズが設定されている場合
                if detailed and params["target_size_kb"] > 0:
                    result = self._process_with_target_size(
                        source_image, 
                        params["target_size_kb"],
                        output_format,
                        params["resize_value"],
                        progress_callback
                    )
                    
                    if result:
                        return ProcessingResult(
                            success=True,
                            after_image=result[0],
                            after_size=result[1],
                            optimized_quality=result[2],
                            process_time=result[3],
                            original_size=original_size,
                            target_achieved=result[1] <= params["target_size_kb"] * 1024
                        )
                    else:
                        return ProcessingResult(
                            success=False,
                            message="目標サイズでのプレビュー生成に失敗しました"
                        )
                
                # 通常のプレビュー処理
                else:
                    output_buffer = io.BytesIO()
                    
                    # デバッグ情報
                    if progress_callback:
                        progress_callback(f"プレビュー処理: {params}")
                    
                    # メモリベース処理を実行
                    success, error_msg = resize_and_compress_image(
                        source_image=source_image.copy(),  # コピーを渡す
                        output_buffer=output_buffer,
                        resize_mode=params["resize_mode"],
                        resize_value=params["resize_value"],
                        quality=params["quality"],
                        output_format=output_format,
                        optimize=True
                    )
                    
                    if success:
                        output_buffer.seek(0)
                        after_image = Image.open(output_buffer)
                        after_size = len(output_buffer.getvalue())
                        
                        return ProcessingResult(
                            success=True,
                            after_image=after_image,
                            after_size=after_size,
                            original_size=original_size,
                            process_time=0.0  # 簡易プレビューなので計測しない
                        )
                    else:
                        return ProcessingResult(
                            success=False,
                            message=error_msg or "プレビュー生成に失敗しました"
                        )
                        
        except Exception as e:
            return ProcessingResult(
                success=False,
                message=f"プレビューエラー: {str(e)}"
            )
    
    def process_compression(self, input_path: str, output_path: str, 
                          ui_widgets: Dict[str, Any],
                          progress_callback: Optional[Callable[[str], None]] = None) -> ProcessingResult:
        """
        実圧縮処理を実行
        
        Args:
            input_path: 入力画像パス
            output_path: 出力画像パス
            ui_widgets: UIウィジェットの辞書
            progress_callback: 進捗通知コールバック
            
        Returns:
            ProcessingResult: 処理結果
        """
        try:
            # パラメータを取得
            params = self.param_extractor.get_processing_params(ui_widgets)
            
            # 出力フォーマットを決定
            format_for_core = "original"
            if params["output_format"] != "original":
                format_for_core = params["output_format"]
            
            # デバッグ情報
            if progress_callback:
                progress_callback(f"実圧縮処理: {params}")
            
            # ファイルベース処理を実行
            result = resize_and_compress_image(
                source_path=input_path,
                dest_path=output_path,
                resize_mode=params["resize_mode"],
                resize_value=params["resize_value"],
                quality=params["quality"],
                format=format_for_core
            )
            
            success = result[0] if result else False
            
            if success:
                # ファイルサイズを取得
                original_size = Path(input_path).stat().st_size
                compressed_size = Path(output_path).stat().st_size
                reduction = (1 - compressed_size / original_size) * 100
                
                return ProcessingResult(
                    success=True,
                    message=f"圧縮完了！ {format_file_size(original_size)} → {format_file_size(compressed_size)} (-{reduction:.1f}%)",
                    original_size=original_size,
                    compressed_size=compressed_size,
                    reduction_rate=reduction
                )
            else:
                return ProcessingResult(
                    success=False,
                    message="圧縮に失敗しました"
                )
                
        except Exception as e:
            return ProcessingResult(
                success=False,
                message=f"圧縮エラー: {str(e)}"
            )
    
    def process_batch(self, file_paths: list[str], output_dir: str,
                     ui_widgets: Dict[str, Any],
                     progress_callback: Optional[Callable[[int, int, str], None]] = None,
                     cancel_check: Optional[Callable[[], bool]] = None) -> ProcessingResult:
        """
        バッチ処理を実行
        
        Args:
            file_paths: 処理するファイルパスのリスト
            output_dir: 出力ディレクトリ
            ui_widgets: UIウィジェットの辞書
            progress_callback: 進捗通知コールバック(current, total, message)
            cancel_check: キャンセルチェック関数
            
        Returns:
            ProcessingResult: 処理結果
        """
        processed_count = 0
        failed_count = 0
        failed_files = []
        
        total_files = len(file_paths)
        
        for i, file_path in enumerate(file_paths):
            # キャンセルチェック
            if cancel_check and cancel_check():
                return ProcessingResult(
                    success=False,
                    message="処理がキャンセルされました",
                    processed_count=processed_count,
                    failed_count=failed_count,
                    cancelled=True
                )
            
            try:
                # 出力パスを生成
                input_path = Path(file_path)
                output_path = Path(output_dir) / input_path.name
                
                # 進捗通知
                if progress_callback:
                    progress_callback(i + 1, total_files, f"処理中: {input_path.name}")
                
                # 圧縮処理
                result = self.process_compression(
                    str(input_path),
                    str(output_path),
                    ui_widgets
                )
                
                if result.success:
                    processed_count += 1
                else:
                    failed_count += 1
                    failed_files.append(input_path.name)
                    
            except Exception as e:
                failed_count += 1
                failed_files.append(Path(file_path).name)
        
        # 結果サマリー
        if failed_count == 0:
            message = f"✅ 全{processed_count}ファイルの処理が完了しました"
        else:
            message = f"⚠️ {processed_count}ファイル処理完了、{failed_count}ファイル失敗"
            if failed_files:
                message += f"\n失敗: {', '.join(failed_files[:3])}"
                if len(failed_files) > 3:
                    message += f" 他{len(failed_files) - 3}件"
        
        return ProcessingResult(
            success=failed_count == 0,
            message=message,
            processed_count=processed_count,
            failed_count=failed_count,
            failed_files=failed_files
        )
    
    def _determine_output_format(self, input_path: str, output_format: str) -> str:
        """出力フォーマットを決定"""
        if output_format != "original":
            return output_format
        
        # 品質が50以下の場合、PNGでもJPEGでプレビュー
        input_lower = input_path.lower()
        if input_lower.endswith('.png') and self.config.quality > 50:
            return "png"
        elif input_lower.endswith('.webp'):
            return "webp"
        else:
            return "jpeg"  # デフォルトはJPEG
    
    def _process_with_target_size(self, source_image: Image.Image, target_size_kb: int,
                                 output_format: str, resize_value: Optional[int],
                                 progress_callback: Optional[Callable[[str], None]] = None) -> Optional[Tuple]:
        """目標サイズでの処理（バイナリサーチ）"""
        start_time = time.time()
        target_bytes = target_size_kb * 1024
        
        min_quality = 5
        max_quality = 95
        best_quality = self.config.quality
        best_result = None
        
        # バイナリサーチで最適な品質を探す
        for attempt in range(7):  # 最大7回試行
            output_buffer = io.BytesIO()
            
            if progress_callback:
                progress_callback(f"品質{best_quality}%で試行中... ({attempt + 1}/7)")
            
            # 処理実行
            success, _ = resize_and_compress_image(
                source_image=source_image.copy(),
                output_buffer=output_buffer,
                resize_mode="width" if resize_value else "none",
                resize_value=resize_value,
                quality=best_quality,
                output_format=output_format,
                optimize=True
            )
            
            if success:
                size = len(output_buffer.getvalue())
                
                if size <= target_bytes or attempt == 6:  # 目標達成または最終試行
                    output_buffer.seek(0)
                    after_image = Image.open(output_buffer)
                    process_time = time.time() - start_time
                    return after_image, size, best_quality, process_time
                
                # サイズが大きすぎる場合
                max_quality = best_quality - 1
            else:
                # 処理失敗の場合
                min_quality = best_quality + 1
            
            # 次の品質を計算
            if max_quality <= min_quality:
                break
            best_quality = (min_quality + max_quality) // 2
        
        return None
    
    def cancel_processing(self):
        """処理をキャンセル"""
        self._cancel_requested = True
        
    def is_processing(self) -> bool:
        """処理中かどうか"""
        return self._processing_thread is not None and self._processing_thread.is_alive()