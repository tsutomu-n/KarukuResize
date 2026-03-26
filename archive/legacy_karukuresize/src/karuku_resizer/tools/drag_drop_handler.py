"""
ドラッグ&ドロップ機能のハンドラーモジュール
"""
import customtkinter as ctk
from pathlib import Path
from typing import Any, Callable, Optional, List, Protocol, cast
import platform
import sys

# Python 3.13でのtkinterdnd2の問題を回避
TKDND_AVAILABLE = False
DND_FILES = None
TkinterDnD = None

if sys.version_info < (3, 13):
    try:
        from tkinterdnd2 import DND_FILES, TkinterDnD
        TKDND_AVAILABLE = True
    except ImportError:
        print("警告: tkinterdnd2が見つかりません。ドラッグ&ドロップ機能は無効です。")
else:
    print("情報: Python 3.13以降ではドラッグ&ドロップ機能は無効です。")


class _DndCapableWidget(Protocol):
    def drop_target_register(self, *dndtypes: Any) -> Any: ...
    def dnd_bind(self, sequence: str, func: Any) -> Any: ...


_INITIALIZED_ROOT_KEYS: set[int] = set()

class DragDropHandler:
    """ドラッグ&ドロップ機能を管理するクラス"""
    
    def __init__(self, widget: ctk.CTkFrame,
                 on_drop_callback: Callable[[List[Path]], None],
                 file_filter: Optional[Callable[[Path], bool]] = None):
        """
        Args:
            widget: ドラッグ&ドロップを受け付けるウィジェット
            on_drop_callback: ファイルドロップ時のコールバック
            file_filter: ファイルフィルター関数（Trueを返すファイルのみ受け付ける）
        """
        self.widget = widget
        self.on_drop_callback = on_drop_callback
        self.file_filter = file_filter or self._default_image_filter
        self.original_bg_color = None
        
        if TKDND_AVAILABLE:
            try:
                self._setup_drag_drop()
            except Exception as e:
                print(f"ドラッグ&ドロップ機能の初期化に失敗しました: {e}")
        
    def _default_image_filter(self, path: Path) -> bool:
        """デフォルトの画像ファイルフィルター"""
        image_extensions = {'.jpg', '.jpeg', '.png', '.webp', '.bmp', '.gif', '.tiff', '.tif'}
        return path.suffix.lower() in image_extensions
    
    def _setup_drag_drop(self):
        """ドラッグ&ドロップのセットアップ"""
        if not TKDND_AVAILABLE:
            return
            
        try:
            # ウィジェットのマスターウィンドウを取得
            root = self.widget.winfo_toplevel()
            _INITIALIZED_ROOT_KEYS.add(id(root))

            # ドロップターゲットとして登録
            dnd_widget = cast(_DndCapableWidget, self.widget)
            dnd_widget.drop_target_register(DND_FILES)

            # イベントバインド
            dnd_widget.dnd_bind('<<DropEnter>>', self._on_drop_enter)
            dnd_widget.dnd_bind('<<DropLeave>>', self._on_drop_leave)
            dnd_widget.dnd_bind('<<Drop>>', self._on_drop)
            
        except Exception as e:
            print(f"ドラッグ&ドロップの初期化エラー: {e}")
            
    def _on_drop_enter(self, event):
        """ドラッグエンター時の処理"""
        if hasattr(self.widget, 'configure'):
            # 現在の背景色を保存
            if hasattr(self.widget, 'cget'):
                try:
                    self.original_bg_color = self.widget.cget('fg_color')
                except Exception:
                    self.original_bg_color = None
            
            # ハイライト表示
            try:
                self.widget.configure(fg_color='#E3F2FD')  # 薄い青色
            except Exception:
                pass
                
    def _on_drop_leave(self, event):
        """ドラッグリーブ時の処理"""
        if hasattr(self.widget, 'configure') and self.original_bg_color:
            try:
                self.widget.configure(fg_color=self.original_bg_color)
            except Exception:
                pass
                
    def _on_drop(self, event):
        """ファイルドロップ時の処理"""
        # ハイライトを解除
        self._on_drop_leave(event)
        
        # ドロップされたファイルパスを解析
        files = self._parse_drop_data(event.data)
        
        # 有効なファイル/ディレクトリをフィルター
        valid_items = []
        for file_path in files:
            try:
                path = Path(file_path)
                if path.exists():
                    # ディレクトリまたはファイルフィルターを通過したファイル
                    if path.is_dir() or (path.is_file() and self.file_filter(path)):
                        valid_items.append(path)
            except Exception as e:
                print(f"ファイルパス解析エラー: {e}")
                
        # コールバックを呼び出し
        if valid_items:
            self.on_drop_callback(valid_items)
            
    def _parse_drop_data(self, data: str) -> List[str]:
        """ドロップデータを解析してファイルパスのリストを返す"""
        # プラットフォーム別の処理
        if platform.system() == 'Windows':
            # Windowsでは波括弧で囲まれている場合がある
            if data.startswith('{') and data.endswith('}'):
                data = data[1:-1]
                
        # スペースで分割（ただし、パス内のスペースは考慮）
        files = []
        current_file = []
        in_quotes = False
        
        for char in data:
            if char == '"':
                in_quotes = not in_quotes
            elif char == ' ' and not in_quotes:
                if current_file:
                    files.append(''.join(current_file))
                    current_file = []
            else:
                current_file.append(char)
                
        if current_file:
            files.append(''.join(current_file))
            
        # 空文字列を除去
        return [f.strip() for f in files if f.strip()]


class DragDropArea(ctk.CTkFrame):
    """ドラッグ&ドロップエリアウィジェット"""
    
    def __init__(self, master, **kwargs):
        # カスタム引数を抽出
        on_drop = kwargs.pop('on_drop', None)
        file_filter = kwargs.pop('file_filter', None)
        
        super().__init__(master, **kwargs)
        
        # デフォルトスタイル設定
        self.configure(
            fg_color='#F5F5F5',
            corner_radius=10,
            border_width=2,
            border_color='#CCCCCC'
        )
        
        # ラベルのテキストを決定
        if TKDND_AVAILABLE:
            label_text = "ここに画像をドラッグ&ドロップ\nまたはクリックして選択"
        else:
            label_text = "クリックして画像を選択\n(ドラッグ&ドロップは利用できません)"
        
        # ラベルを追加
        self.label = ctk.CTkLabel(
            self,
            text=label_text,
            font=("", 14),
            text_color='#666666'
        )
        self.label.pack(expand=True, fill='both', padx=20, pady=40)
        
        # ドラッグ&ドロップハンドラーを設定
        self.drag_drop_handler = None
        if on_drop and TKDND_AVAILABLE:
            try:
                self.drag_drop_handler = DragDropHandler(self, on_drop, file_filter)
            except Exception as e:
                print(f"ドラッグ&ドロップハンドラーの初期化エラー: {e}")
            
        # クリックでファイル選択ダイアログを開く
        self.bind("<Button-1>", self._on_click)
        self.label.bind("<Button-1>", self._on_click)
        
    def _on_click(self, event):
        """クリック時の処理（オーバーライド可能）"""
        pass
        
    def set_file_callback(self, callback: Callable):
        """ファイル選択時のコールバックを設定"""
        self._file_callback = callback
        
    def update_status(self, text: str, is_error: bool = False):
        """ステータステキストを更新"""
        self.label.configure(
            text=text,
            text_color='#D32F2F' if is_error else '#666666'
        )
