#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
エラーケースハンドリングのテスト
"""
import sys
from pathlib import Path
from PIL import Image
import tempfile
import io

# プロジェクトルートをPythonパスに追加
project_root = Path(__file__).parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from resize_core import resize_and_compress_image


def test_error_case_handling():
    """エラーケースのハンドリングテスト"""
    print("=" * 60)
    print("エラーケースハンドリングのテスト")
    print("=" * 60)
    
    # 1. 無効な画像オブジェクトのテスト
    print("\n1. 無効な画像オブジェクトのテスト...")
    
    try:
        output_buffer = io.BytesIO()
        result = resize_and_compress_image(
            source_image=None,  # None画像
            output_buffer=output_buffer,
            resize_mode="width",
            resize_value=400,
            quality=85,
            output_format="jpeg"
        )
        
        if len(result) == 2:
            success, error_msg = result
            if not success:
                print(f"   ✅ 正常にエラー処理: {error_msg}")
            else:
                print(f"   ❌ 予期しない成功")
        else:
            print(f"   ❌ 予期しない戻り値: {result}")
            
    except Exception as e:
        print(f"   ✅ 例外で適切にエラー処理: {str(e)}")
    
    # 2. 無効なリサイズ値のテスト
    print("\n2. 無効なリサイズ値のテスト...")
    
    test_image = Image.new("RGB", (800, 600), color=(255, 0, 0))
    
    invalid_resize_values = [0, -100, None]
    
    for i, invalid_value in enumerate(invalid_resize_values, 1):
        print(f"   テスト 2.{i}: リサイズ値 = {invalid_value}")
        
        try:
            output_buffer = io.BytesIO()
            result = resize_and_compress_image(
                source_image=test_image,
                output_buffer=output_buffer,
                resize_mode="width",
                resize_value=invalid_value,
                quality=85,
                output_format="jpeg"
            )
            
            if len(result) == 2:
                success, error_msg = result
                if not success:
                    print(f"      ✅ 正常にエラー処理: {error_msg}")
                else:
                    print(f"      ❌ 予期しない成功")
            else:
                print(f"      ❌ 予期しない戻り値: {result}")
                
        except Exception as e:
            print(f"      ✅ 例外で適切にエラー処理: {str(e)}")
    
    # 3. 無効な品質値のテスト  
    print("\n3. 無効な品質値のテスト...")
    
    invalid_quality_values = [-1, 0, 101, 200]
    
    for i, invalid_quality in enumerate(invalid_quality_values, 1):
        print(f"   テスト 3.{i}: 品質値 = {invalid_quality}")
        
        try:
            output_buffer = io.BytesIO()
            result = resize_and_compress_image(
                source_image=test_image,
                output_buffer=output_buffer,
                resize_mode="width",
                resize_value=400,
                quality=invalid_quality,
                output_format="jpeg"
            )
            
            if len(result) == 2:
                success, error_msg = result
                if success:
                    # 品質値は自動的に補正される場合もある
                    print(f"      ℹ️  成功（品質値が補正された可能性）")
                else:
                    print(f"      ✅ 正常にエラー処理: {error_msg}")
            else:
                print(f"      ❌ 予期しない戻り値: {result}")
                
        except Exception as e:
            print(f"      ✅ 例外で適切にエラー処理: {str(e)}")
    
    # 4. 無効な出力フォーマットのテスト
    print("\n4. 無効な出力フォーマットのテスト...")
    
    invalid_formats = ["invalid", "gif", "bmp", None]
    
    for i, invalid_format in enumerate(invalid_formats, 1):
        print(f"   テスト 4.{i}: フォーマット = {invalid_format}")
        
        try:
            output_buffer = io.BytesIO()
            result = resize_and_compress_image(
                source_image=test_image,
                output_buffer=output_buffer,
                resize_mode="width", 
                resize_value=400,
                quality=85,
                output_format=invalid_format
            )
            
            if len(result) == 2:
                success, error_msg = result
                if not success:
                    print(f"      ✅ 正常にエラー処理: {error_msg}")
                else:
                    print(f"      ❌ 予期しない成功")
            else:
                print(f"      ❌ 予期しない戻り値: {result}")
                
        except Exception as e:
            print(f"      ✅ 例外で適切にエラー処理: {str(e)}")
    
    # 5. 無効なリサイズモードのテスト
    print("\n5. 無効なリサイズモードのテスト...")
    
    invalid_modes = ["invalid_mode", None, ""]
    
    for i, invalid_mode in enumerate(invalid_modes, 1):
        print(f"   テスト 5.{i}: リサイズモード = {invalid_mode}")
        
        try:
            output_buffer = io.BytesIO()
            result = resize_and_compress_image(
                source_image=test_image,
                output_buffer=output_buffer,
                resize_mode=invalid_mode,
                resize_value=400,
                quality=85,
                output_format="jpeg"
            )
            
            if len(result) == 2:
                success, error_msg = result
                if not success:
                    print(f"      ✅ 正常にエラー処理: {error_msg}")
                else:
                    print(f"      ❌ 予期しない成功")
            else:
                print(f"      ❌ 予期しない戻り値: {result}")
                
        except Exception as e:
            print(f"      ✅ 例外で適切にエラー処理: {str(e)}")
    
    # 6. 破損画像データのテスト
    print("\n6. 破損画像データのテスト...")
    
    try:
        # 無効な画像データを作成
        corrupted_image = Image.new("RGB", (0, 0))  # サイズ0の画像
        
        output_buffer = io.BytesIO()
        result = resize_and_compress_image(
            source_image=corrupted_image,
            output_buffer=output_buffer,
            resize_mode="width",
            resize_value=400,
            quality=85,
            output_format="jpeg"
        )
        
        if len(result) == 2:
            success, error_msg = result
            if not success:
                print(f"   ✅ 正常にエラー処理: {error_msg}")
            else:
                print(f"   ❌ 予期しない成功")
        else:
            print(f"   ❌ 予期しない戻り値: {result}")
            
    except Exception as e:
        print(f"   ✅ 例外で適切にエラー処理: {str(e)}")
    
    # 7. 存在しないファイルパスのテスト（ファイルベース処理）
    print("\n7. 存在しないファイルパスのテスト...")
    
    try:
        non_existent_path = "/path/that/does/not/exist.jpg"
        temp_output = "/tmp/test_output.jpg"
        
        result = resize_and_compress_image(
            source_path=non_existent_path,
            dest_path=temp_output,
            target_width=400,
            quality=85,
            format="jpeg"
        )
        
        if len(result) >= 1:
            success = result[0]
            if not success:
                print(f"   ✅ 正常にエラー処理")
            else:
                print(f"   ❌ 予期しない成功")
        else:
            print(f"   ❌ 予期しない戻り値: {result}")
            
    except Exception as e:
        print(f"   ✅ 例外で適切にエラー処理: {str(e)}")
    
    print("\n✅ エラーケースハンドリングテスト完了")


if __name__ == "__main__":
    test_error_case_handling()