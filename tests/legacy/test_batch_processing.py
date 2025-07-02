#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
バッチ処理機能のテスト
"""
import sys
from pathlib import Path
from PIL import Image
import tempfile
import time
import shutil

# プロジェクトルートをPythonパスに追加
project_root = Path(__file__).parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from resize_core import resize_and_compress_image, find_image_files


def test_batch_processing():
    """バッチ処理機能のテスト"""
    print("=" * 60)
    print("バッチ処理機能のテスト")
    print("=" * 60)
    
    # テスト用のディレクトリと画像を作成
    print("\n1. テスト用の画像ファイルを作成...")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        input_dir = temp_path / "input"
        output_dir = temp_path / "output"
        
        input_dir.mkdir()
        output_dir.mkdir()
        
        # 複数の異なる画像ファイルを作成
        test_images = [
            {"name": "test1.jpg", "size": (800, 600), "color": (255, 0, 0), "format": "JPEG"},
            {"name": "test2.png", "size": (1200, 800), "color": (0, 255, 0), "format": "PNG"},
            {"name": "test3.webp", "size": (600, 400), "color": (0, 0, 255), "format": "WEBP"},
            {"name": "test4.jpeg", "size": (1000, 750), "color": (255, 255, 0), "format": "JPEG"},
        ]
        
        created_files = []
        for img_info in test_images:
            img_path = input_dir / img_info["name"]
            image = Image.new("RGB", img_info["size"], img_info["color"])
            
            if img_info["format"] == "WEBP":
                image.save(img_path, format="WEBP", quality=85)
            else:
                image.save(img_path, format=img_info["format"])
                
            created_files.append(img_path)
            print(f"   作成: {img_info['name']} ({img_info['size'][0]}×{img_info['size'][1]})")
        
        # 2. ファイル発見機能のテスト
        print("\n2. ファイル発見機能のテスト...")
        
        found_files = find_image_files(str(input_dir))
        print(f"   発見されたファイル数: {len(found_files)}")
        
        if len(found_files) == len(created_files):
            print("   ✅ 全ファイルが正しく発見されました")
        else:
            print(f"   ⚠️  期待: {len(created_files)}, 実際: {len(found_files)}")
        
        for file_path in found_files:
            print(f"      - {Path(file_path).name}")
        
        # 3. バッチ処理の実行
        print("\n3. バッチ処理の実行...")
        
        start_time = time.time()
        success_count = 0
        total_original_size = 0
        total_output_size = 0
        
        for i, input_file in enumerate(found_files, 1):
            input_path = Path(input_file)
            output_path = output_dir / f"{input_path.stem}_resized.jpg"
            
            print(f"   処理 {i}/{len(found_files)}: {input_path.name}")
            
            # 元ファイルサイズを記録
            original_size = input_path.stat().st_size
            total_original_size += original_size
            
            # 画像処理を実行
            result = resize_and_compress_image(
                source_path=str(input_path),
                dest_path=str(output_path),
                target_width=400,
                quality=80,
                format="jpeg"
            )
            
            if len(result) >= 1 and result[0]:  # success
                success_count += 1
                output_size = output_path.stat().st_size
                total_output_size += output_size
                reduction = (1 - output_size / original_size) * 100
                
                print(f"      ✅ 成功: {original_size:,} → {output_size:,} bytes ({reduction:.1f}% 削減)")
            else:
                print(f"      ❌ 失敗")
        
        processing_time = time.time() - start_time
        
        print(f"\n4. バッチ処理結果サマリー...")
        print(f"   処理時間: {processing_time:.2f}秒")
        print(f"   成功ファイル: {success_count}/{len(found_files)}")
        print(f"   総元サイズ: {total_original_size:,} bytes")
        print(f"   総出力サイズ: {total_output_size:,} bytes")
        
        if total_original_size > 0:
            total_reduction = (1 - total_output_size / total_original_size) * 100
            print(f"   総削減率: {total_reduction:.1f}%")
        
        if success_count == len(found_files):
            print("   ✅ 全ファイルの処理が成功しました")
        else:
            print(f"   ⚠️  一部のファイルで処理が失敗しました")
        
        # 5. 出力ファイルの検証
        print(f"\n5. 出力ファイルの検証...")
        
        output_files = list(output_dir.glob("*.jpg"))
        print(f"   出力ファイル数: {len(output_files)}")
        
        for output_file in output_files:
            try:
                # 画像として読み込める確認
                with Image.open(output_file) as img:
                    print(f"      {output_file.name}: {img.size} {img.format} ({output_file.stat().st_size:,} bytes)")
            except Exception as e:
                print(f"      ❌ {output_file.name}: 読み込みエラー - {str(e)}")
        
        # 6. 異なる設定でのバッチ処理テスト
        print(f"\n6. 異なる設定でのバッチ処理テスト...")
        
        webp_output_dir = temp_path / "webp_output"
        webp_output_dir.mkdir()
        
        webp_success_count = 0
        for i, input_file in enumerate(found_files[:2], 1):  # 最初の2ファイルのみテスト
            input_path = Path(input_file)
            output_path = webp_output_dir / f"{input_path.stem}_webp.webp"
            
            print(f"   WebP変換 {i}: {input_path.name}")
            
            result = resize_and_compress_image(
                source_path=str(input_path),
                dest_path=str(output_path),
                target_width=300,
                quality=85,
                format="webp",
                webp_lossless=False
            )
            
            if len(result) >= 1 and result[0]:
                webp_success_count += 1
                print(f"      ✅ WebP変換成功: {output_path.stat().st_size:,} bytes")
            else:
                print(f"      ❌ WebP変換失敗")
        
        if webp_success_count > 0:
            print(f"   ✅ WebP形式での変換が動作しています ({webp_success_count}/2)")
        else:
            print(f"   ❌ WebP形式での変換に問題があります")
        
        # 7. パフォーマンス評価
        print(f"\n7. パフォーマンス評価...")
        
        if processing_time < 5.0:
            print(f"   📈 処理速度: 優秀 ({processing_time:.2f}秒)")
        elif processing_time < 10.0:
            print(f"   📊 処理速度: 良好 ({processing_time:.2f}秒)")
        else:
            print(f"   ⚠️  処理速度: 要改善 ({processing_time:.2f}秒)")
        
        files_per_second = len(found_files) / processing_time if processing_time > 0 else 0
        print(f"   処理スループット: {files_per_second:.1f} ファイル/秒")
    
    print("\n✅ バッチ処理機能のテスト完了")


if __name__ == "__main__":
    test_batch_processing()