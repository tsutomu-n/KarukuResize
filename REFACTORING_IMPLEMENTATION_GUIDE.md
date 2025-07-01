# KarukuResize リファクタリング実装ガイド

## 概要

このドキュメントは、KarukuResize GUIのリファクタリングを実際に実装する際の具体的なコード例と手順を提供します。

## ステップ1: プロジェクト構造の再編成

### 新しいディレクトリ構造の作成

```bash
# 新しいディレクトリ構造を作成
mkdir -p karukuresize/gui/{views,view_models,widgets,utils}
mkdir -p karukuresize/{models,services}
touch karukuresize/__init__.py
touch karukuresize/gui/__init__.py
touch karukuresize/gui/views/__init__.py
touch karukuresize/gui/view_models/__init__.py
touch karukuresize/gui/widgets/__init__.py
touch karukuresize/gui/utils/__init__.py
touch karukuresize/models/__init__.py
touch karukuresize/services/__init__.py
```

## ステップ2: 定数とユーティリティの抽出

### constants.py の作成

```python
# karukuresize/gui/utils/constants.py
"""UI定数とアプリケーション設定"""
from dataclasses import dataclass
from typing import Tuple


@dataclass(frozen=True)
class WindowConfig:
    """ウィンドウ設定"""
    DEFAULT_WIDTH: int = 1000
    DEFAULT_HEIGHT: int = 900
    MIN_WIDTH: int = 900
    MIN_HEIGHT: int = 800
    TITLE: str = "画像処理ツール"


@dataclass(frozen=True)
class FontConfig:
    """フォント設定"""
    SIZE_NORMAL: int = 15
    SIZE_BUTTON: int = 15
    SIZE_HEADING: int = 18
    SIZE_SMALL: int = 13
    WEIGHT_NORMAL: str = "normal"
    WEIGHT_BOLD: str = "bold"


@dataclass(frozen=True)
class ColorTheme:
    """カラーテーマ設定"""
    BG_PRIMARY: str = "#F8F9FA"
    BG_SECONDARY: str = "#E9ECEF"
    TEXT_PRIMARY: str = "#212529"
    TEXT_SECONDARY: str = "#6C757D"
    ACCENT: str = "#6C63FF"
    ACCENT_HOVER: str = "#5A52D5"
    SUCCESS: str = "#28A745"
    ERROR: str = "#DC3545"
    WARNING: str = "#FFC107"


@dataclass(frozen=True)
class ProcessingConfig:
    """処理設定"""
    MAX_BATCH_SIZE: int = 1000
    THREAD_POOL_SIZE: int = 4
    PROGRESS_UPDATE_INTERVAL: float = 0.1
    DEFAULT_QUALITY: int = 85
    MIN_QUALITY: int = 1
    MAX_QUALITY: int = 100


# インスタンス化
WINDOW = WindowConfig()
FONT = FontConfig()
THEME = ColorTheme()
PROCESSING = ProcessingConfig()


# リサイズモードの定義
class ResizeMode:
    NONE = "none"
    WIDTH = "width"
    HEIGHT = "height"
    LONGEST_SIDE = "longest_side"
    PERCENTAGE = "percentage"
    
    DISPLAY_NAMES = {
        NONE: "リサイズなし",
        WIDTH: "幅を指定",
        HEIGHT: "高さを指定",
        LONGEST_SIDE: "縦横最大",
        PERCENTAGE: "パーセント"
    }


# 出力フォーマットの定義
class OutputFormat:
    ORIGINAL = "original"
    JPEG = "jpeg"
    PNG = "png"
    WEBP = "webp"
    
    DISPLAY_NAMES = {
        ORIGINAL: "オリジナル",
        JPEG: "JPEG",
        PNG: "PNG",
        WEBP: "WEBP"
    }


# ファイルタイプの定義
IMAGE_FILETYPES = [
    ("画像ファイル", "*.jpg *.jpeg *.png *.gif *.bmp *.tiff *.webp"),
    ("すべてのファイル", "*.*")
]
```

