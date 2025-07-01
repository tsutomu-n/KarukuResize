"""
Viewの基底クラス
"""
import customtkinter as ctk
from abc import ABC, abstractmethod
from typing import Optional, List, Tuple

from ..view_models.base_view_model import BaseViewModel


class BaseView(ctk.CTkFrame, ABC):
    """Viewの基底クラス"""
    
    def __init__(self, parent, view_model: Optional[BaseViewModel] = None):
        super().__init__(parent)
        self._view_model = view_model
        self._bindings: List[Tuple[str, callable]] = []
        
        # ウィジェットを作成
        self._create_widgets()
        self._layout_widgets()
        
        # ViewModelとのバインディングを設定
        if self._view_model:
            self._setup_bindings()
            
    @property
    def view_model(self) -> Optional[BaseViewModel]:
        """ViewModelを取得"""
        return self._view_model
    
    @abstractmethod
    def _create_widgets(self) -> None:
        """ウィジェットを作成"""
        pass
    
    @abstractmethod
    def _layout_widgets(self) -> None:
        """ウィジェットを配置"""
        pass
    
    def _setup_bindings(self) -> None:
        """ViewModelとのバインディングを設定"""
        if self._view_model:
            # 共通のバインディング
            self._bind_property("is_busy", self._on_busy_changed)
            self._bind_property("error_message", self._on_error_changed)
            self._bind_property("status_message", self._on_status_changed)
            self._bind_property("progress", self._on_progress_changed)
            self._bind_property("log_message", self._on_log_message)
    
    def _bind_property(self, property_name: str, callback: callable) -> None:
        """プロパティをバインド"""
        if self._view_model:
            self._view_model.bind(property_name, callback)
            self._bindings.append((property_name, callback))
    
    def _unbind_property(self, property_name: str, callback: callable) -> None:
        """プロパティのバインドを解除"""
        if self._view_model:
            self._view_model.unbind(property_name, callback)
            self._bindings = [(p, c) for p, c in self._bindings if p != property_name or c != callback]
    
    def _on_busy_changed(self, is_busy: bool) -> None:
        """処理中状態が変更されたとき"""
        # サブクラスでオーバーライド
        pass
    
    def _on_error_changed(self, error_message: str) -> None:
        """エラーメッセージが変更されたとき"""
        # サブクラスでオーバーライド
        pass
    
    def _on_status_changed(self, status_message: str) -> None:
        """ステータスメッセージが変更されたとき"""
        # サブクラスでオーバーライド
        pass
    
    def _on_progress_changed(self, progress: float) -> None:
        """進捗が変更されたとき"""
        # サブクラスでオーバーライド
        pass
    
    def _on_log_message(self, log_entry: dict) -> None:
        """ログメッセージが追加されたとき"""
        # サブクラスでオーバーライド
        pass
    
    def cleanup(self) -> None:
        """クリーンアップ処理"""
        # すべてのバインディングを解除
        for property_name, callback in self._bindings:
            if self._view_model:
                self._view_model.unbind(property_name, callback)
        self._bindings.clear()
        
        # ViewModelのクリーンアップ
        if self._view_model:
            self._view_model.cleanup()
    
    def show_error_dialog(self, title: str, message: str) -> None:
        """エラーダイアログを表示"""
        # CustomTkinterにはメッセージボックスがないので、tkinterを使用
        from tkinter import messagebox
        messagebox.showerror(title, message)
    
    def show_info_dialog(self, title: str, message: str) -> None:
        """情報ダイアログを表示"""
        from tkinter import messagebox
        messagebox.showinfo(title, message)
    
    def show_warning_dialog(self, title: str, message: str) -> None:
        """警告ダイアログを表示"""
        from tkinter import messagebox
        messagebox.showwarning(title, message)