#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
WebPロスレス設定のテスト
"""
import sys
from pathlib import Path
from PIL import Image
import tempfile

# プロジェクトルートをPythonパスに追加
project_root = Path(__file__).parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from resize_core import resize_and_compress_image
from karukuresize.models.resize_settings import ResizeSettings
from karukuresize.services.image_service import ImageService


def test_webp_lossless():
    """WebPロスレス機能のテスト"""
    print("=" * 60)
    print("WebPロスレス機能のテスト")
    print("=" * 60)
    
    # テスト画像を作成
    print("\n1. テスト画像を作成...")
    test_image = Image.new("RGB", (800, 600), color=(0, 128, 255))
    
    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as temp_src:
        test_image.save(temp_src.name, "PNG")
        
        # テスト用の設定
        settings = ResizeSettings(
            resize_mode="width",
            resize_value=400,
            quality=85,
            output_format="webp",
            webp_lossless=False
        )
        
        # ImageServiceのテスト
        print("\n2. WebP通常圧縮のテスト...")
        service = ImageService()
        
        with tempfile.TemporaryDirectory() as temp_dir:
            result = service.process_image(
                temp_src.name,
                temp_dir,
                settings
            )
            
            if result.success:
                print("   ✅ 成功")
                print(f"   出力ファイル: {result.output_path}")
                print(f"   サイズ: {result.output_size} bytes")
                
                # 画像を確認
                output_image = Image.open(result.output_path)
                print(f"   形式: {output_image.format}")
                print(f"   サイズ: {output_image.size}")
            else:
                print(f"   ❌ 失敗: {result.error_message}")
        
        # ロスレス設定でテスト
        print("\n3. WebPロスレス圧縮のテスト...")
        settings.webp_lossless = True
        
        with tempfile.TemporaryDirectory() as temp_dir:
            result = service.process_image(
                temp_src.name,
                temp_dir,
                settings
            )
            
            if result.success:
                print("   ✅ 成功")
                print(f"   出力ファイル: {result.output_path}")
                print(f"   サイズ: {result.output_size} bytes（ロスレス）")
                
                # 画像を確認
                output_image = Image.open(result.output_path)
                print(f"   形式: {output_image.format}")
                print(f"   サイズ: {output_image.size}")
            else:
                print(f"   ❌ 失敗: {result.error_message}")
        
        # 直接resize_coreをテスト
        print("\n4. resize_core直接呼び出しのテスト...")
        
        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir) / "test_lossless.webp"
            
            result = resize_and_compress_image(
                source_path=temp_src.name,
                dest_path=str(output_path),
                target_width=400,
                quality=85,
                format="webp",
                webp_lossless=True
            )
            
            if len(result) >= 3:
                success = result[0]
                if success:
                    print("   ✅ 成功")
                    if output_path.exists():
                        print(f"   出力サイズ: {output_path.stat().st_size} bytes")
                else:
                    print("   ❌ 失敗")
            else:
                print(f"   ❌ 予期しない戻り値: {result}")
    
    print("\n✅ テスト完了")


if __name__ == "__main__":
    test_webp_lossless()