#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
ヘルプダイアログモジュール

「使い方」ボタンをクリックしたときに表示されるヘルプダイアログを実装します。
"""

import tkinter as tk
from typing import Optional, Callable

class HelpDialog:
    """ヘルプダイアログクラス"""
    
    def __init__(self, parent: tk.Tk, help_content: str):
        """
        Args:
            parent: 親ウィンドウ
            help_content: マークダウン形式のヘルプコンテンツ
        """
        self.parent = parent
        self.help_content = help_content
        self.window: Optional[tk.Toplevel] = None
        
    def show(self):
        """ヘルプダイアログを表示"""
        # 既存のウィンドウがあれば閉じる
        if self.window is not None:
            self.window.destroy()
            
        # 新しいウィンドウを作成
        self.window = tk.Toplevel(self.parent)
        self.window.title("画像リサイズツールの使い方")
        self.window.geometry("800x600")
        self.window.minsize(640, 480)
        
        # フォント設定
        title_font = ("Yu Gothic UI", 18, "bold")
        heading_font = ("Yu Gothic UI", 16, "bold")
        text_font = ("Yu Gothic UI", 14)
        
        # メインフレーム（スクロール可能）
        main_frame = tk.Frame(self.window)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # スクロールバー
        scrollbar = tk.Scrollbar(main_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # キャンバスとスクロール設定
        canvas = tk.Canvas(main_frame)
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        canvas.configure(yscrollcommand=scrollbar.set)
        scrollbar.configure(command=canvas.yview)
        
        # コンテンツフレーム
        content_frame = tk.Frame(canvas)
        canvas.create_window((0, 0), window=content_frame, anchor="nw")
        
        # ヘルプコンテンツの解析と表示
        lines = self.help_content.strip().split("\n")
        current_section = None
        
        for line in lines:
            if line.startswith("# "):
                # メインタイトル
                title_text = line[2:].strip()
                tk.Label(content_frame, text=title_text, font=title_font, justify=tk.LEFT, anchor="w").pack(fill=tk.X, pady=(10, 5))
            elif line.startswith("## "):
                # セクションタイトル
                section_text = line[3:].strip()
                current_section = section_text
                tk.Label(content_frame, text=section_text, font=heading_font, justify=tk.LEFT, anchor="w", fg="#0078d4").pack(fill=tk.X, pady=(15, 5))
            elif line.startswith("### "):
                # サブセクションタイトル
                subsection_text = line[4:].strip()
                tk.Label(content_frame, text=subsection_text, font=("Yu Gothic UI", 15, "bold"), justify=tk.LEFT, anchor="w").pack(fill=tk.X, pady=(10, 5))
            elif line.startswith("- "):
                # 箇条書き
                bullet_text = line[2:].strip()
                bullet_frame = tk.Frame(content_frame)
                bullet_frame.pack(fill=tk.X, pady=2)
                tk.Label(bullet_frame, text="•", font=text_font, width=2).pack(side=tk.LEFT)
                tk.Label(bullet_frame, text=bullet_text, font=text_font, justify=tk.LEFT, anchor="w", wraplength=700).pack(side=tk.LEFT, fill=tk.X)
            elif line.strip() == "":
                # 空行
                tk.Label(content_frame, text="", height=1).pack()
            else:
                # 通常のテキスト
                if line.strip():
                    tk.Label(content_frame, text=line.strip(), font=text_font, justify=tk.LEFT, anchor="w", wraplength=750).pack(fill=tk.X, pady=2)
        
        # 閉じるボタン
        tk.Button(content_frame, text="閉じる", font=("Yu Gothic UI", 14), command=self.window.destroy, width=20).pack(pady=20)
        
        # キャンバスのスクロール領域を設定
        content_frame.update_idletasks()
        canvas.config(scrollregion=canvas.bbox("all"))
        
        # マウスホイールでスクロールできるようにする
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
        canvas.bind_all("<MouseWheel>", _on_mousewheel)
        
        # ウィンドウが閉じられたときにイベントバインディングを解除
        def _on_closing():
            canvas.unbind_all("<MouseWheel>")
            self.window.destroy()
        self.window.protocol("WM_DELETE_WINDOW", _on_closing)
        
        # ウィンドウをモーダルにする
        self.window.transient(self.parent)
        self.window.grab_set()
        self.parent.wait_window(self.window)