### ui_builders.py の作成

```python
# karukuresize/gui/utils/ui_builders.py
"""UI構築のヘルパー関数"""
import customtkinter as ctk
from typing import Optional, Tuple, Callable
from .constants import FONT, THEME


class UIBuilder:
    """UI構築のヘルパークラス"""
    
    @staticmethod
    def create_labeled_entry(
        parent: ctk.CTkFrame,
        label_text: str,
        entry_width: int = 300,
        **entry_kwargs
    ) -> Tuple[ctk.CTkFrame, ctk.CTkLabel, ctk.CTkEntry]:
        """ラベル付きエントリーを作成"""
        frame = ctk.CTkFrame(parent, fg_color="transparent")
        frame.grid_columnconfigure(1, weight=1)
        
        label = ctk.CTkLabel(
            frame,
            text=label_text,
            font=ctk.CTkFont(size=FONT.SIZE_NORMAL),
            text_color=THEME.TEXT_PRIMARY
        )
        label.grid(row=0, column=0, padx=(0, 10), sticky="w")
        
        entry = ctk.CTkEntry(
            frame,
            width=entry_width,
            font=ctk.CTkFont(size=FONT.SIZE_NORMAL),
            **entry_kwargs
        )
        entry.grid(row=0, column=1, sticky="ew")
        
        return frame, label, entry
    
    @staticmethod
    def create_button(
        parent: ctk.CTkFrame,
        text: str,
        command: Callable,
        variant: str = "primary",
        **kwargs
    ) -> ctk.CTkButton:
        """統一されたスタイルのボタンを作成"""
        if variant == "primary":
            fg_color = THEME.ACCENT
            hover_color = THEME.ACCENT_HOVER
            text_color = "white"
        elif variant == "secondary":
            fg_color = THEME.BG_SECONDARY
            hover_color = "#DEE2E6"
            text_color = THEME.TEXT_PRIMARY
        elif variant == "danger":
            fg_color = THEME.ERROR
            hover_color = "#C82333"
            text_color = "white"
        else:
            fg_color = THEME.BG_SECONDARY
            hover_color = "#DEE2E6"
            text_color = THEME.TEXT_PRIMARY
        
        button = ctk.CTkButton(
            parent,
            text=text,
            command=command,
            font=ctk.CTkFont(size=FONT.SIZE_BUTTON, weight=FONT.WEIGHT_BOLD),
            fg_color=fg_color,
            hover_color=hover_color,
            text_color=text_color,
            **kwargs
        )
        return button
    
    @staticmethod
    def create_frame_with_title(
        parent: ctk.CTkFrame,
        title: str,
        icon: Optional[str] = None
    ) -> ctk.CTkFrame:
        """タイトル付きフレームを作成"""
        frame = ctk.CTkFrame(
            parent,
            corner_radius=10,
            border_width=1,
            border_color=THEME.BG_SECONDARY
        )
        
        title_text = f"{icon} {title}" if icon else title
        title_label = ctk.CTkLabel(
            frame,
            text=title_text,
            font=ctk.CTkFont(size=FONT.SIZE_HEADING, weight=FONT.WEIGHT_BOLD),
            text_color=THEME.TEXT_PRIMARY
        )
        title_label.pack(anchor="w", padx=15, pady=(10, 5))
        
        content_frame = ctk.CTkFrame(frame, fg_color="transparent")
        content_frame.pack(fill="both", expand=True, padx=15, pady=(0, 15))
        
        return content_frame
```

## ステップ3: ViewModelの実装

### base_view_model.py

