#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
pytest設定ファイル
共通のフィクスチャやテスト設定を定義
"""

import pytest
import tempfile
import shutil
from pathlib import Path
from PIL import Image


@pytest.fixture
def temp_dir():
    """一時ディレクトリを作成・削除するフィクスチャ"""
    temp_dir = tempfile.mkdtemp()
    yield Path(temp_dir)
    shutil.rmtree(temp_dir)


@pytest.fixture
def sample_images(temp_dir):
    """様々なフォーマットのサンプル画像を作成するフィクスチャ"""
    images = {}
    
    # JPEG画像
    jpeg_path = temp_dir / "sample.jpg"
    img = Image.new("RGB", (1920, 1080), color=(255, 0, 0))
    img.save(jpeg_path, "JPEG", quality=95)
    images["jpeg"] = jpeg_path
    
    # PNG画像
    png_path = temp_dir / "sample.png"
    img = Image.new("RGBA", (1920, 1080), color=(0, 255, 0, 255))
    img.save(png_path, "PNG")
    images["png"] = png_path
    
    # WebP画像
    webp_path = temp_dir / "sample.webp"
    img = Image.new("RGB", (1920, 1080), color=(0, 0, 255))
    img.save(webp_path, "WEBP", quality=90)
    images["webp"] = webp_path
    
    # GIF画像
    gif_path = temp_dir / "sample.gif"
    img = Image.new("P", (800, 600), color=0)
    img.save(gif_path, "GIF")
    images["gif"] = gif_path
    
    # 小さい画像（リサイズ不要）
    small_path = temp_dir / "small.jpg"
    img = Image.new("RGB", (100, 100), color=(128, 128, 128))
    img.save(small_path, "JPEG")
    images["small"] = small_path
    
    # 縦長画像
    portrait_path = temp_dir / "portrait.jpg"
    img = Image.new("RGB", (1080, 1920), color=(255, 255, 0))
    img.save(portrait_path, "JPEG")
    images["portrait"] = portrait_path
    
    return images


@pytest.fixture
def japanese_filenames():
    """日本語ファイル名のテストケース"""
    return [
        "テスト画像.jpg",
        "新しいフォルダー.png",
        "画像_001_最終版.webp",
        "お寿司🍣.jpg",
        "ファイル名 with スペース.png",
        "長い日本語ファイル名" + "あ" * 100 + ".jpg",
    ]


@pytest.fixture
def mock_settings():
    """テスト用の設定値"""
    return {
        "default_width": 1280,
        "default_quality": 85,
        "supported_formats": ["JPEG", "PNG", "WEBP", "GIF", "BMP", "TIFF"],
        "max_filename_length": 255,
    }