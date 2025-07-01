"""
エラーダイアログのUIモジュール
"""
import customtkinter as ctk
from tkinter import messagebox
from typing import Optional, List
import traceback
import platform
import subprocess

class ErrorDialog(ctk.CTkToplevel):
    """詳細なエラーダイアログ"""
    
    def __init__(self, parent, title: str, message: str, 
                 details: Optional[str] = None,
                 suggestions: Optional[List[str]] = None):
        super().__init__(parent)
        
        self.title(title)
        self.geometry("600x500")
        self.minsize(500, 400)
        
        # ウィンドウを中央に配置
        self.transient(parent)
        self.grab_set()
        
        # メインフレーム
        main_frame = ctk.CTkFrame(self)
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # エラーアイコンとメッセージ
        header_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        header_frame.pack(fill="x", pady=(0, 15))
        
        # エラーアイコン（絵文字）
        icon_label = ctk.CTkLabel(
            header_frame,
            text="⚠️",
            font=("", 32)
        )
        icon_label.pack(side="left", padx=(0, 15))
        
        # メッセージ
        message_label = ctk.CTkLabel(
            header_frame,
            text=message,
            font=("", 14),
            wraplength=450,
            justify="left"
        )
        message_label.pack(side="left", fill="x", expand=True)
        
        # 提案セクション
        if suggestions:
            suggestions_frame = ctk.CTkFrame(main_frame)
            suggestions_frame.pack(fill="x", pady=(0, 15))
            
            suggestions_title = ctk.CTkLabel(
                suggestions_frame,
                text="💡 解決方法:",
                font=("", 12, "bold")
            )
            suggestions_title.pack(anchor="w", pady=(0, 5))
            
            for suggestion in suggestions:
                suggestion_label = ctk.CTkLabel(
                    suggestions_frame,
                    text=f"• {suggestion}",
                    font=("", 11),
                    justify="left",
                    wraplength=550
                )
                suggestion_label.pack(anchor="w", padx=(20, 0), pady=2)
        
        # 詳細セクション
        if details:
            details_frame = ctk.CTkFrame(main_frame)
            details_frame.pack(fill="both", expand=True, pady=(0, 15))
            
            details_title = ctk.CTkLabel(
                details_frame,
                text="📋 詳細情報:",
                font=("", 12, "bold")
            )
            details_title.pack(anchor="w", pady=(0, 5))
            
            # スクロール可能なテキストボックス
            self.details_text = ctk.CTkTextbox(
                details_frame,
                height=150,
                font=("Consolas" if platform.system() == "Windows" else "Courier", 10)
            )
            self.details_text.pack(fill="both", expand=True)
            self.details_text.insert("1.0", details)
            self.details_text.configure(state="disabled")
        
        # ボタンフレーム
        button_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        button_frame.pack(fill="x")
        
        # コピーボタン
        if details:
            copy_button = ctk.CTkButton(
                button_frame,
                text="詳細をコピー",
                width=120,
                command=self._copy_details
            )
            copy_button.pack(side="left", padx=(0, 10))
        
        # 閉じるボタン
        close_button = ctk.CTkButton(
            button_frame,
            text="閉じる",
            width=100,
            command=self.destroy
        )
        close_button.pack(side="right")
        
        # ESCキーで閉じる
        self.bind("<Escape>", lambda e: self.destroy())
        
        # フォーカス設定
        self.focus_set()
        
    def _copy_details(self):
        """詳細をクリップボードにコピー"""
        if hasattr(self, 'details_text'):
            details = self.details_text.get("1.0", "end-1c")
            self.clipboard_clear()
            self.clipboard_append(details)
            
            # フィードバック表示
            messagebox.showinfo("コピー完了", "詳細情報をクリップボードにコピーしました")


class SimpleErrorDialog:
    """シンプルなエラーダイアログ（messagebox使用）"""
    
    @staticmethod
    def show_error(parent, title: str, message: str):
        """エラーメッセージを表示"""
        messagebox.showerror(title, message)
        
    @staticmethod
    def show_warning(parent, title: str, message: str):
        """警告メッセージを表示"""
        messagebox.showwarning(title, message)
        
    @staticmethod
    def show_info(parent, title: str, message: str):
        """情報メッセージを表示"""
        messagebox.showinfo(title, message)
        
    @staticmethod
    def ask_yes_no(parent, title: str, message: str) -> bool:
        """Yes/No質問を表示"""
        return messagebox.askyesno(title, message)
        
    @staticmethod
    def ask_ok_cancel(parent, title: str, message: str) -> bool:
        """OK/Cancel質問を表示"""
        return messagebox.askokcancel(title, message)


def show_error_with_details(parent, error: Exception, context: str = ""):
    """例外情報を含む詳細なエラーダイアログを表示"""
    # エラーメッセージを構築
    title = "エラーが発生しました"
    message = str(error)
    
    # 詳細情報
    details_parts = []
    if context:
        details_parts.append(f"コンテキスト: {context}")
    details_parts.append(f"エラータイプ: {type(error).__name__}")
    details_parts.append(f"エラーメッセージ: {str(error)}")
    details_parts.append("\nスタックトレース:")
    details_parts.append(traceback.format_exc())
    
    details = "\n".join(details_parts)
    
    # エラータイプに応じた提案
    suggestions = []
    if isinstance(error, PermissionError):
        suggestions = [
            "ファイルが他のプログラムで開かれていないか確認してください",
            "ファイルの書き込み権限を確認してください",
            "別の保存先を選択してみてください"
        ]
    elif isinstance(error, FileNotFoundError):
        suggestions = [
            "ファイルパスが正しいか確認してください",
            "ファイルが移動・削除されていないか確認してください"
        ]
    elif isinstance(error, MemoryError):
        suggestions = [
            "より小さな画像で試してください",
            "他のアプリケーションを終了してメモリを解放してください"
        ]
    elif isinstance(error, ValueError):
        suggestions = [
            "入力値が正しい形式か確認してください",
            "必要な項目がすべて入力されているか確認してください"
        ]
    
    # ダイアログを表示
    dialog = ErrorDialog(parent, title, message, details, suggestions)
    
    # ウィンドウを中央に配置
    dialog.update_idletasks()
    x = (dialog.winfo_screenwidth() // 2) - (dialog.winfo_width() // 2)
    y = (dialog.winfo_screenheight() // 2) - (dialog.winfo_height() // 2)
    dialog.geometry(f"+{x}+{y}")
    
    return dialog