```python
# karukuresize/gui/view_models/base_view_model.py
"""ViewModelの基底クラス"""
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Callable
import threading


class Observable:
    """観察可能なプロパティを持つクラス"""
    
    def __init__(self):
        self._observers: Dict[str, List[Callable]] = {}
        self._properties: Dict[str, Any] = {}
        self._lock = threading.Lock()
    
    def bind(self, property_name: str, callback: Callable):
        """プロパティの変更を監視"""
        with self._lock:
            if property_name not in self._observers:
                self._observers[property_name] = []
            self._observers[property_name].append(callback)
    
    def unbind(self, property_name: str, callback: Callable):
        """監視を解除"""
        with self._lock:
            if property_name in self._observers:
                self._observers[property_name].remove(callback)
    
    def _notify(self, property_name: str, value: Any):
        """プロパティ変更を通知"""
        with self._lock:
            if property_name in self._observers:
                for callback in self._observers[property_name]:
                    callback(value)
    
    def _get_property(self, name: str, default: Any = None) -> Any:
        """プロパティを取得"""
        return self._properties.get(name, default)
    
    def _set_property(self, name: str, value: Any):
        """プロパティを設定"""
        old_value = self._properties.get(name)
        if old_value != value:
            self._properties[name] = value
            self._notify(name, value)


class BaseViewModel(Observable, ABC):
    """ViewModelの基底クラス"""
    
    def __init__(self):
        super().__init__()
        self._is_busy = False
        self._error_message = ""
    
    @property
    def is_busy(self) -> bool:
        """処理中フラグ"""
        return self._get_property("is_busy", False)
    
    @is_busy.setter
    def is_busy(self, value: bool):
        self._set_property("is_busy", value)
    
    @property
    def error_message(self) -> str:
        """エラーメッセージ"""
        return self._get_property("error_message", "")
    
    @error_message.setter
    def error_message(self, value: str):
        self._set_property("error_message", value)
    
    @abstractmethod
    def initialize(self):
        """初期化処理"""
        pass
    
    @abstractmethod
    def cleanup(self):
        """クリーンアップ処理"""
        pass
```

### resize_view_model.py

