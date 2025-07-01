"""
プレビュータブのView
"""
import customtkinter as ctk
from pathlib import Path
from typing import Optional
from PIL import Image, ImageTk
import sys

# プロジェクトルートをPythonパスに追加
project_root = Path(__file__).parent.parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from .base_view import BaseView
from ..view_models.preview_view_model import PreviewViewModel
from ..utils.ui_builders import UIBuilder
from ..utils.constants import FONT, THEME, UI
from image_preview import ComparisonPreviewWidget, ImageInfo


class PreviewTabView(BaseView):
    """プレビュータブのView"""
    
    def __init__(self, parent, view_model: Optional[PreviewViewModel] = None, resize_view_model=None):
        # ViewModelがない場合は作成
        if view_model is None:
            view_model = PreviewViewModel()
        
        # リサイズViewModelへの参照を保持（設定の同期用）
        self.resize_view_model = resize_view_model
        
        super().__init__(parent, view_model)
        
    def _create_widgets(self) -> None:
        """ウィジェットを作成"""
        # メインコンテナ
        self.main_container = ctk.CTkFrame(self, fg_color="transparent")
        
        # ツールバー
        self._create_toolbar()
        
        # 比較プレビューウィジェット
        self.comparison_widget = ComparisonPreviewWidget(self.main_container)
        
        # 情報パネル
        self._create_info_panel()
        
    def _layout_widgets(self) -> None:
        """ウィジェットを配置"""
        self.main_container.pack(fill="both", expand=True)
        
        # ツールバー
        self.toolbar.pack(fill="x", padx=UI.PADDING_MEDIUM, pady=(UI.PADDING_MEDIUM, 0))
        
        # 比較プレビューウィジェット
        self.comparison_widget.pack(
            fill="both", 
            expand=True, 
            padx=UI.PADDING_MEDIUM, 
            pady=UI.PADDING_MEDIUM
        )
        
        # 情報パネル
        self.info_panel.pack(
            fill="x", 
            padx=UI.PADDING_MEDIUM, 
            pady=(0, UI.PADDING_MEDIUM)
        )
    
    def _create_toolbar(self) -> None:
        """ツールバーを作成"""
        self.toolbar = ctk.CTkFrame(
            self.main_container,
            height=40,
            corner_radius=UI.CORNER_RADIUS,
            border_width=UI.BORDER_WIDTH,
            border_color=THEME.BORDER_COLOR
        )
        
        # 左側のコントロール
        left_frame = ctk.CTkFrame(self.toolbar, fg_color="transparent")
        left_frame.pack(side="left", padx=UI.PADDING_MEDIUM, pady=UI.PADDING_SMALL)
        
        # ズームコントロール
        self.zoom_out_btn = UIBuilder.create_button(
            left_frame,
            "−",
            self._on_zoom_out,
            variant="secondary",
            width=30
        )
        self.zoom_out_btn.pack(side="left", padx=(0, UI.PADDING_SMALL))
        
        self.zoom_label = ctk.CTkLabel(
            left_frame,
            text="100%",
            font=ctk.CTkFont(size=FONT.SIZE_NORMAL),
            text_color=THEME.TEXT_PRIMARY,
            width=60
        )
        self.zoom_label.pack(side="left", padx=UI.PADDING_SMALL)
        
        self.zoom_in_btn = UIBuilder.create_button(
            left_frame,
            "＋",
            self._on_zoom_in,
            variant="secondary",
            width=30
        )
        self.zoom_in_btn.pack(side="left", padx=(UI.PADDING_SMALL, 0))
        
        # セパレーター
        sep = ctk.CTkFrame(left_frame, width=1, height=20, fg_color=THEME.BORDER_COLOR)
        sep.pack(side="left", padx=UI.PADDING_MEDIUM)
        
        # リセットボタン
        self.reset_zoom_btn = UIBuilder.create_button(
            left_frame,
            "画面に合わせる",
            self._on_fit_to_window,
            variant="secondary",
            width=120
        )
        self.reset_zoom_btn.pack(side="left")
        
        # 右側のコントロール
        right_frame = ctk.CTkFrame(self.toolbar, fg_color="transparent")
        right_frame.pack(side="right", padx=UI.PADDING_MEDIUM, pady=UI.PADDING_SMALL)
        
        # プレビュー更新ボタン
        self.update_preview_btn = UIBuilder.create_button(
            right_frame,
            "プレビュー更新",
            self._on_update_preview,
            variant="primary",
            width=120
        )
        self.update_preview_btn.pack(side="right")
        
        # 自動更新チェックボックス
        self.auto_update_var = ctk.BooleanVar(value=True)
        self.auto_update_check = UIBuilder.create_checkbox(
            right_frame,
            "自動更新",
            self.auto_update_var,
            self._on_auto_update_changed
        )
        self.auto_update_check.pack(side="right", padx=(0, UI.PADDING_MEDIUM))
    
    def _create_info_panel(self) -> None:
        """情報パネルを作成"""
        self.info_panel = ctk.CTkFrame(
            self.main_container,
            height=60,
            corner_radius=UI.CORNER_RADIUS,
            border_width=UI.BORDER_WIDTH,
            border_color=THEME.BORDER_COLOR
        )
        
        # 元画像情報
        before_frame = ctk.CTkFrame(self.info_panel, fg_color="transparent")
        before_frame.pack(side="left", fill="x", expand=True, padx=UI.PADDING_MEDIUM)
        
        before_title = ctk.CTkLabel(
            before_frame,
            text="元画像",
            font=ctk.CTkFont(size=FONT.SIZE_NORMAL, weight=FONT.WEIGHT_BOLD),
            text_color=THEME.TEXT_PRIMARY
        )
        before_title.pack(anchor="w")
        
        self.before_info_label = ctk.CTkLabel(
            before_frame,
            text="画像が選択されていません",
            font=ctk.CTkFont(size=FONT.SIZE_SMALL),
            text_color=THEME.TEXT_SECONDARY
        )
        self.before_info_label.pack(anchor="w")
        
        # セパレーター
        sep = ctk.CTkFrame(self.info_panel, width=1, height=40, fg_color=THEME.BORDER_COLOR)
        sep.pack(side="left", padx=UI.PADDING_MEDIUM)
        
        # 処理後画像情報
        after_frame = ctk.CTkFrame(self.info_panel, fg_color="transparent")
        after_frame.pack(side="left", fill="x", expand=True, padx=UI.PADDING_MEDIUM)
        
        after_title = ctk.CTkLabel(
            after_frame,
            text="処理後（予測）",
            font=ctk.CTkFont(size=FONT.SIZE_NORMAL, weight=FONT.WEIGHT_BOLD),
            text_color=THEME.TEXT_PRIMARY
        )
        after_title.pack(anchor="w")
        
        self.after_info_label = ctk.CTkLabel(
            after_frame,
            text="プレビューが生成されていません",
            font=ctk.CTkFont(size=FONT.SIZE_SMALL),
            text_color=THEME.TEXT_SECONDARY
        )
        self.after_info_label.pack(anchor="w")
        
        # サイズ削減情報
        reduction_frame = ctk.CTkFrame(self.info_panel, fg_color="transparent")
        reduction_frame.pack(side="right", padx=UI.PADDING_MEDIUM)
        
        self.reduction_label = ctk.CTkLabel(
            reduction_frame,
            text="",
            font=ctk.CTkFont(size=FONT.SIZE_HEADING, weight=FONT.WEIGHT_BOLD),
            text_color=THEME.SUCCESS
        )
        self.reduction_label.pack()
    
    def _setup_bindings(self) -> None:
        """ViewModelとのバインディングを設定"""
        super()._setup_bindings()
        
        if self.view_model:
            # 追加のバインディング
            self._bind_property("source_image_loaded", self._on_source_image_loaded)
            self._bind_property("preview_generated", self._on_preview_generated)
            self._bind_property("zoom_level", self._on_zoom_changed)
            self._bind_property("is_generating_preview", self._on_generating_preview_changed)
            self._bind_property("fit_to_window_requested", self._on_fit_to_window_requested)
            
            # 初期化
            if not self.view_model.is_initialized:
                self.view_model.initialize()
        
        # リサイズViewModelのバインディング（設定変更の監視）
        if self.resize_view_model:
            self.resize_view_model.bind("input_path", self._on_resize_input_changed)
            # 設定変更時の自動更新
            for prop in ["resize_mode", "resize_value", "quality", "output_format"]:
                self.resize_view_model.bind(prop, lambda _: self._on_settings_changed())
    
    # イベントハンドラ
    def _on_zoom_in(self) -> None:
        """ズームイン"""
        if self.view_model:
            self.view_model.zoom_in()
    
    def _on_zoom_out(self) -> None:
        """ズームアウト"""
        if self.view_model:
            self.view_model.zoom_out()
    
    def _on_fit_to_window(self) -> None:
        """ウィンドウに合わせる"""
        if self.view_model:
            self.view_model.fit_to_window()
    
    def _on_update_preview(self) -> None:
        """プレビュー更新"""
        self._generate_preview()
    
    def _on_auto_update_changed(self) -> None:
        """自動更新設定変更"""
        if self.auto_update_var.get():
            self._generate_preview()
    
    def _generate_preview(self) -> None:
        """プレビューを生成"""
        if not self.view_model or not self.resize_view_model:
            return
        
        # 現在の設定を取得
        settings = self.resize_view_model._get_current_settings()
        
        # プレビューを生成
        self.view_model.generate_preview(settings)
    
    # ViewModelからの通知
    def _on_resize_input_changed(self, path: str) -> None:
        """リサイズ入力パス変更"""
        if self.view_model and path and Path(path).exists() and Path(path).is_file():
            self.view_model.source_image_path = path
    
    def _on_settings_changed(self) -> None:
        """設定変更"""
        if self.auto_update_var.get():
            self._generate_preview()
    
    def _on_source_image_loaded(self, image: Image.Image) -> None:
        """ソース画像読み込み完了"""
        if not self.view_model:
            return
        
        # 比較ウィジェットに画像を設定
        info = self.view_model.source_image_info
        image_info = ImageInfo(
            path=Path(info.get("path", "")),
            size=info.get("size", (0, 0)),
            file_size=info.get("file_size", 0),
            format=info.get("format", ""),
            mode=info.get("mode", ""),
            has_exif=info.get("has_exif", False)
        )
        
        self.comparison_widget.set_before_image(image, image_info)
        
        # 情報を更新
        self.before_info_label.configure(
            text=f"{image_info.size_text} • {image_info.file_size_text} • {image_info.format}"
        )
        
        # 自動プレビュー生成
        if self.auto_update_var.get():
            self._generate_preview()
    
    def _on_preview_generated(self, image: Image.Image) -> None:
        """プレビュー生成完了"""
        if not self.view_model:
            return
        
        # 比較ウィジェットに画像を設定
        info = self.view_model.preview_image_info
        settings = info.get("settings", {})
        
        # 疑似的なImageInfoを作成（実際のファイルではないため）
        image_info = ImageInfo(
            path=Path("preview"),
            size=info.get("size", (0, 0)),
            file_size=info.get("estimated_file_size", 0),
            format=info.get("format", ""),
            mode=info.get("mode", ""),
            has_exif=settings.get("preserve_metadata", False)
        )
        
        self.comparison_widget.set_after_image(image, image_info)
        
        # 情報を更新
        self.after_info_label.configure(
            text=f"{image_info.size_text} • {image_info.file_size_text} • {image_info.format}"
        )
        
        # サイズ削減情報を更新
        reduction_info = self.view_model.get_size_reduction_info()
        if reduction_info:
            percent = reduction_info.get("reduction_percent", 0)
            if percent > 0:
                self.reduction_label.configure(
                    text=f"▼ {percent:.1f}%",
                    text_color=THEME.SUCCESS
                )
            else:
                self.reduction_label.configure(
                    text=f"▲ {abs(percent):.1f}%",
                    text_color=THEME.ERROR
                )
    
    def _on_zoom_changed(self, zoom_level: float) -> None:
        """ズームレベル変更"""
        self.zoom_label.configure(text=f"{int(zoom_level * 100)}%")
        
        # 比較ウィジェットのズームを更新
        if hasattr(self.comparison_widget, 'set_zoom_level'):
            self.comparison_widget.set_zoom_level(zoom_level)
    
    def _on_generating_preview_changed(self, is_generating: bool) -> None:
        """プレビュー生成状態変更"""
        if is_generating:
            self.update_preview_btn.configure(state="disabled", text="生成中...")
        else:
            self.update_preview_btn.configure(state="normal", text="プレビュー更新")
    
    def _on_fit_to_window_requested(self, _) -> None:
        """ウィンドウに合わせるリクエスト"""
        # 比較ウィジェットからウィンドウサイズを取得して適切なズームを設定
        if hasattr(self.comparison_widget, 'get_fit_zoom_level'):
            zoom = self.comparison_widget.get_fit_zoom_level()
            if self.view_model:
                self.view_model.zoom_level = zoom
    
    def _on_busy_changed(self, is_busy: bool) -> None:
        """処理中状態変更"""
        # プレビュータブでは特に何もしない
        pass
    
    def _on_error_changed(self, error_message: str) -> None:
        """エラーメッセージ変更"""
        if error_message:
            # エラーを情報パネルに表示
            self.after_info_label.configure(
                text=f"エラー: {error_message}",
                text_color=THEME.ERROR
            )