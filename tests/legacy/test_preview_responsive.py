#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
プレビュー機能のレスポンシブテスト
"""
import sys
from pathlib import Path
from PIL import Image
import tempfile
import time
import io

# プロジェクトルートをPythonパスに追加
project_root = Path(__file__).parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from resize_core import resize_and_compress_image


def test_preview_memory_processing():
    """メモリベースのプレビュー処理テスト"""
    print("=" * 60)
    print("プレビュー機能のレスポンシブテスト")
    print("=" * 60)
    
    # テスト画像を作成
    print("\n1. テスト画像を作成...")
    test_image = Image.new("RGB", (1920, 1080), color=(255, 128, 64))
    
    print(f"   元画像サイズ: {test_image.size}")
    print(f"   元画像モード: {test_image.mode}")
    
    # メモリベース処理のテスト
    print("\n2. メモリベースのプレビュー生成テスト...")
    
    test_cases = [
        {"format": "jpeg", "quality": 85, "desc": "JPEG品質85"},
        {"format": "webp", "quality": 80, "desc": "WebP品質80"},
        {"format": "png", "quality": 100, "desc": "PNG"},
        {"format": "webp", "quality": 90, "webp_lossless": True, "desc": "WebPロスレス"},
    ]
    
    for i, case in enumerate(test_cases, 1):
        print(f"\n   テスト {i}: {case['desc']}")
        
        # 処理時間を計測
        start_time = time.time()
        
        # メモリバッファを作成
        output_buffer = io.BytesIO()
        
        try:
            # メモリベース処理を実行
            success, error_msg = resize_and_compress_image(
                source_image=test_image,
                output_buffer=output_buffer,
                resize_mode="width",
                resize_value=800,
                quality=case["quality"],
                output_format=case["format"],
                exif_handling="remove",
                lanczos_filter=True,
                progressive=False,
                optimize=True,
                webp_lossless=case.get("webp_lossless", False)
            )
            
            processing_time = time.time() - start_time
            
            if success:
                # バッファから画像を読み込み
                output_buffer.seek(0)
                result_image = Image.open(output_buffer)
                output_size = len(output_buffer.getvalue())
                
                print(f"      ✅ 成功 ({processing_time:.3f}秒)")
                print(f"      出力サイズ: {result_image.size}")
                print(f"      ファイルサイズ: {output_size:,} bytes")
                print(f"      形式: {result_image.format}")
                
                # レスポンス性の評価
                if processing_time < 0.5:
                    print(f"      📈 レスポンス: 優秀 ({processing_time:.3f}秒)")
                elif processing_time < 1.0:
                    print(f"      📊 レスポンス: 良好 ({processing_time:.3f}秒)")
                else:
                    print(f"      ⚠️  レスポンス: 要改善 ({processing_time:.3f}秒)")
                    
            else:
                print(f"      ❌ 失敗: {error_msg}")
                
        except Exception as e:
            print(f"      ❌ エラー: {str(e)}")
    
    print("\n3. 大サイズ画像での処理テスト...")
    
    # 大きな画像でのテスト
    large_image = Image.new("RGB", (4000, 3000), color=(128, 255, 128))
    print(f"   大画像サイズ: {large_image.size}")
    
    start_time = time.time()
    output_buffer = io.BytesIO()
    
    try:
        success, error_msg = resize_and_compress_image(
            source_image=large_image,
            output_buffer=output_buffer,
            resize_mode="width",
            resize_value=1200,
            quality=85,
            output_format="jpeg",
            exif_handling="remove",
            lanczos_filter=True,
            progressive=False,
            optimize=True
        )
        
        processing_time = time.time() - start_time
        
        if success:
            output_buffer.seek(0)
            result_image = Image.open(output_buffer)
            output_size = len(output_buffer.getvalue())
            
            print(f"   ✅ 大画像処理成功 ({processing_time:.3f}秒)")
            print(f"   出力サイズ: {result_image.size}")
            print(f"   ファイルサイズ: {output_size:,} bytes")
            
            # メモリ効率性の評価
            if processing_time < 2.0:
                print("   📈 大画像レスポンス: 優秀")
            elif processing_time < 5.0:
                print("   📊 大画像レスポンス: 良好")
            else:
                print("   ⚠️  大画像レスポンス: 要改善")
                
        else:
            print(f"   ❌ 大画像処理失敗: {error_msg}")
            
    except Exception as e:
        print(f"   ❌ 大画像処理エラー: {str(e)}")
    
    print("\n4. 変換予測情報のテスト...")
    
    # 予測情報のテスト
    test_image_small = Image.new("RGB", (800, 600), color=(200, 100, 50))
    
    settings_test_cases = [
        {"mode": "width", "value": 400, "quality": 85, "format": "jpeg"},
        {"mode": "percentage", "value": 50, "quality": 90, "format": "webp"},
        {"mode": "height", "value": 300, "quality": 95, "format": "png"},
    ]
    
    for i, settings in enumerate(settings_test_cases, 1):
        print(f"\n   予測テスト {i}: {settings['mode']} {settings['value']}, {settings['format']}")
        
        # 元画像情報
        original_size = test_image_small.size
        
        # サイズ計算ロジックをテスト
        if settings['mode'] == 'width':
            calculated_width = settings['value']
            calculated_height = int(original_size[1] * (settings['value'] / original_size[0]))
        elif settings['mode'] == 'height':
            calculated_height = settings['value']
            calculated_width = int(original_size[0] * (settings['value'] / original_size[1]))
        elif settings['mode'] == 'percentage':
            calculated_width = int(original_size[0] * (settings['value'] / 100))
            calculated_height = int(original_size[1] * (settings['value'] / 100))
        
        print(f"      元サイズ: {original_size[0]} × {original_size[1]} px")
        print(f"      予測サイズ: {calculated_width} × {calculated_height} px")
        
        # 実際に処理して検証
        output_buffer = io.BytesIO()
        success, _ = resize_and_compress_image(
            source_image=test_image_small,
            output_buffer=output_buffer,
            resize_mode=settings['mode'],
            resize_value=settings['value'],
            quality=settings['quality'],
            output_format=settings['format']
        )
        
        if success:
            output_buffer.seek(0)
            result_image = Image.open(output_buffer)
            actual_size = result_image.size
            
            if actual_size == (calculated_width, calculated_height):
                print(f"      ✅ サイズ予測正確: {actual_size[0]} × {actual_size[1]} px")
            else:
                print(f"      ⚠️  サイズ予測誤差: 予測={calculated_width}×{calculated_height}, 実際={actual_size[0]}×{actual_size[1]}")
        else:
            print("      ❌ 処理失敗")
    
    print("\n✅ プレビュー機能のレスポンシブテスト完了")


if __name__ == "__main__":
    test_preview_memory_processing()