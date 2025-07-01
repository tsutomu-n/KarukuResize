#!/usr/bin/env python
"""ドラッグ&ドロップ機能のテストスクリプト"""

import customtkinter as ctk
from pathlib import Path
from drag_drop_handler import DragDropHandler, TKDND_AVAILABLE

def main():
    """テストGUIを起動"""
    if not TKDND_AVAILABLE:
        print("tkinterdnd2が利用できません。インストールしてください。")
        return
    
    # ウィンドウ作成
    root = ctk.CTk()
    root.title("ドラッグ&ドロップテスト")
    root.geometry("600x400")
    
    # フレーム作成
    frame = ctk.CTkFrame(root)
    frame.pack(fill="both", expand=True, padx=20, pady=20)
    
    # ラベル
    label = ctk.CTkLabel(
        frame,
        text="ここにファイルやフォルダをドラッグ&ドロップしてください",
        font=("", 16)
    )
    label.pack(pady=20)
    
    # ログテキストボックス
    log_text = ctk.CTkTextbox(frame, height=200)
    log_text.pack(fill="both", expand=True, padx=10, pady=10)
    
    def on_files_dropped(files):
        """ファイルがドロップされた時の処理"""
        log_text.insert("end", f"\n{len(files)}個のアイテムがドロップされました:\n")
        for file in files:
            file_type = "ディレクトリ" if file.is_dir() else "ファイル"
            log_text.insert("end", f"- {file_type}: {file}\n")
        log_text.see("end")
    
    def file_filter(path):
        """すべてのファイルを受け入れる"""
        return True
    
    # ドラッグ&ドロップハンドラー設定
    try:
        handler = DragDropHandler(frame, on_files_dropped, file_filter)
        label.configure(text="✅ ドラッグ&ドロップが有効です")
    except Exception as e:
        label.configure(text=f"❌ エラー: {e}")
        print(f"ドラッグ&ドロップの初期化エラー: {e}")
    
    # メインループ
    root.mainloop()

if __name__ == "__main__":
    main()