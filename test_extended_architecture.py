#!/usr/bin/env python
"""
拡張版アーキテクチャのテストスクリプト（すべてのタブを含む）
"""
import os
import sys
from pathlib import Path

# 環境変数で新アーキテクチャを有効化
os.environ["USE_NEW_ARCHITECTURE"] = "1"
os.environ["USE_EXTENDED_VERSION"] = "1"

# プロジェクトルートをPythonパスに追加
project_root = Path(__file__).parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# 拡張版メインウィンドウを起動
from karukuresize.gui.main_window_extended import main

if __name__ == "__main__":
    print("拡張版アーキテクチャでKarukuResize GUIを起動しています...")
    print("- リサイズタブ: 完全実装")
    print("- プレビュータブ: 完全実装")
    print("- 履歴タブ: 完全実装")
    print("- 統計タブ: 基本実装")
    main()