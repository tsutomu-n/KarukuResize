"""
リサイズタブのView
"""
import customtkinter as ctk
from tkinter import filedialog
from pathlib import Path
from typing import Optional
import sys

# プロジェクトルートをPythonパスに追加
project_root = Path(__file__).parent.parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from .base_view import BaseView
from ..view_models.resize_view_model import ResizeViewModel
from ..utils.ui_builders import UIBuilder
from ..utils.constants import (
    WINDOW, FONT, THEME, UI,
    ResizeMode, OutputFormat, ProcessingMode,
    IMAGE_FILETYPES, ExifMode
)

# ドラッグ&ドロップのインポート
try:
    from drag_drop_handler import DragDropHandler, TKDND_AVAILABLE
except ImportError:
    TKDND_AVAILABLE = False
    DragDropHandler = None


class ResizeTabView(BaseView):
    """リサイズタブのView"""
    
    def __init__(self, parent, view_model: Optional[ResizeViewModel] = None):
        # ViewModelがない場合は作成
        if view_model is None:
            view_model = ResizeViewModel()
        super().__init__(parent, view_model)
        
    def _create_widgets(self) -> None:
        """ウィジェットを作成"""
        # スクロール可能なコンテナ
        self.scroll_frame = ctk.CTkScrollableFrame(
            self,
            corner_radius=0,
            fg_color="transparent"
        )
        
        # 処理モード選択
        self._create_mode_section()
        
        # 入力/出力設定セクション
        self._create_io_section()
        
        # リサイズ設定セクション
        self._create_resize_section()
        
        # 品質設定セクション
        self._create_quality_section()
        
        # ファイル名設定セクション
        self._create_filename_section()
        
        # アクションボタン
        self._create_action_buttons()
        
        # ログとプログレスバー
        self._create_log_section()
    
    def _layout_widgets(self) -> None:
        """ウィジェットを配置"""
        self.scroll_frame.pack(fill="both", expand=True)
    
    def _create_mode_section(self) -> None:
        """処理モード選択セクション"""
        mode_frame = UIBuilder.create_frame_with_title(
            self.scroll_frame, "処理モード", "⚙️"
        )
        mode_frame.pack(fill="x", padx=UI.PADDING_LARGE, pady=(UI.PADDING_LARGE, UI.PADDING_MEDIUM))
        
        # ラジオボタンフレーム
        radio_frame = ctk.CTkFrame(mode_frame, fg_color="transparent")
        radio_frame.pack(fill="x")
        
        self.mode_var = ctk.StringVar(value=ProcessingMode.SINGLE)
        
        self.single_radio = UIBuilder.create_radio_button(
            radio_frame,
            ProcessingMode.DISPLAY_NAMES[ProcessingMode.SINGLE],
            self.mode_var,
            ProcessingMode.SINGLE,
            command=self._on_mode_changed
        )
        self.single_radio.pack(side="left", padx=(0, UI.PADDING_LARGE))
        
        self.batch_radio = UIBuilder.create_radio_button(
            radio_frame,
            ProcessingMode.DISPLAY_NAMES[ProcessingMode.BATCH],
            self.mode_var,
            ProcessingMode.BATCH,
            command=self._on_mode_changed
        )
        self.batch_radio.pack(side="left")
    
    def _create_io_section(self) -> None:
        """入力/出力設定セクション"""
        io_frame = UIBuilder.create_frame_with_title(
            self.scroll_frame, "入力/出力設定", "📁"
        )
        io_frame.pack(fill="x", padx=UI.PADDING_LARGE, pady=UI.PADDING_MEDIUM)
        
        # 入力選択
        label_text = "入力ファイル:"
        if TKDND_AVAILABLE:
            label_text += " (ドラッグ&ドロップ対応)"
        
        self.input_label = ctk.CTkLabel(
            io_frame,
            text=label_text,
            font=ctk.CTkFont(size=FONT.SIZE_NORMAL),
            text_color=THEME.TEXT_PRIMARY
        )
        self.input_label.pack(anchor="w", pady=(0, UI.PADDING_SMALL))
        
        input_frame = ctk.CTkFrame(io_frame, fg_color="transparent")
        input_frame.pack(fill="x", pady=(0, UI.PADDING_MEDIUM))
        
        self.input_entry = ctk.CTkEntry(
            input_frame,
            font=ctk.CTkFont(size=FONT.SIZE_NORMAL),
            height=UI.ENTRY_HEIGHT
        )
        self.input_entry.pack(side="left", fill="x", expand=True)
        self.input_entry.bind("<KeyRelease>", self._on_input_changed)
        
        self.browse_input_btn = UIBuilder.create_button(
            input_frame,
            "参照...",
            self._browse_input,
            variant="secondary",
            width=100
        )
        self.browse_input_btn.pack(side="left", padx=(UI.PADDING_SMALL, 0))
        
        # ドラッグ&ドロップの設定
        if TKDND_AVAILABLE and DragDropHandler:
            try:
                self.drag_handler = DragDropHandler(
                    input_frame,  # 入力フレームに限定
                    self._on_files_dropped,
                    self._filter_valid_files
                )
            except Exception as e:
                print(f"ドラッグ&ドロップの初期化エラー: {e}")
        
        # 出力先選択
        output_label_text = "出力先フォルダ:"
        if TKDND_AVAILABLE:
            output_label_text += " (ドラッグ&ドロップ対応)"
            
        output_label = ctk.CTkLabel(
            io_frame,
            text=output_label_text,
            font=ctk.CTkFont(size=FONT.SIZE_NORMAL),
            text_color=THEME.TEXT_PRIMARY
        )
        output_label.pack(anchor="w", pady=(0, UI.PADDING_SMALL))
        
        output_frame = ctk.CTkFrame(io_frame, fg_color="transparent")
        output_frame.pack(fill="x")
        
        self.output_entry = ctk.CTkEntry(
            output_frame,
            font=ctk.CTkFont(size=FONT.SIZE_NORMAL),
            height=UI.ENTRY_HEIGHT
        )
        self.output_entry.pack(side="left", fill="x", expand=True)
        self.output_entry.bind("<KeyRelease>", self._on_output_changed)
        
        self.browse_output_btn = UIBuilder.create_button(
            output_frame,
            "参照...",
            self._browse_output,
            variant="secondary",
            width=100
        )
        self.browse_output_btn.pack(side="left", padx=(UI.PADDING_SMALL, 0))
        
        # 出力先のドラッグ&ドロップ設定
        if TKDND_AVAILABLE and DragDropHandler:
            try:
                self.output_drag_handler = DragDropHandler(
                    output_frame,
                    self._on_output_directory_dropped,
                    lambda path: path.is_dir()  # ディレクトリのみ受け付ける
                )
            except Exception as e:
                print(f"出力先ドラッグ&ドロップの初期化エラー: {e}")
    
    def _create_resize_section(self) -> None:
        """リサイズ設定セクション"""
        resize_frame = UIBuilder.create_frame_with_title(
            self.scroll_frame, "リサイズ設定", "📐"
        )
        resize_frame.pack(fill="x", padx=UI.PADDING_LARGE, pady=UI.PADDING_MEDIUM)
        
        # リサイズモード
        mode_frame = ctk.CTkFrame(resize_frame, fg_color="transparent")
        mode_frame.pack(fill="x", pady=(0, UI.PADDING_MEDIUM))
        
        ctk.CTkLabel(
            mode_frame,
            text="リサイズモード:",
            font=ctk.CTkFont(size=FONT.SIZE_NORMAL),
            text_color=THEME.TEXT_PRIMARY
        ).pack(side="left", padx=(0, UI.PADDING_MEDIUM))
        
        self.resize_mode_var = ctk.StringVar(value=ResizeMode.get_display_name(ResizeMode.LONGEST_SIDE))
        self.resize_mode_menu = UIBuilder.create_option_menu(
            mode_frame,
            self.resize_mode_var,
            list(ResizeMode.DISPLAY_NAMES.values()),
            self._on_resize_mode_changed
        )
        self.resize_mode_menu.pack(side="left")
        
        # リサイズ値
        value_frame = ctk.CTkFrame(resize_frame, fg_color="transparent")
        value_frame.pack(fill="x")
        
        ctk.CTkLabel(
            value_frame,
            text="サイズ:",
            font=ctk.CTkFont(size=FONT.SIZE_NORMAL),
            text_color=THEME.TEXT_PRIMARY
        ).pack(side="left", padx=(0, UI.PADDING_MEDIUM))
        
        self.resize_value_entry = ctk.CTkEntry(
            value_frame,
            width=100,
            font=ctk.CTkFont(size=FONT.SIZE_NORMAL),
            height=UI.ENTRY_HEIGHT
        )
        self.resize_value_entry.pack(side="left")
        self.resize_value_entry.bind("<KeyRelease>", self._on_resize_value_changed)
        
        self.resize_unit_label = ctk.CTkLabel(
            value_frame,
            text="px",
            font=ctk.CTkFont(size=FONT.SIZE_NORMAL),
            text_color=THEME.TEXT_SECONDARY
        )
        self.resize_unit_label.pack(side="left", padx=(UI.PADDING_SMALL, 0))
        
        # アスペクト比維持
        self.aspect_ratio_var = ctk.BooleanVar(value=True)
        self.aspect_ratio_check = UIBuilder.create_checkbox(
            resize_frame,
            "アスペクト比を維持",
            self.aspect_ratio_var,
            self._on_aspect_ratio_changed
        )
        self.aspect_ratio_check.pack(anchor="w", pady=(UI.PADDING_MEDIUM, 0))
    
    def _create_quality_section(self) -> None:
        """品質設定セクション"""
        quality_frame = UIBuilder.create_frame_with_title(
            self.scroll_frame, "出力設定", "🎨"
        )
        quality_frame.pack(fill="x", padx=UI.PADDING_LARGE, pady=UI.PADDING_MEDIUM)
        
        # 出力フォーマット
        format_frame = ctk.CTkFrame(quality_frame, fg_color="transparent")
        format_frame.pack(fill="x", pady=(0, UI.PADDING_MEDIUM))
        
        ctk.CTkLabel(
            format_frame,
            text="出力形式:",
            font=ctk.CTkFont(size=FONT.SIZE_NORMAL),
            text_color=THEME.TEXT_PRIMARY
        ).pack(side="left", padx=(0, UI.PADDING_MEDIUM))
        
        self.format_var = ctk.StringVar(value=OutputFormat.get_display_name(OutputFormat.ORIGINAL))
        self.format_menu = UIBuilder.create_option_menu(
            format_frame,
            self.format_var,
            list(OutputFormat.DISPLAY_NAMES.values()),
            self._on_format_changed
        )
        self.format_menu.pack(side="left")
        
        # 品質スライダー
        quality_label = ctk.CTkLabel(
            quality_frame,
            text="品質:",
            font=ctk.CTkFont(size=FONT.SIZE_NORMAL),
            text_color=THEME.TEXT_PRIMARY
        )
        quality_label.pack(anchor="w", pady=(0, UI.PADDING_SMALL))
        
        slider_frame = ctk.CTkFrame(quality_frame, fg_color="transparent")
        slider_frame.pack(fill="x")
        
        self.quality_slider = UIBuilder.create_slider(
            slider_frame,
            from_=1,
            to=100,
            command=self._on_quality_changed
        )
        self.quality_slider.pack(side="left", fill="x", expand=True)
        self.quality_slider.set(85)
        
        self.quality_label = ctk.CTkLabel(
            slider_frame,
            text="85%",
            font=ctk.CTkFont(size=FONT.SIZE_NORMAL),
            text_color=THEME.TEXT_PRIMARY,
            width=50
        )
        self.quality_label.pack(side="left", padx=(UI.PADDING_SMALL, 0))
        
        # WebPロスレス設定（WebP選択時のみ表示）
        self.webp_lossless_var = ctk.BooleanVar(value=False)
        self.webp_lossless_check = UIBuilder.create_checkbox(
            quality_frame,
            "WebPロスレス圧縮",
            self.webp_lossless_var,
            self._on_webp_lossless_changed
        )
        self.webp_lossless_check.pack(anchor="w", pady=(UI.PADDING_MEDIUM, 0))
        # 初期状態では非表示
        self.webp_lossless_check.pack_forget()
        
        # メタデータ設定
        self.metadata_var = ctk.StringVar(value=ExifMode.DISPLAY_NAMES[ExifMode.KEEP])
        metadata_frame = ctk.CTkFrame(quality_frame, fg_color="transparent")
        metadata_frame.pack(fill="x", pady=(UI.PADDING_MEDIUM, 0))
        
        ctk.CTkLabel(
            metadata_frame,
            text="メタデータ:",
            font=ctk.CTkFont(size=FONT.SIZE_NORMAL),
            text_color=THEME.TEXT_PRIMARY
        ).pack(side="left", padx=(0, UI.PADDING_MEDIUM))
        
        for value, display in ExifMode.DISPLAY_NAMES.items():
            radio = UIBuilder.create_radio_button(
                metadata_frame,
                display,
                self.metadata_var,
                display,
                command=self._on_metadata_changed
            )
            radio.pack(side="left", padx=(0, UI.PADDING_MEDIUM))
    
    def _create_filename_section(self) -> None:
        """ファイル名設定セクション"""
        filename_frame = UIBuilder.create_frame_with_title(
            self.scroll_frame, "ファイル名設定", "✏️"
        )
        filename_frame.pack(fill="x", padx=UI.PADDING_LARGE, pady=UI.PADDING_MEDIUM)
        
        # プレフィックス
        prefix_frame = ctk.CTkFrame(filename_frame, fg_color="transparent")
        prefix_frame.pack(fill="x", pady=(0, UI.PADDING_SMALL))
        
        ctk.CTkLabel(
            prefix_frame,
            text="プレフィックス:",
            font=ctk.CTkFont(size=FONT.SIZE_NORMAL),
            text_color=THEME.TEXT_PRIMARY,
            width=100
        ).pack(side="left")
        
        self.prefix_entry = ctk.CTkEntry(
            prefix_frame,
            font=ctk.CTkFont(size=FONT.SIZE_NORMAL),
            height=UI.ENTRY_HEIGHT,
            width=200
        )
        self.prefix_entry.pack(side="left")
        self.prefix_entry.bind("<KeyRelease>", self._on_prefix_changed)
        
        # サフィックス
        suffix_frame = ctk.CTkFrame(filename_frame, fg_color="transparent")
        suffix_frame.pack(fill="x")
        
        ctk.CTkLabel(
            suffix_frame,
            text="サフィックス:",
            font=ctk.CTkFont(size=FONT.SIZE_NORMAL),
            text_color=THEME.TEXT_PRIMARY,
            width=100
        ).pack(side="left")
        
        self.suffix_entry = ctk.CTkEntry(
            suffix_frame,
            font=ctk.CTkFont(size=FONT.SIZE_NORMAL),
            height=UI.ENTRY_HEIGHT,
            width=200
        )
        self.suffix_entry.pack(side="left")
        self.suffix_entry.insert(0, "_resized")
        self.suffix_entry.bind("<KeyRelease>", self._on_suffix_changed)
    
    def _create_action_buttons(self) -> None:
        """アクションボタン"""
        button_frame = ctk.CTkFrame(self.scroll_frame, fg_color="transparent")
        button_frame.pack(fill="x", padx=UI.PADDING_LARGE, pady=UI.PADDING_LARGE)
        
        self.process_button = UIBuilder.create_button(
            button_frame,
            "処理開始",
            self._on_process_clicked,
            variant="primary",
            width=150
        )
        self.process_button.pack(side="left", padx=(0, UI.PADDING_MEDIUM))
        
        self.cancel_button = UIBuilder.create_button(
            button_frame,
            "キャンセル",
            self._on_cancel_clicked,
            variant="danger",
            width=150
        )
        self.cancel_button.pack(side="left")
        self.cancel_button.configure(state="disabled")
    
    def _create_log_section(self) -> None:
        """ログとプログレスバーセクション"""
        log_frame = UIBuilder.create_frame_with_title(
            self.scroll_frame, "処理ログ", "📋"
        )
        log_frame.pack(fill="both", expand=True, padx=UI.PADDING_LARGE, pady=(0, UI.PADDING_LARGE))
        
        # ログテキストボックス
        self.log_textbox = UIBuilder.create_textbox(
            log_frame,
            height=UI.LOG_HEIGHT
        )
        self.log_textbox.pack(fill="both", expand=True, pady=(0, UI.PADDING_SMALL))
        self.log_textbox.configure(state="disabled")
        
        # プログレスバー
        self.progress_bar = UIBuilder.create_progress_bar(log_frame)
        self.progress_bar.pack(fill="x")
        self.progress_bar.set(0)
        
        # ステータスラベル
        self.status_label = ctk.CTkLabel(
            log_frame,
            text="",
            font=ctk.CTkFont(size=FONT.SIZE_SMALL),
            text_color=THEME.TEXT_SECONDARY
        )
        self.status_label.pack(anchor="w", pady=(UI.PADDING_SMALL, 0))
    
    def _setup_bindings(self) -> None:
        """ViewModelとのバインディングを設定"""
        super()._setup_bindings()
        
        # 追加のバインディング
        if self.view_model:
            self._bind_property("processing_mode", self._on_vm_mode_changed)
            self._bind_property("input_path", self._on_vm_input_changed)
            self._bind_property("output_directory", self._on_vm_output_changed)
            self._bind_property("resize_mode", self._on_vm_resize_mode_changed)
            self._bind_property("resize_value", self._on_vm_resize_value_changed)
            self._bind_property("quality", self._on_vm_quality_changed)
            self._bind_property("output_format", self._on_vm_format_changed)
            self._bind_property("webp_lossless", self._on_vm_webp_lossless_changed)
            self._bind_property("processing_completed", self._on_processing_completed)
            self._bind_property("batch_completed", self._on_batch_completed)
            
            # 初期値を設定
            if not self.view_model.is_initialized:
                self.view_model.initialize()
    
    # イベントハンドラ
    def _on_mode_changed(self) -> None:
        """処理モード変更"""
        mode = self.mode_var.get()
        if self.view_model:
            self.view_model.processing_mode = mode
        
        # UIを更新
        if mode == ProcessingMode.SINGLE:
            label_text = "入力ファイル:"
        else:
            label_text = "入力フォルダ:"
        
        if TKDND_AVAILABLE:
            label_text += " (ドラッグ&ドロップ対応)"
        
        self.input_label.configure(text=label_text)
    
    def _browse_input(self) -> None:
        """入力を選択"""
        if self.mode_var.get() == ProcessingMode.SINGLE:
            filename = filedialog.askopenfilename(
                title="入力ファイルを選択",
                filetypes=IMAGE_FILETYPES
            )
            if filename and self.view_model:
                self.view_model.input_path = filename
        else:
            dirname = filedialog.askdirectory(title="入力フォルダを選択")
            if dirname and self.view_model:
                self.view_model.input_path = dirname
    
    def _browse_output(self) -> None:
        """出力先を選択"""
        dirname = filedialog.askdirectory(title="出力先フォルダを選択")
        if dirname and self.view_model:
            self.view_model.output_directory = dirname
    
    def _on_input_changed(self, event) -> None:
        """入力パス変更"""
        if self.view_model:
            self.view_model.input_path = self.input_entry.get()
    
    def _on_output_changed(self, event) -> None:
        """出力パス変更"""
        if self.view_model:
            self.view_model.output_directory = self.output_entry.get()
    
    def _on_resize_mode_changed(self, value: str) -> None:
        """リサイズモード変更"""
        if self.view_model:
            mode = ResizeMode.from_display_name(value)
            self.view_model.resize_mode = mode
            
            # UIを更新
            if mode == ResizeMode.PERCENTAGE:
                self.resize_unit_label.configure(text="%")
            else:
                self.resize_unit_label.configure(text="px")
            
            # リサイズ値の有効/無効を切り替え
            if mode == ResizeMode.NONE:
                self.resize_value_entry.configure(state="disabled")
            else:
                self.resize_value_entry.configure(state="normal")
    
    def _on_resize_value_changed(self, event) -> None:
        """リサイズ値変更"""
        if self.view_model:
            try:
                value = int(self.resize_value_entry.get())
                self.view_model.resize_value = value
            except ValueError:
                pass
    
    def _on_aspect_ratio_changed(self) -> None:
        """アスペクト比設定変更"""
        if self.view_model:
            self.view_model.maintain_aspect_ratio = self.aspect_ratio_var.get()
    
    def _on_format_changed(self, value: str) -> None:
        """出力フォーマット変更"""
        if self.view_model:
            fmt = OutputFormat.from_display_name(value)
            self.view_model.output_format = fmt
            
            # 品質スライダーの有効/無効を切り替え
            if fmt in [OutputFormat.JPEG, OutputFormat.WEBP]:
                self.quality_slider.configure(state="normal")
            else:
                self.quality_slider.configure(state="disabled")
            
            # WebPロスレスチェックボックスの表示/非表示
            if fmt == OutputFormat.WEBP:
                self.webp_lossless_check.pack(anchor="w", pady=(UI.PADDING_MEDIUM, 0))
            else:
                self.webp_lossless_check.pack_forget()
    
    def _on_quality_changed(self, value: float) -> None:
        """品質変更"""
        if self.view_model:
            self.view_model.quality = int(value)
        self.quality_label.configure(text=f"{int(value)}%")
    
    def _on_metadata_changed(self) -> None:
        """メタデータ設定変更"""
        if self.view_model:
            value = self.metadata_var.get()
            self.view_model.preserve_metadata = (value == ExifMode.DISPLAY_NAMES[ExifMode.KEEP])
    
    def _on_webp_lossless_changed(self) -> None:
        """WebPロスレス設定変更"""
        if self.view_model:
            self.view_model.webp_lossless = self.webp_lossless_var.get()
            # ロスレスの場合は品質スライダーを無効化
            if self.webp_lossless_var.get():
                self.quality_slider.configure(state="disabled")
                self.quality_label.configure(text="ロスレス")
            else:
                self.quality_slider.configure(state="normal")
                self.quality_label.configure(text=f"{int(self.quality_slider.get())}%")
    
    def _on_prefix_changed(self, event) -> None:
        """プレフィックス変更"""
        if self.view_model:
            self.view_model.prefix = self.prefix_entry.get()
    
    def _on_suffix_changed(self, event) -> None:
        """サフィックス変更"""
        if self.view_model:
            self.view_model.suffix = self.suffix_entry.get()
    
    def _on_process_clicked(self) -> None:
        """処理開始ボタンクリック"""
        if self.view_model and self.view_model.validate():
            self.view_model.start_processing()
    
    def _on_cancel_clicked(self) -> None:
        """キャンセルボタンクリック"""
        if self.view_model:
            self.view_model.cancel_processing()
    
    # ViewModelからの通知
    def _on_busy_changed(self, is_busy: bool) -> None:
        """処理中状態変更"""
        if is_busy:
            self.process_button.configure(state="disabled")
            self.cancel_button.configure(state="normal")
            # 入力UIを無効化
            self.browse_input_btn.configure(state="disabled")
            self.browse_output_btn.configure(state="disabled")
        else:
            self.process_button.configure(state="normal")
            self.cancel_button.configure(state="disabled")
            # 入力UIを有効化
            self.browse_input_btn.configure(state="normal")
            self.browse_output_btn.configure(state="normal")
    
    def _on_error_changed(self, error_message: str) -> None:
        """エラーメッセージ変更"""
        if error_message:
            self.show_error_dialog("エラー", error_message)
    
    def _on_status_changed(self, status_message: str) -> None:
        """ステータスメッセージ変更"""
        self.status_label.configure(text=status_message)
    
    def _on_progress_changed(self, progress: float) -> None:
        """進捗変更"""
        self.progress_bar.set(progress)
    
    def _on_log_message(self, log_entry: dict) -> None:
        """ログメッセージ追加"""
        timestamp = log_entry.get("timestamp", "")
        level = log_entry.get("level", "info")
        message = log_entry.get("message", "")
        
        # ログに追加
        self.log_textbox.configure(state="normal")
        self.log_textbox.insert("end", f"[{timestamp}] {message}\n")
        self.log_textbox.see("end")
        self.log_textbox.configure(state="disabled")
    
    def _on_vm_mode_changed(self, mode: str) -> None:
        """ViewModelの処理モード変更"""
        self.mode_var.set(mode)
        self._on_mode_changed()
    
    def _on_vm_input_changed(self, path: str) -> None:
        """ViewModelの入力パス変更"""
        self.input_entry.delete(0, "end")
        self.input_entry.insert(0, path)
    
    def _on_vm_output_changed(self, path: str) -> None:
        """ViewModelの出力パス変更"""
        self.output_entry.delete(0, "end")
        self.output_entry.insert(0, path)
    
    def _on_vm_resize_mode_changed(self, mode: str) -> None:
        """ViewModelのリサイズモード変更"""
        display_name = ResizeMode.get_display_name(mode)
        self.resize_mode_var.set(display_name)
        self._on_resize_mode_changed(display_name)
    
    def _on_vm_resize_value_changed(self, value: int) -> None:
        """ViewModelのリサイズ値変更"""
        self.resize_value_entry.delete(0, "end")
        self.resize_value_entry.insert(0, str(value))
    
    def _on_vm_quality_changed(self, quality: int) -> None:
        """ViewModelの品質変更"""
        self.quality_slider.set(quality)
        self.quality_label.configure(text=f"{quality}%")
    
    def _on_vm_format_changed(self, fmt: str) -> None:
        """ViewModelの出力フォーマット変更"""
        display_name = OutputFormat.get_display_name(fmt)
        self.format_var.set(display_name)
        self._on_format_changed(display_name)
    
    def _on_vm_webp_lossless_changed(self, value: bool) -> None:
        """ViewModelのWebPロスレス設定変更"""
        self.webp_lossless_var.set(value)
        # UIも更新
        if value:
            self.quality_slider.configure(state="disabled")
            self.quality_label.configure(text="ロスレス")
        else:
            self.quality_slider.configure(state="normal")
            self.quality_label.configure(text=f"{int(self.quality_slider.get())}%")
    
    def _on_processing_completed(self, result) -> None:
        """処理完了"""
        if result.success:
            self.show_info_dialog("完了", "画像処理が完了しました")
    
    def _on_batch_completed(self, results) -> None:
        """バッチ処理完了"""
        success_count = sum(1 for r in results if r.success)
        total_count = len(results)
        self.show_info_dialog(
            "バッチ処理完了",
            f"処理が完了しました\n成功: {success_count}/{total_count}件"
        )
    
    # ドラッグ&ドロップ関連メソッド
    def _filter_valid_files(self, path: Path) -> bool:
        """有効なファイルかどうかをフィルター"""
        # 処理モードに応じて判定
        if self.mode_var.get() == ProcessingMode.SINGLE:
            # 単一ファイルモード: 画像ファイルのみ
            image_extensions = {'.jpg', '.jpeg', '.png', '.webp', '.bmp', '.gif', '.tiff', '.tif'}
            return path.is_file() and path.suffix.lower() in image_extensions
        else:
            # バッチモード: ディレクトリまたは画像ファイル
            if path.is_dir():
                return True
            image_extensions = {'.jpg', '.jpeg', '.png', '.webp', '.bmp', '.gif', '.tiff', '.tif'}
            return path.is_file() and path.suffix.lower() in image_extensions
    
    def _on_files_dropped(self, files: list[Path]) -> None:
        """ファイルがドロップされた時の処理"""
        if not self.view_model or not files:
            return
        
        mode = self.mode_var.get()
        
        if mode == ProcessingMode.SINGLE:
            # 単一ファイルモード: 最初の画像ファイルのみ使用
            for file in files:
                if file.is_file() and self._filter_valid_files(file):
                    self.view_model.input_path = str(file)
                    # 出力ディレクトリが空の場合は同じディレクトリを設定
                    if not self.view_model.output_directory:
                        self.view_model.output_directory = str(file.parent)
                    break
            else:
                self.show_error_dialog("エラー", "有効な画像ファイルがドロップされませんでした")
        else:
            # バッチモード
            if len(files) == 1 and files[0].is_dir():
                # ディレクトリがドロップされた場合
                self.view_model.input_path = str(files[0])
                # 出力ディレクトリが空の場合は同じディレクトリを設定
                if not self.view_model.output_directory:
                    self.view_model.output_directory = str(files[0])
            else:
                # 複数ファイルがドロップされた場合
                # 最初のファイルの親ディレクトリを設定
                valid_files = [f for f in files if self._filter_valid_files(f)]
                if valid_files:
                    parent_dir = valid_files[0].parent
                    self.view_model.input_path = str(parent_dir)
                    # 出力ディレクトリが空の場合は同じディレクトリを設定
                    if not self.view_model.output_directory:
                        self.view_model.output_directory = str(parent_dir)
                else:
                    self.show_error_dialog("エラー", "有効な画像ファイルがドロップされませんでした")
    
    def _on_output_directory_dropped(self, items: list[Path]) -> None:
        """出力ディレクトリがドロップされた時の処理"""
        if not self.view_model or not items:
            return
        
        # 最初のディレクトリを使用
        for item in items:
            if item.is_dir():
                self.view_model.output_directory = str(item)
                break
        else:
            self.show_error_dialog("エラー", "有効なフォルダがドロップされませんでした")