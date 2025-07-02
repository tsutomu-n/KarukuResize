#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
プレビュー機能のメモリベース処理テスト
"""
import sys
from pathlib import Path
from PIL import Image
import io

# プロジェクトルートをPythonパスに追加
project_root = Path(__file__).parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from resize_core import resize_and_compress_image


def test_memory_based_processing():
    """メモリベース処理のテスト"""
    print("=" * 60)
    print("メモリベース画像処理のテスト")
    print("=" * 60)
    
    # テスト画像を作成
    print("\n1. テスト画像を作成...")
    test_image = Image.new("RGB", (800, 600), color=(255, 0, 0))
    print(f"   作成した画像: {test_image.size} {test_image.mode}")
    
    # 出力バッファを準備
    output_buffer = io.BytesIO()
    
    # メモリベース処理を実行
    print("\n2. メモリベース処理を実行...")
    result = resize_and_compress_image(
        source_image=test_image,
        output_buffer=output_buffer,
        resize_mode="width",
        resize_value=400,
        quality=85,
        output_format="jpeg",
        optimize=True,
        progressive=True
    )
    
    print(f"   処理結果: {result}")
    
    if len(result) == 2:
        success, error_msg = result
        if success:
            print("   ✅ 成功")
            
            # 結果を確認
            output_buffer.seek(0)
            result_image = Image.open(output_buffer)
            print(f"   出力画像: {result_image.size} {result_image.format}")
            print(f"   バッファサイズ: {len(output_buffer.getvalue())} bytes")
        else:
            print(f"   ❌ 失敗: {error_msg}")
    else:
        print(f"   ❌ 予期しない戻り値: {result}")
    
    # 異なるフォーマットでテスト
    print("\n3. 異なるフォーマットでテスト...")
    
    formats = ["png", "webp"]
    for fmt in formats:
        output_buffer = io.BytesIO()
        result = resize_and_compress_image(
            source_image=test_image,
            output_buffer=output_buffer,
            resize_mode="percentage",
            resize_value=50,
            quality=90,
            output_format=fmt,
            optimize=True
        )
        
        if len(result) == 2 and result[0]:
            output_buffer.seek(0)
            result_image = Image.open(output_buffer)
            print(f"   {fmt.upper()}: {result_image.size} - {len(output_buffer.getvalue())} bytes")
        else:
            print(f"   {fmt.upper()}: 失敗")
    
    # ファイルベース処理の互換性テスト
    print("\n4. ファイルベース処理の互換性テスト...")
    import tempfile
    
    with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as temp_src:
        test_image.save(temp_src.name)
        
        with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as temp_dst:
            result = resize_and_compress_image(
                source_path=temp_src.name,
                dest_path=temp_dst.name,
                target_width=300,
                quality=80,
                format="original"
            )
            
            if len(result) == 3:
                success, keep_original, estimated_size = result
                print(f"   ファイルベース処理: 成功={success}, 元サイズ維持={keep_original}")
            else:
                print(f"   ファイルベース処理: 予期しない結果 {result}")
    
    print("\n✅ テスト完了")


if __name__ == "__main__":
    test_memory_based_processing()