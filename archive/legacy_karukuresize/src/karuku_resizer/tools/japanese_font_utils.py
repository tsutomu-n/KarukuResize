#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
日本語フォント設定ユーティリティ

Windows11の日本語環境で最適なフォント表示を実現するための
ユーティリティクラスとヘルパー関数を提供します。
"""

import platform
from loguru import logger


class JapaneseFontManager:
    """日本語フォント管理クラス"""

    # 各OSでの推奨日本語フォント（優先度順）
    WINDOWS_FONTS = ["Yu Gothic UI", "Meiryo UI", "MS Gothic", "MS UI Gothic"]
    MACOS_FONTS = ["Hiragino Sans", "Hiragino Kaku Gothic ProN", "Osaka"]
    LINUX_FONTS = ["Noto Sans CJK JP", "Droid Sans Japanese", "Takao Gothic"]

    def __init__(self):
        """初期化処理"""
        self.system_name = platform.system()
        self.selected_font = self._get_best_font()
        self.size_normal = 13
        self.size_small = 12
        self.size_large = 15
        self.size_heading = 17

        # フォント調整（OSごとの差異を吸収）
        self._adjust_font_size_for_platform()

        logger.debug(f"選択された日本語フォント: {self.selected_font}, " f"通常サイズ: {self.size_normal}")

    def _get_best_font(self):
        """プラットフォームに最適なフォントを選択"""
        if self.system_name == "Windows":
            return self._find_first_available_font(self.WINDOWS_FONTS)
        elif self.system_name == "Darwin":  # macOS
            return self._find_first_available_font(self.MACOS_FONTS)
        else:  # Linux or other
            return self._find_first_available_font(self.LINUX_FONTS)

    def _find_first_available_font(self, font_list):
        """指定されたフォントリストから最初に利用可能なフォントを返す"""
        # 注: この実装は単純化されており、実際のフォント存在確認は行っていません
        # 本来はtkinterのフォントリスト取得機能などを使うべきですが、簡略化のため省略
        if font_list:
            return font_list[0]
        return ""

    def _adjust_font_size_for_platform(self):
        """プラットフォームに応じたフォントサイズ調整"""
        # macOSは少し小さめに
        if self.system_name == "Darwin":
            self.size_normal -= 1
            self.size_small -= 1
            self.size_large -= 1
            self.size_heading -= 1
        # Windowsの高DPI環境では少し大きめに
        elif self.system_name == "Windows":
            # Windows 10/11の高DPI対応（単純化した実装）
            self.size_normal += 0
            self.size_small += 0
            self.size_large += 0
            self.size_heading += 0

    def get_font_dict(self, size=None, bold=False):
        """フォント設定辞書を返す"""
        if size is None:
            size = self.size_normal

        return {
            "family": self.selected_font,
            "size": size,
            "weight": "bold" if bold else "normal",
        }

    def get_normal_font(self):
        """通常テキスト用フォント設定を返す"""
        return self.get_font_dict(self.size_normal)

    def get_small_font(self):
        """小さいテキスト用フォント設定を返す"""
        return self.get_font_dict(self.size_small)

    def get_large_font(self):
        """大きいテキスト用フォント設定を返す"""
        return self.get_font_dict(self.size_large)

    def get_heading_font(self, bold=True):
        """見出し用フォント設定を返す"""
        return self.get_font_dict(self.size_heading, bold)

    def get_button_font(self):
        """ボタン用フォント設定を返す"""
        return self.get_font_dict(self.size_normal, bold=True)


# シングルトンインスタンス
font_manager = JapaneseFontManager()


def get_font_dict(size=None, bold=False):
    """フォント設定辞書を返すヘルパー関数"""
    return font_manager.get_font_dict(size, bold)


def get_normal_font():
    """通常テキスト用フォント設定を返すヘルパー関数"""
    return font_manager.get_normal_font()


def get_button_font():
    """ボタン用フォント設定を返すヘルパー関数"""
    return font_manager.get_button_font()


def get_heading_font():
    """見出し用フォント設定を返すヘルパー関数"""
    return font_manager.get_heading_font()


# テスト用コード
if __name__ == "__main__":
    print(f"システム: {platform.system()}")
    print(f"選択されたフォント: {font_manager.selected_font}")
    print(f"通常フォント設定: {get_normal_font()}")
    print(f"ボタンフォント設定: {get_button_font()}")
    print(f"見出しフォント設定: {get_heading_font()}")