```python
# karukuresize/gui/view_models/resize_view_model.py
"""リサイズタブのViewModel"""
from typing import Optional, Dict, Any
import threading
from pathlib import Path

from .base_view_model import BaseViewModel
from ...models.resize_settings import ResizeSettings
from ...services.image_service import ImageService
from ..utils.constants import ResizeMode, OutputFormat, PROCESSING


class ResizeViewModel(BaseViewModel):
    """リサイズ機能のViewModel"""
    
    def __init__(self, image_service: ImageService):
        super().__init__()
        self.image_service = image_service
        self._settings = ResizeSettings()
        self._current_thread: Optional[threading.Thread] = None
        
    def initialize(self):
        """初期化処理"""
        # デフォルト設定を適用
        self.resize_mode = ResizeMode.LONGEST_SIDE
        self.resize_value = 1920
        self.quality = PROCESSING.DEFAULT_QUALITY
        self.output_format = OutputFormat.ORIGINAL
        
    def cleanup(self):
        """クリーンアップ処理"""
        self.cancel_processing()
    
    # プロパティ定義
    @property
    def input_path(self) -> str:
        return self._get_property("input_path", "")
    
    @input_path.setter
    def input_path(self, value: str):
        self._set_property("input_path", value)
        self._validate_input()
    
    @property
    def output_directory(self) -> str:
        return self._get_property("output_directory", "")
    
    @output_directory.setter
    def output_directory(self, value: str):
        self._set_property("output_directory", value)
    
    @property
    def resize_mode(self) -> str:
        return self._get_property("resize_mode", ResizeMode.NONE)
    
    @resize_mode.setter
    def resize_mode(self, value: str):
        self._set_property("resize_mode", value)
        self._update_settings()
    
    @property
    def resize_value(self) -> int:
        return self._get_property("resize_value", 0)
    
    @resize_value.setter
    def resize_value(self, value: int):
        self._set_property("resize_value", max(0, value))
        self._update_settings()
    
    @property
    def quality(self) -> int:
        return self._get_property("quality", PROCESSING.DEFAULT_QUALITY)
    
    @quality.setter
    def quality(self, value: int):
        value = max(PROCESSING.MIN_QUALITY, min(PROCESSING.MAX_QUALITY, value))
        self._set_property("quality", value)
        self._update_settings()
    
    @property
    def output_format(self) -> str:
        return self._get_property("output_format", OutputFormat.ORIGINAL)
    
    @output_format.setter
    def output_format(self, value: str):
        self._set_property("output_format", value)
        self._update_settings()
    
    @property
    def can_process(self) -> bool:
        """処理可能かどうか"""
        return (
            bool(self.input_path) and
            Path(self.input_path).exists() and
            bool(self.output_directory) and
            Path(self.output_directory).exists() and
            not self.is_busy
        )
    
    # メソッド
    def start_processing(self):
        """画像処理を開始"""
        if not self.can_process:
            self.error_message = "入力ファイルまたは出力先が無効です"
            return
        
        self.is_busy = True
        self.error_message = ""
        
        self._current_thread = threading.Thread(
            target=self._process_image,
            daemon=True
        )
        self._current_thread.start()
    
    def cancel_processing(self):
        """処理をキャンセル"""
        if self._current_thread and self._current_thread.is_alive():
            # キャンセル処理の実装
            self.is_busy = False
    
    def _process_image(self):
        """画像処理の実行"""
        try:
            result = self.image_service.process_image(
                self.input_path,
                self.output_directory,
                self._settings
            )
            
            if result.success:
                self._notify("processing_completed", result)
            else:
                self.error_message = result.error_message
                
        except Exception as e:
            self.error_message = str(e)
        finally:
            self.is_busy = False
    
    def _validate_input(self):
        """入力の検証"""
        if self.input_path and not Path(self.input_path).exists():
            self.error_message = "指定されたファイルが見つかりません"
        else:
            self.error_message = ""
    
    def _update_settings(self):
        """設定を更新"""
        self._settings.resize_mode = self.resize_mode
        self._settings.resize_value = self.resize_value
        self._settings.quality = self.quality
        self._settings.output_format = self.output_format
    
    def apply_preset(self, preset_data: Dict[str, Any]):
        """プリセットを適用"""
        self.resize_mode = preset_data.get("resize_mode", ResizeMode.NONE)
        self.resize_value = preset_data.get("resize_value", 0)
        self.quality = preset_data.get("quality", PROCESSING.DEFAULT_QUALITY)
        self.output_format = preset_data.get("output_format", OutputFormat.ORIGINAL)
```

## ステップ4: Viewの実装

### base_view.py

```python
# karukuresize/gui/views/base_view.py
"""Viewの基底クラス"""
import customtkinter as ctk
from abc import ABC, abstractmethod
from typing import Optional

from ..view_models.base_view_model import BaseViewModel


class BaseView(ctk.CTkFrame, ABC):
    """Viewの基底クラス"""
    
    def __init__(self, parent, view_model: Optional[BaseViewModel] = None):
        super().__init__(parent)
        self._view_model = view_model
        self._bindings = []
        
        if self._view_model:
            self._setup_bindings()
        
        self._create_widgets()
        self._layout_widgets()
    
    @abstractmethod
    def _create_widgets(self):
        """ウィジェットを作成"""
        pass
    
    @abstractmethod
    def _layout_widgets(self):
        """ウィジェットを配置"""
        pass
    
    def _setup_bindings(self):
        """ViewModelとのバインディングを設定"""
        if self._view_model:
            # 共通のバインディング
            self._view_model.bind("is_busy", self._on_busy_changed)
            self._view_model.bind("error_message", self._on_error_changed)
    
    def _on_busy_changed(self, is_busy: bool):
        """処理中状態が変更されたとき"""
        # サブクラスでオーバーライド
        pass
    
    def _on_error_changed(self, error_message: str):
        """エラーメッセージが変更されたとき"""
        # サブクラスでオーバーライド
        pass
    
    def cleanup(self):
        """クリーンアップ処理"""
        if self._view_model:
            self._view_model.cleanup()
```

