#!/usr/bin/env python
"""
新しいアーキテクチャのテストスクリプト
"""
import os
import sys
from pathlib import Path

# 環境変数で新アーキテクチャを有効化
os.environ["USE_NEW_ARCHITECTURE"] = "1"

# プロジェクトルートをPythonパスに追加
project_root = Path(__file__).parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# 新しいメインウィンドウを起動
from karukuresize.gui.main_window import main

if __name__ == "__main__":
    print("新しいアーキテクチャでKarukuResize GUIを起動しています...")
    main()