#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
ファイルベース処理修正のテスト
"""

import sys
from pathlib import Path
from PIL import Image
import io
import tempfile
import os

# プロジェクトルートをPythonパスに追加
project_root = Path(__file__).parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from resize_core import resize_and_compress_image

def test_file_based_fix():
    """ファイルベース処理の修正をテスト"""
    print("=" * 60)
    print("ファイルベース処理修正テスト")
    print("=" * 60)
    
    # テスト用の画像を作成
    test_image = Image.new('RGB', (200, 150), (255, 0, 0))
    
    print("\n📋 テストケース:")
    
    test_cases = [
        {
            "name": "ファイルベース - リサイズなし",
            "resize_mode": "none",
            "resize_value": None,
            "quality": 85,
            "format": "jpeg"
        },
        {
            "name": "ファイルベース - 幅100pxにリサイズ",
            "resize_mode": "width", 
            "resize_value": 100,
            "quality": 85,
            "format": "jpeg"
        },
        {
            "name": "メモリベース - リサイズなし",
            "resize_mode": "none",
            "resize_value": None,
            "quality": 85,
            "output_format": "jpeg",
            "memory_based": True
        }
    ]
    
    for i, case in enumerate(test_cases, 1):
        print(f"\n{i}. {case['name']}")
        print(f"   resize_mode: {case['resize_mode']}")
        print(f"   resize_value: {case['resize_value']}")
        
        try:
            if case.get("memory_based"):
                # メモリベース処理
                output_buffer = io.BytesIO()
                
                success, error_msg = resize_and_compress_image(
                    source_image=test_image,
                    output_buffer=output_buffer,
                    resize_mode=case["resize_mode"],
                    resize_value=case["resize_value"],
                    quality=case["quality"],
                    output_format=case["output_format"],
                    optimize=True
                )
                
                if success:
                    output_size = len(output_buffer.getvalue())
                    print(f"   ✅ メモリベース成功: 出力サイズ={output_size}bytes")
                else:
                    print(f"   ❌ メモリベース失敗: {error_msg}")
            else:
                # ファイルベース処理
                with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as input_file:
                    test_image.save(input_file.name, 'JPEG', quality=95)
                    input_path = input_file.name
                
                with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as output_file:
                    output_path = output_file.name
                
                try:
                    success, kept_original, estimated_size = resize_and_compress_image(
                        source_path=input_path,
                        dest_path=output_path,
                        resize_mode=case["resize_mode"],
                        resize_value=case["resize_value"],
                        quality=case["quality"],
                        format=case["format"]
                    )
                    
                    if success:
                        if os.path.exists(output_path):
                            output_size = os.path.getsize(output_path)
                            print(f"   ✅ ファイルベース成功: 出力サイズ={output_size}bytes")
                            
                            # 出力画像のサイズを確認
                            with Image.open(output_path) as result_img:
                                print(f"   📐 出力画像サイズ: {result_img.size}")
                        else:
                            print("   ❌ 出力ファイルが作成されませんでした")
                    else:
                        print("   ❌ ファイルベース失敗")
                finally:
                    # 一時ファイルを削除
                    for temp_path in [input_path, output_path]:
                        if os.path.exists(temp_path):
                            try:
                                os.unlink(temp_path)
                            except:
                                pass
                
        except Exception as e:
            print(f"   💥 例外: {e}")
    
    print("\n✅ テスト完了")

if __name__ == "__main__":
    test_file_based_fix()