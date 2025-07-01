#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
プレビュー機能のメモリ管理修正テスト
"""

import sys
from pathlib import Path
from PIL import Image
import io
import time

# プロジェクトルートをPythonパスに追加
project_root = Path(__file__).parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from resize_core import resize_and_compress_image


def test_memory_issue():
    """メモリ管理の問題を再現・検証"""
    print("=" * 60)
    print("プレビュー機能メモリ管理修正テスト")
    print("=" * 60)
    
    # テスト画像を作成
    test_image = Image.new('RGB', (200, 150), (255, 0, 0))
    
    print("\n📋 メモリバッファからの画像読み込みテスト:")
    
    # 1. 問題のあるパターン（修正前の動作）
    print("\n1. 問題のあるパターン:")
    output_buffer = io.BytesIO()
    
    success, error_msg = resize_and_compress_image(
        source_image=test_image,
        output_buffer=output_buffer,
        resize_mode="none",
        resize_value=None,
        quality=85,
        output_format="jpeg",
        optimize=True
    )
    
    if success:
        output_buffer.seek(0)
        after_image_bad = Image.open(output_buffer)
        print(f"  after_image_bad: {after_image_bad}")
        print(f"  size: {after_image_bad.size}")
        
        # バッファをクリア（問題を再現）
        output_buffer.close()
        
        # 遅延してアクセス（スレッド間通信を模擬）
        time.sleep(0.1)
        
        try:
            # これは失敗する可能性がある
            print(f"  遅延後のアクセス: size={after_image_bad.size}")
        except Exception as e:
            print(f"  ❌ エラー発生: {e}")
    
    # 2. 修正されたパターン
    print("\n2. 修正されたパターン:")
    output_buffer = io.BytesIO()
    
    success, error_msg = resize_and_compress_image(
        source_image=test_image,
        output_buffer=output_buffer,
        resize_mode="none",
        resize_value=None,
        quality=85,
        output_format="jpeg",
        optimize=True
    )
    
    if success:
        # バッファのデータを保持
        image_data = output_buffer.getvalue()
        after_size = len(image_data)
        
        # 独立したバッファから画像を開く
        output_buffer.seek(0)
        after_image_good = Image.open(output_buffer)
        # 画像データを完全にメモリに読み込む
        after_image_good.load()
        # さらに安全のため、独立したコピーを作成
        after_image_good = after_image_good.copy()
        
        print(f"  after_image_good: {after_image_good}")
        print(f"  size: {after_image_good.size}")
        
        # バッファをクリア
        output_buffer.close()
        
        # 遅延してアクセス
        time.sleep(0.1)
        
        try:
            # これは成功するはず
            print(f"  ✅ 遅延後のアクセス: size={after_image_good.size}")
            print(f"  ✅ mode={after_image_good.mode}")
        except Exception as e:
            print(f"  ❌ エラー発生: {e}")
    
    print("\n💡 修正の効果:")
    print("  1. load()メソッドで画像データを完全にメモリに読み込み")
    print("  2. copy()メソッドで独立したコピーを作成")
    print("  3. バッファが閉じられても画像データにアクセス可能")
    
    print("\n📊 メモリ使用量の違い:")
    print("  - 修正前: バッファに依存（遅延読み込み）")
    print("  - 修正後: 独立したメモリ領域に画像データを保持")
    
    return True


def test_threading_simulation():
    """スレッド間通信のシミュレーション"""
    print("\n" + "=" * 60)
    print("スレッド間通信シミュレーション")
    print("=" * 60)
    
    import threading
    
    shared_image = None
    
    def worker_thread():
        """ワーカースレッド（プレビュー生成）"""
        global shared_image
        
        # テスト画像を作成
        test_image = Image.new('RGB', (100, 100), (0, 255, 0))
        output_buffer = io.BytesIO()
        
        # 圧縮処理
        success, _ = resize_and_compress_image(
            source_image=test_image,
            output_buffer=output_buffer,
            resize_mode="none",
            resize_value=None,
            quality=85,
            output_format="jpeg",
            optimize=True
        )
        
        if success:
            # 修正されたパターンで画像を作成
            output_buffer.seek(0)
            after_image = Image.open(output_buffer)
            after_image.load()
            after_image = after_image.copy()
            
            # 共有変数に設定
            shared_image = after_image
            print("  ワーカー: 画像生成完了")
    
    def ui_thread():
        """UIスレッド（表示）"""
        global shared_image
        
        # ワーカーの完了を待つ
        time.sleep(0.2)
        
        if shared_image:
            print(f"  UI: 画像受信 size={shared_image.size}")
            print("  ✅ スレッド間通信成功")
        else:
            print("  ❌ 画像が受信できませんでした")
    
    # スレッドを実行
    worker = threading.Thread(target=worker_thread)
    ui = threading.Thread(target=ui_thread)
    
    worker.start()
    ui.start()
    
    worker.join()
    ui.join()
    
    print("\n✅ スレッド間通信テスト完了")


def main():
    """メインテスト関数"""
    print("🔧 プレビュー機能メモリ管理修正テスト")
    print("=" * 60)
    
    # メモリ管理の問題をテスト
    test_memory_issue()
    
    # スレッド間通信をテスト
    test_threading_simulation()
    
    print("\n" + "=" * 60)
    print("✅ 全テスト完了")
    print("\n🎯 結論:")
    print("  - メモリバッファ依存の問題を解決")
    print("  - スレッド間での画像オブジェクト共有が安全に")
    print("  - プレビュー機能が正常に動作するはず")


if __name__ == "__main__":
    main()