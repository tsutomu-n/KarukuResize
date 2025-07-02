#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
resize_core.py のユニットテスト
"""

import pytest
import os
import sys
from pathlib import Path
import tempfile
import shutil
from PIL import Image

# プロジェクトのルートディレクトリをパスに追加
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from resize_core import (
    sanitize_filename,
    get_system_encoding,
    normalize_path,
    format_file_size,
    find_image_files,
    get_destination_path,
    resize_and_compress_image,
    calculate_reduction_rate,
    get_directory_size,
    create_directory_with_permissions,
)


class TestSanitizeFilename:
    """sanitize_filename 関数のテスト"""
    
    def test_normal_filename(self):
        """通常のファイル名はそのまま返される"""
        assert sanitize_filename("test.jpg") == "test.jpg"
        assert sanitize_filename("image_001.png") == "image_001.png"
        
    def test_japanese_filename(self):
        """日本語ファイル名が正しく処理される"""
        assert sanitize_filename("テスト画像.jpg") == "テスト画像.jpg"
        assert sanitize_filename("寿司🍣.png") == "寿司🍣.png"
        
    def test_invalid_characters(self):
        """無効な文字が置換される"""
        assert sanitize_filename('test<>:"/\\|?*.jpg') == "test________.jpg"
        assert sanitize_filename("test\x00file.jpg") == "test_file.jpg"
        
    def test_windows_reserved_names(self):
        """Windowsの予約語が処理される"""
        assert sanitize_filename("CON.jpg") == "_CON.jpg"
        assert sanitize_filename("AUX.png") == "_AUX.png"
        assert sanitize_filename("NUL.txt") == "_NUL.txt"
        
    def test_max_length(self):
        """最大長を超えるファイル名が切り詰められる"""
        long_name = "a" * 300 + ".jpg"
        result = sanitize_filename(long_name)
        # 拡張子を除いた部分が250文字以下になっていることを確認
        name_without_ext = result.rsplit(".", 1)[0]
        assert len(name_without_ext) <= 250
        assert result.endswith(".jpg")
        
    def test_unicode_normalization(self):
        """Unicode正規化が行われる"""
        # 濁点の分離形と結合形
        assert sanitize_filename("がぎぐげご.jpg") == sanitize_filename("がぎぐげご.jpg")


class TestPathOperations:
    """パス操作関連の関数のテスト"""
    
    def test_normalize_path(self):
        """パスの正規化テスト"""
        # 通常のパス
        result = normalize_path("/home/user/test.jpg")
        assert isinstance(result, Path)
        
        # 相対パス
        result = normalize_path("./test.jpg")
        assert isinstance(result, Path)
        
        # Path オブジェクト
        path_obj = Path("/home/user/test.jpg")
        result = normalize_path(path_obj)
        assert result == path_obj
        
    def test_get_destination_path(self):
        """出力パスの生成テスト"""
        source = Path("/input/subdir/test.jpg")
        source_dir = "/input"
        dest_dir = "/output"
        
        result = get_destination_path(source, source_dir, dest_dir)
        assert str(result) == str(Path("/output/subdir/test.jpg"))
        
        # 異なる拡張子
        source = Path("/input/test.png")
        result = get_destination_path(source, "/input", "/output")
        assert result.suffix == ".png"


class TestFileOperations:
    """ファイル操作関連の関数のテスト"""
    
    def test_format_file_size(self):
        """ファイルサイズのフォーマットテスト"""
        assert format_file_size(0) == "0 B"
        assert format_file_size(1023) == "1023 B"
        assert format_file_size(1024) == "1.0 KB"
        assert format_file_size(1024 * 1024) == "1.0 MB"
        assert format_file_size(1024 * 1024 * 1024) == "1.0 GB"
        assert format_file_size(1536) == "1.5 KB"
        
    def test_calculate_reduction_rate(self):
        """削減率の計算テスト"""
        assert calculate_reduction_rate(1000, 500) == 50.0
        assert calculate_reduction_rate(1000, 1000) == 0.0
        assert calculate_reduction_rate(0, 500) == 0.0
        assert calculate_reduction_rate(1000, 0) == 100.0


class TestImageOperations:
    """画像処理関連の関数のテスト"""
    
    @pytest.fixture
    def temp_dir(self):
        """一時ディレクトリのフィクスチャ"""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir)
        
    @pytest.fixture
    def sample_image(self, temp_dir):
        """サンプル画像を作成するフィクスチャ"""
        img_path = Path(temp_dir) / "test.jpg"
        img = Image.new("RGB", (1000, 800), color="red")
        img.save(img_path, "JPEG")
        return img_path
        
    def test_find_image_files(self, temp_dir):
        """画像ファイル検索のテスト"""
        # 画像ファイルを作成
        img_files = ["test1.jpg", "test2.png", "test3.webp"]
        for filename in img_files:
            img = Image.new("RGB", (100, 100), color="blue")
            img.save(Path(temp_dir) / filename)
            
        # テキストファイルも作成（無視されるべき）
        (Path(temp_dir) / "test.txt").write_text("test")
        
        # 画像ファイルを検索
        found_files = find_image_files(temp_dir)
        found_names = [f.name for f in found_files]
        
        assert len(found_files) == 3
        for img_file in img_files:
            assert img_file in found_names
            
    def test_resize_and_compress_image_basic(self, sample_image, temp_dir):
        """基本的なリサイズと圧縮のテスト"""
        output_path = Path(temp_dir) / "output.jpg"
        
        success, skipped, size_kb = resize_and_compress_image(
            source_path=sample_image,
            dest_path=output_path,
            target_width=500,
            quality=80,
            format="jpeg",
            dry_run=False
        )
        
        assert success == True
        assert skipped == False
        assert output_path.exists()
        
        # リサイズされた画像のサイズを確認
        img = Image.open(output_path)
        assert img.width == 500
        assert img.height == 400  # アスペクト比維持
        
    def test_resize_and_compress_image_webp(self, sample_image, temp_dir):
        """WebP形式への変換テスト"""
        output_path = Path(temp_dir) / "output.webp"
        
        success, skipped, size_kb = resize_and_compress_image(
            source_path=sample_image,
            dest_path=output_path,
            target_width=500,
            quality=80,
            format="webp",
            webp_lossless=False,
            dry_run=False
        )
        
        assert success == True
        assert output_path.exists()
        assert output_path.suffix == ".webp"
        
    def test_resize_and_compress_image_dry_run(self, sample_image, temp_dir):
        """ドライランモードのテスト"""
        output_path = Path(temp_dir) / "output.jpg"
        
        result = resize_and_compress_image(
            source_path=sample_image,
            dest_path=output_path,
            target_width=500,
            quality=80,
            format="jpeg",
            dry_run=True
        )
        
        # ドライランモードでは3つの値が返される
        assert len(result) == 3
        original_size, new_size, estimated_size = result
        
        assert original_size == (1000, 800)
        assert new_size == (500, 400)
        assert not output_path.exists()  # ファイルは作成されない
        
    def test_resize_and_compress_image_skip_smaller(self, temp_dir):
        """既に小さい画像はスキップされるテスト"""
        # 小さい画像を作成
        small_img_path = Path(temp_dir) / "small.jpg"
        img = Image.new("RGB", (100, 100), color="green")
        img.save(small_img_path, "JPEG")
        
        output_path = Path(temp_dir) / "output.jpg"
        
        success, skipped, size_kb = resize_and_compress_image(
            source_path=small_img_path,
            dest_path=output_path,
            target_width=500,
            quality=80,
            format="jpeg",
            dry_run=False
        )
        
        assert success == True
        assert skipped == True
        assert output_path.exists()  # ファイルはコピーされる
        
        # サイズは変更されない
        img = Image.open(output_path)
        assert img.width == 100
        assert img.height == 100


class TestDirectoryOperations:
    """ディレクトリ操作関連の関数のテスト"""
    
    @pytest.fixture
    def temp_dir(self):
        """一時ディレクトリのフィクスチャ"""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir)
        
    def test_get_directory_size(self, temp_dir):
        """ディレクトリサイズ取得のテスト"""
        # 空のディレクトリ
        size = get_directory_size(temp_dir)
        assert size == 0
        
        # ファイルを追加
        file1 = Path(temp_dir) / "file1.txt"
        file1.write_text("Hello" * 100)
        
        file2 = Path(temp_dir) / "file2.txt"
        file2.write_text("World" * 200)
        
        size = get_directory_size(temp_dir)
        assert size > 0
        assert size == file1.stat().st_size + file2.stat().st_size
        
    def test_create_directory_with_permissions(self, temp_dir):
        """ディレクトリ作成のテスト"""
        new_dir = Path(temp_dir) / "new_folder"
        
        success, path = create_directory_with_permissions(str(new_dir))
        assert success == True
        assert Path(path).exists()
        assert Path(path).is_dir()
        
        # 既存のディレクトリ
        success, path = create_directory_with_permissions(str(new_dir))
        assert success == True
        
        # ネストしたディレクトリ
        nested_dir = Path(temp_dir) / "level1" / "level2" / "level3"
        success, path = create_directory_with_permissions(str(nested_dir))
        assert success == True
        assert Path(path).exists()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])