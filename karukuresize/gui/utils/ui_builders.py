"""
UI構築のヘルパー関数
"""
import customtkinter as ctk
from typing import Optional, Tuple, Callable, Any
from .constants import FONT, THEME, UI


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
        label.grid(row=0, column=0, padx=(0, UI.PADDING_MEDIUM), sticky="w")
        
        entry = ctk.CTkEntry(
            frame,
            width=entry_width,
            height=UI.ENTRY_HEIGHT,
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
        width: Optional[int] = None,
        **kwargs
    ) -> ctk.CTkButton:
        """統一されたスタイルのボタンを作成"""
        # バリアントに応じた色設定
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
        elif variant == "success":
            fg_color = THEME.SUCCESS
            hover_color = "#218838"
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
            height=UI.BUTTON_HEIGHT,
            corner_radius=UI.CORNER_RADIUS,
            width=width,
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
            corner_radius=UI.CORNER_RADIUS,
            border_width=UI.BORDER_WIDTH,
            border_color=THEME.BORDER_COLOR
        )
        
        title_text = f"{icon} {title}" if icon else title
        title_label = ctk.CTkLabel(
            frame,
            text=title_text,
            font=ctk.CTkFont(size=FONT.SIZE_HEADING, weight=FONT.WEIGHT_BOLD),
            text_color=THEME.TEXT_PRIMARY
        )
        title_label.pack(anchor="w", padx=UI.PADDING_LARGE, pady=(UI.PADDING_MEDIUM, UI.PADDING_SMALL))
        
        content_frame = ctk.CTkFrame(frame, fg_color="transparent")
        content_frame.pack(fill="both", expand=True, padx=UI.PADDING_LARGE, pady=(0, UI.PADDING_LARGE))
        
        return content_frame
    
    @staticmethod
    def create_option_menu(
        parent: ctk.CTkFrame,
        variable: ctk.StringVar,
        values: list,
        command: Optional[Callable] = None,
        width: int = 200,
        **kwargs
    ) -> ctk.CTkOptionMenu:
        """オプションメニューを作成"""
        option_menu = ctk.CTkOptionMenu(
            parent,
            variable=variable,
            values=values,
            command=command,
            width=width,
            height=UI.BUTTON_HEIGHT,
            font=ctk.CTkFont(size=FONT.SIZE_NORMAL),
            dropdown_font=ctk.CTkFont(size=FONT.SIZE_NORMAL),
            corner_radius=UI.CORNER_RADIUS,
            **kwargs
        )
        return option_menu
    
    @staticmethod
    def create_slider(
        parent: ctk.CTkFrame,
        from_: float,
        to: float,
        command: Optional[Callable] = None,
        **kwargs
    ) -> ctk.CTkSlider:
        """スライダーを作成"""
        slider = ctk.CTkSlider(
            parent,
            from_=from_,
            to=to,
            command=command,
            button_color=THEME.ACCENT,
            button_hover_color=THEME.ACCENT_HOVER,
            progress_color=THEME.ACCENT,
            **kwargs
        )
        return slider
    
    @staticmethod
    def create_radio_button(
        parent: ctk.CTkFrame,
        text: str,
        variable: Any,
        value: Any,
        command: Optional[Callable] = None,
        **kwargs
    ) -> ctk.CTkRadioButton:
        """ラジオボタンを作成"""
        radio = ctk.CTkRadioButton(
            parent,
            text=text,
            variable=variable,
            value=value,
            command=command,
            font=ctk.CTkFont(size=FONT.SIZE_NORMAL),
            text_color=THEME.TEXT_PRIMARY,
            fg_color=THEME.ACCENT,
            hover_color=THEME.ACCENT_HOVER,
            **kwargs
        )
        return radio
    
    @staticmethod
    def create_checkbox(
        parent: ctk.CTkFrame,
        text: str,
        variable: Optional[Any] = None,
        command: Optional[Callable] = None,
        **kwargs
    ) -> ctk.CTkCheckBox:
        """チェックボックスを作成"""
        checkbox = ctk.CTkCheckBox(
            parent,
            text=text,
            variable=variable,
            command=command,
            font=ctk.CTkFont(size=FONT.SIZE_NORMAL),
            text_color=THEME.TEXT_PRIMARY,
            fg_color=THEME.ACCENT,
            hover_color=THEME.ACCENT_HOVER,
            corner_radius=4,
            **kwargs
        )
        return checkbox
    
    @staticmethod
    def create_textbox(
        parent: ctk.CTkFrame,
        height: int = 100,
        **kwargs
    ) -> ctk.CTkTextbox:
        """テキストボックスを作成"""
        textbox = ctk.CTkTextbox(
            parent,
            height=height,
            corner_radius=UI.CORNER_RADIUS,
            border_width=UI.BORDER_WIDTH,
            border_color=THEME.BORDER_COLOR,
            font=ctk.CTkFont(size=FONT.SIZE_NORMAL),
            **kwargs
        )
        return textbox
    
    @staticmethod
    def create_progress_bar(
        parent: ctk.CTkFrame,
        **kwargs
    ) -> ctk.CTkProgressBar:
        """プログレスバーを作成"""
        progress_bar = ctk.CTkProgressBar(
            parent,
            corner_radius=UI.CORNER_RADIUS,
            height=UI.PROGRESS_BAR_HEIGHT,
            progress_color=THEME.ACCENT,
            **kwargs
        )
        return progress_bar
    
    @staticmethod
    def create_separator(
        parent: ctk.CTkFrame,
        orientation: str = "horizontal"
    ) -> ctk.CTkFrame:
        """セパレーターを作成"""
        if orientation == "horizontal":
            separator = ctk.CTkFrame(parent, height=1, fg_color=THEME.BORDER_COLOR)
            separator.pack(fill="x", pady=UI.PADDING_MEDIUM)
        else:
            separator = ctk.CTkFrame(parent, width=1, fg_color=THEME.BORDER_COLOR)
            separator.pack(fill="y", padx=UI.PADDING_MEDIUM)
        
        return separator