#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""pre-commitのテストファイル"""

import os  # 未使用のインポート
import sys  # 未使用のインポート


def test_function():
    """テスト関数"""
    unused_variable = "これは使われない変数"  # 未使用の変数
    very_long_line = "これは非常に長い行です。120文字を超えるかもしれませんが、新しい設定では問題ありません。" * 2

    print("Hello, World!")


if __name__ == "__main__":
    test_function()