### resize_tab_view.py

```python
# karukuresize/gui/views/resize_tab_view.py
"""リサイズタブのView"""
import customtkinter as ctk
from tkinter import filedialog
from pathlib import Path

from .base_view import BaseView
from ..view_models.resize_view_model import ResizeViewModel
from ..utils.ui_builders import UIBuilder
from ..utils.constants import (
    WINDOW, FONT, THEME, ResizeMode, OutputFormat, IMAGE_FILETYPES
)


class ResizeTabView(BaseView):
    """リサイズタブのView"""
    
    def __init__(self, parent, view_model: ResizeViewModel):
        self.view_model = view_model
        super().__init__(parent, view_model)
    
    def _create_widgets(self):
        """ウィジェットを作成"""
        # スクロール可能なフレーム
        self.scroll_frame = ctk.CTkScrollableFrame(self)
        
        # 入力セクション
        self._create_input_section()
        
        # リサイズ設定セクション
        self._create_resize_section()
        
        # 品質設定セクション
        self._create_quality_section()
        
        # アクションボタン
        self._create_action_buttons()
    
    def _layout_widgets(self):
        """ウィジェットを配置"""
        self.scroll_frame.pack(fill="both", expand=True, padx=20, pady=20)
    
    def _create_input_section(self):
        """入力セクションを作成"""
        input_frame = UIBuilder.create_frame_with_title(
            self.scroll_frame, "入力設定", "📁"
        )
        
        # 入力ファイル
        input_row, _, self.input_entry = UIBuilder.create_labeled_entry(
            input_frame, "入力ファイル:", entry_width=400
        )
        input_row.pack(fill="x", pady=5)
        
        browse_btn = UIBuilder.create_button(
            input_row, "参照...", self._browse_input, variant="secondary"
        )
        browse_btn.grid(row=0, column=2, padx=(10, 0))
        
        # 出力ディレクトリ
        output_row, _, self.output_entry = UIBuilder.create_labeled_entry(
            input_frame, "出力先:", entry_width=400
        )
        output_row.pack(fill="x", pady=5)
        
        browse_output_btn = UIBuilder.create_button(
            output_row, "参照...", self._browse_output, variant="secondary"
        )
        browse_output_btn.grid(row=0, column=2, padx=(10, 0))
        
        # ViewModelとのバインディング
        self.input_entry.bind("<KeyRelease>", 
            lambda e: setattr(self.view_model, "input_path", self.input_entry.get())
        )
        self.output_entry.bind("<KeyRelease>",
            lambda e: setattr(self.view_model, "output_directory", self.output_entry.get())
        )
    
    def _create_resize_section(self):
        """リサイズ設定セクションを作成"""
        resize_frame = UIBuilder.create_frame_with_title(
            self.scroll_frame, "リサイズ設定", "📐"
        )
        
        # リサイズモード
        mode_frame = ctk.CTkFrame(resize_frame, fg_color="transparent")
        mode_frame.pack(fill="x", pady=5)
        
        ctk.CTkLabel(
            mode_frame, 
            text="リサイズモード:",
            font=ctk.CTkFont(size=FONT.SIZE_NORMAL)
        ).pack(side="left", padx=(0, 10))
        
        self.resize_mode_var = ctk.StringVar(value=ResizeMode.LONGEST_SIDE)
        self.resize_mode_menu = ctk.CTkOptionMenu(
            mode_frame,
            variable=self.resize_mode_var,
            values=list(ResizeMode.DISPLAY_NAMES.values()),
            command=self._on_resize_mode_changed
        )
        self.resize_mode_menu.pack(side="left")
        
        # リサイズ値
        value_frame, _, self.resize_value_entry = UIBuilder.create_labeled_entry(
            resize_frame, "サイズ:", entry_width=100
        )
        value_frame.pack(fill="x", pady=5)
        
        self.resize_unit_label = ctk.CTkLabel(
            value_frame,
            text="px",
            font=ctk.CTkFont(size=FONT.SIZE_NORMAL)
        )
        self.resize_unit_label.grid(row=0, column=2, padx=(5, 0))
        
        # ViewModelとのバインディング
        self.resize_value_entry.bind("<KeyRelease>", self._on_resize_value_changed)
    
    def _create_quality_section(self):
        """品質設定セクションを作成"""
        quality_frame = UIBuilder.create_frame_with_title(
            self.scroll_frame, "出力設定", "⚙️"
        )
        
        # 出力フォーマット
        format_frame = ctk.CTkFrame(quality_frame, fg_color="transparent")
        format_frame.pack(fill="x", pady=5)
        
        ctk.CTkLabel(
            format_frame,
            text="出力形式:",
            font=ctk.CTkFont(size=FONT.SIZE_NORMAL)
        ).pack(side="left", padx=(0, 10))
        
        self.format_var = ctk.StringVar(value=OutputFormat.ORIGINAL)
        self.format_menu = ctk.CTkOptionMenu(
            format_frame,
            variable=self.format_var,
            values=list(OutputFormat.DISPLAY_NAMES.values()),
            command=self._on_format_changed
        )
        self.format_menu.pack(side="left")
        
        # 品質スライダー
        quality_frame_inner = ctk.CTkFrame(quality_frame, fg_color="transparent")
        quality_frame_inner.pack(fill="x", pady=10)
        
        ctk.CTkLabel(
            quality_frame_inner,
            text="品質:",
            font=ctk.CTkFont(size=FONT.SIZE_NORMAL)
        ).pack(side="left", padx=(0, 10))
        
        self.quality_slider = ctk.CTkSlider(
            quality_frame_inner,
            from_=1,
            to=100,
            command=self._on_quality_changed
        )
        self.quality_slider.pack(side="left", fill="x", expand=True, padx=10)
        self.quality_slider.set(85)
        
        self.quality_label = ctk.CTkLabel(
            quality_frame_inner,
            text="85%",
            font=ctk.CTkFont(size=FONT.SIZE_NORMAL)
        )
        self.quality_label.pack(side="left")
    
    def _create_action_buttons(self):
        """アクションボタンを作成"""
        button_frame = ctk.CTkFrame(self.scroll_frame, fg_color="transparent")
        button_frame.pack(fill="x", pady=20)
        
        self.process_button = UIBuilder.create_button(
            button_frame,
            "処理開始",
            self._on_process_clicked,
            variant="primary",
            width=150
        )
        self.process_button.pack(side="left", padx=5)
        
        self.cancel_button = UIBuilder.create_button(
            button_frame,
            "キャンセル",
            self._on_cancel_clicked,
            variant="danger",
            width=150
        )
        self.cancel_button.pack(side="left", padx=5)
        self.cancel_button.configure(state="disabled")
    
    def _setup_bindings(self):
        """ViewModelとのバインディングを設定"""
        super()._setup_bindings()
        
        # プロパティ変更の監視
        self.view_model.bind("input_path", self._on_input_path_changed)
        self.view_model.bind("output_directory", self._on_output_dir_changed)
        self.view_model.bind("resize_mode", self._on_vm_resize_mode_changed)
        self.view_model.bind("resize_value", self._on_vm_resize_value_changed)
        self.view_model.bind("quality", self._on_vm_quality_changed)
        self.view_model.bind("output_format", self._on_vm_format_changed)
        self.view_model.bind("processing_completed", self._on_processing_completed)
    
    # イベントハンドラ
    def _browse_input(self):
        """入力ファイルを選択"""
        filename = filedialog.askopenfilename(
            title="入力ファイルを選択",
            filetypes=IMAGE_FILETYPES
        )
        if filename:
            self.view_model.input_path = filename
    
    def _browse_output(self):
        """出力ディレクトリを選択"""
        directory = filedialog.askdirectory(title="出力先フォルダを選択")
        if directory:
            self.view_model.output_directory = directory
    
    def _on_resize_mode_changed(self, value: str):
        """リサイズモード変更時"""
        # 表示名から実際の値に変換
        for mode, display_name in ResizeMode.DISPLAY_NAMES.items():
            if display_name == value:
                self.view_model.resize_mode = mode
                break
    
    def _on_resize_value_changed(self, event):
        """リサイズ値変更時"""
        try:
            value = int(self.resize_value_entry.get())
            self.view_model.resize_value = value
        except ValueError:
            pass
    
    def _on_format_changed(self, value: str):
        """出力形式変更時"""
        for fmt, display_name in OutputFormat.DISPLAY_NAMES.items():
            if display_name == value:
                self.view_model.output_format = fmt
                break
    
    def _on_quality_changed(self, value: float):
        """品質変更時"""
        self.view_model.quality = int(value)
    
    def _on_process_clicked(self):
        """処理開始ボタンクリック時"""
        self.view_model.start_processing()
    
    def _on_cancel_clicked(self):
        """キャンセルボタンクリック時"""
        self.view_model.cancel_processing()
    
    # ViewModelからの通知
    def _on_busy_changed(self, is_busy: bool):
        """処理中状態が変更されたとき"""
        if is_busy:
            self.process_button.configure(state="disabled")
            self.cancel_button.configure(state="normal")
        else:
            self.process_button.configure(state="normal")
            self.cancel_button.configure(state="disabled")
    
    def _on_error_changed(self, error_message: str):
        """エラーメッセージが変更されたとき"""
        if error_message:
            # エラーダイアログを表示
            from tkinter import messagebox
            messagebox.showerror("エラー", error_message)
    
    def _on_input_path_changed(self, path: str):
        """入力パスが変更されたとき"""
        self.input_entry.delete(0, "end")
        self.input_entry.insert(0, path)
    
    def _on_output_dir_changed(self, path: str):
        """出力ディレクトリが変更されたとき"""
        self.output_entry.delete(0, "end")
        self.output_entry.insert(0, path)
    
    def _on_vm_resize_mode_changed(self, mode: str):
        """ViewModelのリサイズモードが変更されたとき"""
        display_name = ResizeMode.DISPLAY_NAMES.get(mode, "")
        self.resize_mode_var.set(display_name)
    
    def _on_vm_resize_value_changed(self, value: int):
        """ViewModelのリサイズ値が変更されたとき"""
        self.resize_value_entry.delete(0, "end")
        self.resize_value_entry.insert(0, str(value))
    
    def _on_vm_quality_changed(self, quality: int):
        """ViewModelの品質が変更されたとき"""
        self.quality_slider.set(quality)
        self.quality_label.configure(text=f"{quality}%")
    
    def _on_vm_format_changed(self, fmt: str):
        """ViewModelの出力形式が変更されたとき"""
        display_name = OutputFormat.DISPLAY_NAMES.get(fmt, "")
        self.format_var.set(display_name)
    
    def _on_processing_completed(self, result):
        """処理が完了したとき"""
        from tkinter import messagebox
        messagebox.showinfo("完了", "画像処理が完了しました")
```

