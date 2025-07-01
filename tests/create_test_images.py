#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
テスト用の画像ファイルを作成するスクリプト
"""

from PIL import Image
import os

# inputディレクトリを作成
os.makedirs("input", exist_ok=True)

# テスト画像を作成
print("テスト画像を作成中...")

# 1. 大きな画像（リサイズが必要）
img1 = Image.new("RGB", (3000, 2000), color=(255, 100, 100))
img1.save("input/large_image.jpg", "JPEG", quality=95)
print("✓ large_image.jpg (3000x2000)")

# 2. 中サイズの画像
img2 = Image.new("RGB", (1920, 1080), color=(100, 255, 100))
img2.save("input/medium_image.png", "PNG")
print("✓ medium_image.png (1920x1080)")

# 3. 小さな画像（リサイズ不要）
img3 = Image.new("RGB", (800, 600), color=(100, 100, 255))
img3.save("input/small_image.jpg", "JPEG")
print("✓ small_image.jpg (800x600)")

# 4. 日本語ファイル名
img4 = Image.new("RGB", (1600, 1200), color=(255, 255, 100))
img4.save("input/テスト画像.jpg", "JPEG")
print("✓ テスト画像.jpg (1600x1200)")

# 5. WebP形式
img5 = Image.new("RGB", (2048, 1536), color=(255, 100, 255))
img5.save("input/webp_test.webp", "WEBP", quality=90)
print("✓ webp_test.webp (2048x1536)")

print("\nテスト画像の作成が完了しました！")
print("inputフォルダに5つの画像が作成されました。")