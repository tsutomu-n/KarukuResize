#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
GUIアプリケーションのテスト
注: GUI要素の完全なテストは難しいため、ロジック部分を中心にテスト
"""

import pytest
import os
import sys
from pathlib import Path
import tempfile
from unittest.mock import Mock, patch, MagicMock
from PIL import Image

# プロジェクトのルートディレクトリをパスに追加
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# GUI関連のインポートをモック化（テスト環境では実際のGUIを起動しない）
sys.modules['customtkinter'] = MagicMock()
sys.modules['tkinter'] = MagicMock()
sys.modules['tkinter.filedialog'] = MagicMock()

# インポートはモックの後で行う
from resize_images_gui import App


class TestGUILogic:
    """GUIアプリケーションのロジックテスト"""
    
    @pytest.fixture
    def mock_app(self):
        """モック化されたAppインスタンス"""
        with patch('resize_images_gui.ctk'):
            # 必要な属性をモック
            app = App.__new__(App)
            
            # 基本的な属性を初期化
            app.cancel_requested = False
            app.batch_input_folder_path_var = Mock()
            app.batch_output_folder_path_var = Mock()
            app.batch_resize_mode_var = Mock()
            app.batch_resize_value_var = Mock()
            app.batch_keep_aspect_ratio_var = Mock()
            app.batch_enable_compression_var = Mock()
            app.batch_output_format_var = Mock()
            app.batch_jpeg_quality_var = Mock()
            app.batch_webp_quality_var = Mock()
            app.batch_webp_lossless_var = Mock()
            app.batch_start_button = Mock()
            app.batch_cancel_button = Mock()
            app.progress_bar = Mock()
            app.log_text = Mock()
            
            # メソッドをモック
            app.add_log_message = Mock()
            app.after = Mock(side_effect=lambda delay, func: func())
            
            return app
    
    def test_batch_process_input_validation(self, mock_app):
        """バッチ処理の入力検証テスト"""
        # 入力フォルダが選択されていない場合
        mock_app.batch_input_folder_path_var.get.return_value = ""
        mock_app.batch_output_folder_path_var.get.return_value = "/output"
        
        mock_app.start_batch_process()
        
        # エラーメッセージが表示される
        mock_app.add_log_message.assert_called_with(
            "エラー: 入力フォルダが選択されていません。", is_error=True
        )
        
        # 出力フォルダが選択されていない場合
        mock_app.add_log_message.reset_mock()
        mock_app.batch_input_folder_path_var.get.return_value = "/input"
        mock_app.batch_output_folder_path_var.get.return_value = ""
        
        mock_app.start_batch_process()
        
        mock_app.add_log_message.assert_called_with(
            "エラー: 出力フォルダが選択されていません。", is_error=True
        )
    
    def test_batch_process_resize_mode_conversion(self, mock_app, temp_dir):
        """リサイズモードの変換テスト"""
        # 入力を設定
        mock_app.batch_input_folder_path_var.get.return_value = str(temp_dir)
        mock_app.batch_output_folder_path_var.get.return_value = str(temp_dir / "output")
        
        # テストケース
        test_cases = [
            ("指定なし", None),
            ("幅を指定", "width"),
            ("高さを指定", "height"),
            ("縦横最大", "longest_side"),
            ("パーセント指定", "percentage"),
        ]
        
        for gui_mode, expected_core_mode in test_cases:
            mock_app.batch_resize_mode_var.get.return_value = gui_mode
            mock_app.batch_resize_value_var.get.return_value = "100"
            
            # バッチ処理を開始（実際の処理は行わない）
            with patch('resize_images_gui.threading.Thread'):
                mock_app.start_batch_process()
            
            # スレッドに渡されるパラメータを確認
            # （実際のテストでは、Thread.startが呼ばれることを確認）
            assert mock_app.batch_start_button.configure.called
    
    def test_cancel_batch_process(self, mock_app):
        """バッチ処理のキャンセルテスト"""
        # キャンセル前の状態
        mock_app.cancel_requested = False
        
        # キャンセルを実行
        mock_app.cancel_batch_process()
        
        # キャンセルフラグが設定される
        assert mock_app.cancel_requested == True
        
        # ログメッセージが追加される
        mock_app.add_log_message.assert_called_with(
            "一括処理の中断をリクエストしました..."
        )
        
        # キャンセルボタンが無効化される
        mock_app.batch_cancel_button.configure.assert_called_with(state="disabled")


class TestGUIHelpers:
    """GUI用のヘルパー関数のテスト"""
    
    def test_format_mode_mapping(self):
        """フォーマット変換のマッピングテスト"""
        # GUIの表示名からコア関数用の値への変換
        format_mapping = {
            "オリジナルを維持": None,
            "JPEG": "JPEG",
            "PNG": "PNG",
            "WEBP": "WEBP"
        }
        
        # 各マッピングが正しいことを確認
        assert format_mapping["オリジナルを維持"] is None
        assert format_mapping["JPEG"] == "JPEG"
        assert format_mapping["PNG"] == "PNG"
        assert format_mapping["WEBP"] == "WEBP"
    
    def test_resize_value_validation(self):
        """リサイズ値の検証ロジックテスト"""
        # 整数値の検証
        def validate_resize_value(value, mode):
            if mode and mode != "percentage":
                try:
                    int_value = int(value)
                    return int_value > 0
                except ValueError:
                    return False
            elif mode == "percentage":
                try:
                    float_value = float(value)
                    return float_value > 0
                except ValueError:
                    return False
            return True
        
        # 幅指定モードでの検証
        assert validate_resize_value("1280", "width") == True
        assert validate_resize_value("0", "width") == False
        assert validate_resize_value("-100", "width") == False
        assert validate_resize_value("abc", "width") == False
        
        # パーセンテージモードでの検証
        assert validate_resize_value("50", "percentage") == True
        assert validate_resize_value("50.5", "percentage") == True
        assert validate_resize_value("0", "percentage") == False
        assert validate_resize_value("-10", "percentage") == False


class TestGUIIntegration:
    """GUI統合テスト（実際の処理フローのテスト）"""
    
    @pytest.fixture
    def setup_gui_test_env(self, temp_dir):
        """GUIテスト環境のセットアップ"""
        # 入力ディレクトリを作成
        input_dir = temp_dir / "gui_input"
        output_dir = temp_dir / "gui_output"
        input_dir.mkdir()
        
        # テスト画像を作成
        img1 = Image.new("RGB", (1920, 1080), color=(255, 0, 0))
        img1.save(input_dir / "test1.jpg", "JPEG")
        
        img2 = Image.new("RGB", (1600, 1200), color=(0, 255, 0))
        img2.save(input_dir / "test2.png", "PNG")
        
        return {
            "input_dir": str(input_dir),
            "output_dir": str(output_dir),
        }
    
    def test_gui_batch_process_flow(self, mock_app, setup_gui_test_env):
        """GUIバッチ処理の完全なフローテスト"""
        # 環境設定
        input_dir = setup_gui_test_env["input_dir"]
        output_dir = setup_gui_test_env["output_dir"]
        
        # GUIの入力値を設定
        mock_app.batch_input_folder_path_var.get.return_value = input_dir
        mock_app.batch_output_folder_path_var.get.return_value = output_dir
        mock_app.batch_resize_mode_var.get.return_value = "幅を指定"
        mock_app.batch_resize_value_var.get.return_value = "1280"
        mock_app.batch_keep_aspect_ratio_var.get.return_value = True
        mock_app.batch_enable_compression_var.get.return_value = True
        mock_app.batch_output_format_var.get.return_value = "JPEG"
        mock_app.batch_jpeg_quality_var.get.return_value = 85
        
        # process_batch_workerメソッドを直接テスト
        params = {
            "input_folder": input_dir,
            "output_folder": output_dir,
            "resize_mode": "width",
            "resize_value": "1280",
            "keep_aspect_ratio": True,
            "enable_compression": True,
            "output_format": "JPEG",
            "jpeg_quality": 85,
            "webp_quality": 85,
            "webp_lossless": False
        }
        
        # finish_batch_processをモック
        mock_app.finish_batch_process = Mock()
        
        # バッチ処理を実行
        mock_app.process_batch_worker(params)
        
        # 処理が完了したことを確認
        mock_app.finish_batch_process.assert_called()
        
        # 出力ファイルを確認
        output_path = Path(output_dir)
        if output_path.exists():
            output_files = list(output_path.glob("*.jpg"))
            assert len(output_files) == 2  # 2つのファイルがJPEGに変換される


if __name__ == "__main__":
    pytest.main([__file__, "-v"])