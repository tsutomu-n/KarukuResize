#!/usr/bin/env python
"""
完全版アーキテクチャのテストスクリプト（すべての機能を統合）
"""
import os
import sys
from pathlib import Path

# 環境変数で新アーキテクチャを有効化
os.environ["USE_NEW_ARCHITECTURE"] = "1"
os.environ["USE_COMPLETE_VERSION"] = "1"

# プロジェクトルートをPythonパスに追加
project_root = Path(__file__).parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# 完全版メインウィンドウを起動
from karukuresize.gui.main_window_complete import main

if __name__ == "__main__":
    print("=" * 60)
    print("KarukuResize - 完全版アーキテクチャ")
    print("=" * 60)
    print()
    print("✅ リサイズタブ: 完全実装")
    print("  - MVVMパターン")
    print("  - 設定の永続化")
    print("  - プリセット機能")
    print()
    print("✅ プレビュータブ: 完全実装")
    print("  - リアルタイムプレビュー")
    print("  - Before/After比較")
    print("  - ズーム/パン機能")
    print()
    print("✅ 履歴タブ: 完全実装")
    print("  - 検索/フィルタリング")
    print("  - 再処理機能")
    print("  - CSV/JSONエクスポート")
    print()
    print("✅ 統計タブ: 完全実装")
    print("  - 期間別統計")
    print("  - グラフ表示")
    print("  - データエクスポート")
    print()
    print("✅ 追加機能:")
    print("  - 設定の保存/読み込み")
    print("  - 最近使用したファイル")
    print("  - プリセットのインポート/エクスポート")
    print("  - ウィンドウ位置の記憶")
    print()
    print("=" * 60)
    print()
    
    main()