## ステップ5: メインウィンドウの実装

### main_window.py

```python
# karukuresize/gui/main_window.py
"""メインウィンドウ"""
import customtkinter as ctk
from pathlib import Path

from .views.resize_tab_view import ResizeTabView
from .view_models.resize_view_model import ResizeViewModel
from ..services.image_service import ImageService
from .utils.constants import WINDOW, THEME


class MainWindow(ctk.CTk):
    """メインウィンドウクラス"""
    
    def __init__(self):
        super().__init__()
        
        # ウィンドウ設定
        self.title(WINDOW.TITLE)
        self.geometry(f"{WINDOW.DEFAULT_WIDTH}x{WINDOW.DEFAULT_HEIGHT}")
        self.minsize(WINDOW.MIN_WIDTH, WINDOW.MIN_HEIGHT)
        
        # テーマ設定
        self.configure(fg_color=THEME.BG_PRIMARY)
        
        # サービスの初期化
        self.image_service = ImageService()
        
        # ViewModelの初期化
        self.resize_view_model = ResizeViewModel(self.image_service)
        
        # UIの構築
        self._create_widgets()
        self._create_menu_bar()
        
        # 初期化
        self.resize_view_model.initialize()
        
        # ウィンドウを中央に配置
        self._center_window()
    
    def _create_widgets(self):
        """ウィジェットを作成"""
        # メインコンテナ
        main_container = ctk.CTkFrame(self, fg_color="transparent")
        main_container.pack(fill="both", expand=True, padx=20, pady=20)
        
        # タブビュー
        self.tab_view = ctk.CTkTabview(main_container)
        self.tab_view.pack(fill="both", expand=True)
        
        # リサイズタブ
        resize_tab = self.tab_view.add("画像リサイズ")
        self.resize_view = ResizeTabView(resize_tab, self.resize_view_model)
        self.resize_view.pack(fill="both", expand=True)
        
        # 他のタブは遅延読み込み
        self.tab_view.add("プレビュー")
        self.tab_view.add("履歴")
        self.tab_view.add("統計")
    
    def _create_menu_bar(self):
        """メニューバーを作成"""
        # CustomTkinterはネイティブメニューバーをサポートしていないため
        # 代替実装またはtkinterのMenuを使用
        pass
    
    def _center_window(self):
        """ウィンドウを中央に配置"""
        self.update_idletasks()
        width = self.winfo_width()
        height = self.winfo_height()
        x = (self.winfo_screenwidth() // 2) - (width // 2)
        y = (self.winfo_screenheight() // 2) - (height // 2)
        self.geometry(f"{width}x{height}+{x}+{y}")
    
    def on_closing(self):
        """ウィンドウを閉じるとき"""
        # クリーンアップ
        self.resize_view.cleanup()
        self.destroy()


def main():
    """アプリケーションのエントリーポイント"""
    # テーマ設定
    ctk.set_appearance_mode("light")
    
    # アプリケーション起動
    app = MainWindow()
    app.protocol("WM_DELETE_WINDOW", app.on_closing)
    app.mainloop()


if __name__ == "__main__":
    main()
```

## ステップ6: 段階的移行計画

### 移行手順

1. **新しい構造でテストを作成**
   ```bash
   # tests/test_view_models.py
   pytest tests/test_view_models.py
   ```

2. **既存コードと新コードの並行稼働**
   ```python
   # resize_images_gui.py の一時的な変更
   if USE_NEW_ARCHITECTURE:
       from karukuresize.gui.main_window import main
   else:
       # 既存のコード
   ```

3. **機能ごとに段階的に移行**
   - Week 1: リサイズタブ
   - Week 2: プレビュータブ
   - Week 3: 履歴タブ
   - Week 4: 統計タブ

4. **統合テスト**
   ```bash
   pytest tests/integration/
   ```

5. **パフォーマンステスト**
   ```bash
   python -m cProfile -o profile.stats karukuresize/gui/main_window.py
   ```

6. **完全移行**
   - 古いコードの削除
   - ドキュメントの更新
   - リリース準備

## まとめ

このリファクタリング実装ガイドは、KarukuResize GUIを保守可能で拡張可能なアーキテクチャに移行するための具体的な実装例を提供します。
段階的な移行により、リスクを最小限に抑えながら、コード品質を大幅に向上させることができます。

---

作成日: 2025年6月29日
最終更新: 2025年6月29日