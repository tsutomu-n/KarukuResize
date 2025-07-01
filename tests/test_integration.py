#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
統合テスト
実際のワークフローに基づいたEnd-to-Endテスト
"""

import pytest
import os
import sys
from pathlib import Path
import tempfile
import shutil
from PIL import Image
import subprocess

# プロジェクトのルートディレクトリをパスに追加
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from resize_core import (
    find_image_files,
    resize_and_compress_image,
    get_destination_path,
    format_file_size,
)


class TestCLIIntegration:
    """CLIツールの統合テスト"""
    
    @pytest.fixture
    def setup_test_images(self, temp_dir):
        """テスト用の画像ファイル構造を作成"""
        # ディレクトリ構造を作成
        input_dir = temp_dir / "input"
        output_dir = temp_dir / "output"
        input_dir.mkdir()
        output_dir.mkdir()
        
        # サブディレクトリを作成
        subdir1 = input_dir / "subdir1"
        subdir2 = input_dir / "subdir2"
        subdir1.mkdir()
        subdir2.mkdir()
        
        # 画像ファイルを作成
        created_files = []
        
        # ルートディレクトリに画像
        img1 = Image.new("RGB", (2000, 1500), color=(255, 0, 0))
        img1_path = input_dir / "image1.jpg"
        img1.save(img1_path, "JPEG")
        created_files.append(img1_path)
        
        # サブディレクトリ1に画像
        img2 = Image.new("RGB", (1920, 1080), color=(0, 255, 0))
        img2_path = subdir1 / "image2.png"
        img2.save(img2_path, "PNG")
        created_files.append(img2_path)
        
        # サブディレクトリ2に画像
        img3 = Image.new("RGB", (3000, 2000), color=(0, 0, 255))
        img3_path = subdir2 / "image3.webp"
        img3.save(img3_path, "WEBP")
        created_files.append(img3_path)
        
        # 日本語ファイル名の画像
        img4 = Image.new("RGB", (1600, 1200), color=(255, 255, 0))
        img4_path = input_dir / "テスト画像.jpg"
        img4.save(img4_path, "JPEG")
        created_files.append(img4_path)
        
        return {
            "input_dir": input_dir,
            "output_dir": output_dir,
            "files": created_files
        }
    
    def test_cli_basic_workflow(self, setup_test_images):
        """基本的なCLIワークフローのテスト"""
        input_dir = setup_test_images["input_dir"]
        output_dir = setup_test_images["output_dir"]
        
        # CLIスクリプトを実行
        cmd = [
            sys.executable,
            "resize_images.py",
            "-s", str(input_dir),
            "-d", str(output_dir),
            "-w", "1280",
            "-q", "85"
        ]
        
        # テスト環境でCLIが実行できるか確認
        cli_script = Path("resize_images.py")
        if cli_script.exists():
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            # 成功を確認
            assert result.returncode == 0
            
            # 出力ファイルが作成されているか確認
            output_files = list(output_dir.rglob("*"))
            image_files = [f for f in output_files if f.is_file() and f.suffix.lower() in [".jpg", ".jpeg", ".png", ".webp"]]
            assert len(image_files) == 4  # 入力と同じ数のファイル
            
            # リサイズされているか確認
            for output_file in image_files:
                img = Image.open(output_file)
                assert img.width <= 1280  # 指定した幅以下
    
    def test_cli_dry_run(self, setup_test_images):
        """ドライランモードのテスト"""
        input_dir = setup_test_images["input_dir"]
        output_dir = setup_test_images["output_dir"]
        
        # CLIスクリプトを実行（ドライランモード）
        cmd = [
            sys.executable,
            "resize_images.py",
            "-s", str(input_dir),
            "-d", str(output_dir),
            "-w", "800",
            "--dry-run"
        ]
        
        cli_script = Path("resize_images.py")
        if cli_script.exists():
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            # 成功を確認
            assert result.returncode == 0
            
            # 出力ファイルが作成されていないことを確認
            output_files = list(output_dir.rglob("*"))
            assert len(output_files) == 0  # ドライランなのでファイルは作成されない


class TestBatchProcessing:
    """バッチ処理の統合テスト"""
    
    def test_batch_processing_workflow(self, temp_dir, sample_images):
        """バッチ処理の完全なワークフローテスト"""
        input_dir = temp_dir / "batch_input"
        output_dir = temp_dir / "batch_output"
        input_dir.mkdir()
        
        # サンプル画像を入力ディレクトリにコピー
        for format_name, image_path in sample_images.items():
            shutil.copy(image_path, input_dir / image_path.name)
        
        # 画像ファイルを検索
        image_files = find_image_files(str(input_dir))
        assert len(image_files) > 0
        
        # 各画像を処理
        processed_count = 0
        error_count = 0
        total_size_before = 0
        total_size_after = 0
        
        for source_path in image_files:
            # ファイルサイズを記録
            size_before = source_path.stat().st_size
            total_size_before += size_before
            
            # 出力パスを生成
            dest_path = get_destination_path(source_path, str(input_dir), str(output_dir))
            
            # ディレクトリを作成
            dest_path.parent.mkdir(parents=True, exist_ok=True)
            
            # リサイズと圧縮
            try:
                success, skipped, size_kb = resize_and_compress_image(
                    source_path=source_path,
                    dest_path=dest_path,
                    target_width=1024,
                    quality=80,
                    format="original",
                    dry_run=False
                )
                
                if success:
                    processed_count += 1
                    if dest_path.exists():
                        size_after = dest_path.stat().st_size
                        total_size_after += size_after
                else:
                    error_count += 1
                    
            except Exception as e:
                error_count += 1
        
        # 結果を検証
        assert processed_count > 0
        assert error_count == 0
        assert total_size_after < total_size_before  # 圧縮されている
        
        # 出力ファイルを確認
        output_files = list(Path(output_dir).rglob("*"))
        output_images = [f for f in output_files if f.is_file() and f.suffix.lower() in [".jpg", ".jpeg", ".png", ".webp", ".gif"]]
        assert len(output_images) == processed_count


class TestErrorHandling:
    """エラーハンドリングの統合テスト"""
    
    def test_invalid_input_handling(self, temp_dir):
        """無効な入力に対するエラーハンドリング"""
        # 存在しないファイル
        non_existent = temp_dir / "non_existent.jpg"
        output_path = temp_dir / "output.jpg"
        
        with pytest.raises(FileNotFoundError):
            resize_and_compress_image(
                source_path=non_existent,
                dest_path=output_path,
                target_width=1000,
                quality=80,
                dry_run=False
            )
    
    def test_corrupted_image_handling(self, temp_dir):
        """破損した画像ファイルの処理"""
        # 不正な画像ファイルを作成
        corrupted_path = temp_dir / "corrupted.jpg"
        corrupted_path.write_text("This is not an image")
        output_path = temp_dir / "output.jpg"
        
        # エラーが発生することを確認
        with pytest.raises(Exception):
            resize_and_compress_image(
                source_path=corrupted_path,
                dest_path=output_path,
                target_width=1000,
                quality=80,
                dry_run=False
            )
    
    def test_permission_error_handling(self, temp_dir):
        """権限エラーのハンドリング（Unix系のみ）"""
        if os.name == 'posix':  # Unix系OSの場合のみ
            # 読み取り専用ディレクトリを作成
            readonly_dir = temp_dir / "readonly"
            readonly_dir.mkdir()
            os.chmod(readonly_dir, 0o444)
            
            # 画像を作成
            img_path = temp_dir / "test.jpg"
            img = Image.new("RGB", (100, 100), color="red")
            img.save(img_path)
            
            output_path = readonly_dir / "output.jpg"
            
            # 権限エラーが発生することを確認
            try:
                resize_and_compress_image(
                    source_path=img_path,
                    dest_path=output_path,
                    target_width=50,
                    quality=80,
                    dry_run=False
                )
                assert False, "権限エラーが発生するはず"
            except (PermissionError, OSError):
                pass  # 期待通りのエラー
            finally:
                # 権限を戻す
                os.chmod(readonly_dir, 0o755)


class TestPerformance:
    """パフォーマンステスト"""
    
    def test_large_image_processing(self, temp_dir):
        """大きな画像の処理性能テスト"""
        # 大きな画像を作成（4K解像度）
        large_img_path = temp_dir / "large.jpg"
        img = Image.new("RGB", (3840, 2160), color=(100, 100, 100))
        img.save(large_img_path, "JPEG", quality=95)
        
        output_path = temp_dir / "large_output.jpg"
        
        import time
        start_time = time.time()
        
        success, skipped, size_kb = resize_and_compress_image(
            source_path=large_img_path,
            dest_path=output_path,
            target_width=1920,
            quality=85,
            dry_run=False
        )
        
        processing_time = time.time() - start_time
        
        assert success == True
        assert processing_time < 5.0  # 5秒以内に処理完了
        
        # サイズが削減されているか確認
        original_size = large_img_path.stat().st_size
        new_size = output_path.stat().st_size
        assert new_size < original_size
    
    def test_batch_performance(self, temp_dir):
        """複数ファイルの処理性能テスト"""
        # 複数の画像を作成
        num_images = 10
        for i in range(num_images):
            img_path = temp_dir / f"image_{i}.jpg"
            img = Image.new("RGB", (1920, 1080), color=(i*25, i*25, i*25))
            img.save(img_path, "JPEG")
        
        import time
        start_time = time.time()
        
        # 全画像を処理
        image_files = find_image_files(str(temp_dir))
        for source_path in image_files:
            output_path = source_path.with_stem(f"{source_path.stem}_resized")
            resize_and_compress_image(
                source_path=source_path,
                dest_path=output_path,
                target_width=1280,
                quality=80,
                dry_run=False
            )
        
        total_time = time.time() - start_time
        avg_time = total_time / num_images
        
        # 1画像あたり平均2秒以内
        assert avg_time < 2.0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])