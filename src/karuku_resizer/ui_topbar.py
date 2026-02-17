"""Top bar UI builder for the main GUI."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Dict

import customtkinter


TOPBAR_DENSITY_COMPACT_MAX_WIDTH = 1310
TOPBAR_WIDTHS: Dict[str, Dict[str, int]] = {
    "normal": {
        "select": 128,
        "help": 108,
        "settings": 90,
        "preset_menu": 180,
        "preset_action": 72,
        "preview": 118,
        "save": 118,
        "batch": 118,
        "zoom": 140,
    },
    "compact": {
        "select": 118,
        "help": 94,
        "settings": 82,
        "preset_menu": 156,
        "preset_action": 64,
        "preview": 108,
        "save": 96,
        "batch": 106,
        "zoom": 126,
    },
}


@dataclass
class TopBarWidgets:
    """Widget container created for top bar."""

    top_container: customtkinter.CTkFrame
    top_guide_frame: customtkinter.CTkFrame
    top_action_guide_var: customtkinter.StringVar
    top_action_guide_label: customtkinter.CTkLabel
    top_row_primary: customtkinter.CTkFrame
    select_button: customtkinter.CTkButton
    help_button: customtkinter.CTkButton
    settings_button: customtkinter.CTkButton
    preset_manage_button: customtkinter.CTkButton
    preset_menu: customtkinter.CTkOptionMenu
    preset_caption_label: customtkinter.CTkLabel
    preview_button: customtkinter.CTkButton
    save_button: customtkinter.CTkButton
    batch_button: customtkinter.CTkButton
    zoom_cb: customtkinter.CTkComboBox


class TopBarController:
    """Build and update top bar widgets with injected handlers."""

    def __init__(
        self,
        *,
        on_select: Callable[[], None],
        on_help: Callable[[], None],
        on_settings: Callable[[], None],
        on_preset_manage: Callable[[], None],
        on_preset_changed: Callable[[str], None],
        on_preview: Callable[[], None],
        on_save: Callable[[], None],
        on_batch: Callable[[], None],
        on_zoom_changed: Callable[[str], None],
        scale_px: Callable[[int], int],
        scale_topbar_widths: Callable[[str], Dict[str, int]],
        style_primary_button: Callable[[Any], None],
        style_secondary_button: Callable[[Any], None],
        style_card_frame: Callable[[Any], None],
        font_default: Any,
        font_small: Any,
        colors: Dict[str, Any],
        get_topbar_density: Callable[[], str],
        set_topbar_density: Callable[[str], None],
        select_button_text: Callable[[], str],
        icon_folder: Any,
        icon_circle_help: Any,
        icon_settings: Any,
        icon_refresh: Any,
        icon_save: Any,
        icon_folder_open: Any,
        preset_var: customtkinter.StringVar,
        zoom_var: customtkinter.StringVar,
    ) -> None:
        self._on_select = on_select
        self._on_help = on_help
        self._on_settings = on_settings
        self._on_preset_manage = on_preset_manage
        self._on_preset_changed = on_preset_changed
        self._on_preview = on_preview
        self._on_save = on_save
        self._on_batch = on_batch
        self._on_zoom_changed = on_zoom_changed
        self._scale_px = scale_px
        self._scale_topbar_widths = scale_topbar_widths
        self._style_primary_button = style_primary_button
        self._style_secondary_button = style_secondary_button
        self._style_card_frame = style_card_frame
        self._font_default = font_default
        self._font_small = font_small
        self._colors = colors
        self._get_topbar_density = get_topbar_density
        self._set_topbar_density = set_topbar_density
        self._select_button_text = select_button_text
        self._icon_folder = icon_folder
        self._icon_circle_help = icon_circle_help
        self._icon_settings = icon_settings
        self._icon_refresh = icon_refresh
        self._icon_save = icon_save
        self._icon_folder_open = icon_folder_open
        self._preset_var = preset_var
        self._zoom_var = zoom_var
        self._widgets: TopBarWidgets | None = None

    @staticmethod
    def _density_for_width(window_width: int) -> str:
        return "compact" if window_width <= TOPBAR_DENSITY_COMPACT_MAX_WIDTH else "normal"

    @staticmethod
    def _batch_button_text_for_density(density: str) -> str:
        return "一括保存" if density == "compact" else "一括適用保存"

    def build(self, parent: Any, setup_entry_widgets: Callable[[Any], None]) -> TopBarWidgets:
        """Build top bar widgets."""
        top_container = customtkinter.CTkFrame(parent)
        self._style_card_frame(top_container)
        top_container.pack(
            side="top",
            fill="x",
            padx=self._scale_px(10),
            pady=(self._scale_px(1), self._scale_px(2)),
        )

        top_guide_frame = customtkinter.CTkFrame(top_container, fg_color="transparent")
        top_guide_frame.pack(
            side="top",
            fill="x",
            padx=self._scale_px(8),
            pady=(self._scale_px(1), self._scale_px(1)),
        )
        top_action_guide_var = customtkinter.StringVar(value="")
        top_action_guide_label = customtkinter.CTkLabel(
            top_guide_frame,
            textvariable=top_action_guide_var,
            anchor="w",
            justify="left",
            font=self._font_small,
            text_color=self._colors["text_secondary"],
            fg_color=self._colors["bg_secondary"],
            corner_radius=10,
            padx=self._scale_px(10),
        )
        top_action_guide_label.pack(fill="x", padx=(0, 0), pady=(0, 0))

        top_row_primary = customtkinter.CTkFrame(top_container, fg_color="transparent")
        top_row_primary.pack(
            side="top",
            fill="x",
            padx=self._scale_px(8),
            pady=(0, self._scale_px(0)),
        )
        topbar_widths = self._scale_topbar_widths("normal")

        select_button = customtkinter.CTkButton(
            top_row_primary,
            text="画像を選択",
            image=self._icon_folder,
            compound="left",
            width=topbar_widths["select"],
            command=self._on_select,
            font=self._font_default,
        )
        self._style_primary_button(select_button)
        select_button.pack(side="left", padx=(0, self._scale_px(6)), pady=self._scale_px(1))

        size_controls_frame = customtkinter.CTkFrame(top_row_primary, fg_color="transparent")
        size_controls_frame.pack(side="left", padx=(0, self._scale_px(8)))
        setup_entry_widgets(size_controls_frame)

        settings_button = customtkinter.CTkButton(
            top_row_primary,
            text="設定",
            image=self._icon_settings,
            compound="left",
            width=topbar_widths["settings"],
            command=self._on_settings,
            font=self._font_default,
        )
        self._style_secondary_button(settings_button)
        settings_button.pack(
            side="right",
            padx=(self._scale_px(4), 0),
            pady=self._scale_px(1),
        )
        help_button = customtkinter.CTkButton(
            top_row_primary,
            text="使い方",
            image=self._icon_circle_help,
            compound="left",
            width=topbar_widths["help"],
            command=self._on_help,
            font=self._font_default,
        )
        self._style_secondary_button(help_button)

        preset_manage_button = customtkinter.CTkButton(
            top_row_primary,
            text="管理",
            width=topbar_widths["preset_action"],
            command=self._on_preset_manage,
            font=self._font_small,
        )
        self._style_secondary_button(preset_manage_button)
        preset_menu = customtkinter.CTkOptionMenu(
            top_row_primary,
            variable=self._preset_var,
            values=[self._preset_var.get()],
            width=topbar_widths["preset_menu"],
            command=self._on_preset_changed,
            font=self._font_small,
            fg_color=self._colors["bg_tertiary"],
            button_color=self._colors["primary"],
            button_hover_color=self._colors["hover"],
            text_color=self._colors["text_primary"],
            dropdown_fg_color=self._colors["bg_secondary"],
            dropdown_text_color=self._colors["text_primary"],
        )
        preset_menu.pack(side="right", padx=(self._scale_px(4), 0), pady=self._scale_px(1))
        preset_caption_label = customtkinter.CTkLabel(
            top_row_primary,
            text="プリセット",
            font=self._font_small,
            text_color=self._colors["text_secondary"],
        )
        preset_caption_label.pack(side="right", padx=(0, self._scale_px(4)), pady=self._scale_px(1))

        # Mode radio buttons are appended to `mode_radio_buttons` inside `setup_entry_widgets`

        action_controls_frame = customtkinter.CTkFrame(top_row_primary, fg_color="transparent")
        action_controls_frame.pack(side="right")
        preview_button = customtkinter.CTkButton(
            action_controls_frame,
            text="プレビュー",
            image=self._icon_refresh,
            compound="left",
            width=topbar_widths["preview"],
            command=self._on_preview,
            font=self._font_default,
        )
        self._style_primary_button(preview_button)
        preview_button.pack(side="left", padx=(0, self._scale_px(8)), pady=self._scale_px(2))
        save_button = customtkinter.CTkButton(
            action_controls_frame,
            text="保存",
            image=self._icon_save,
            compound="left",
            width=topbar_widths["save"],
            command=self._on_save,
            font=self._font_default,
        )
        self._style_primary_button(save_button)
        save_button.pack(side="left", pady=self._scale_px(2))
        batch_button = customtkinter.CTkButton(
            action_controls_frame,
            image=self._icon_folder_open,
            compound="left",
            text=self._batch_button_text_for_density(self._get_topbar_density()),
            width=topbar_widths["batch"],
            command=self._on_batch,
            font=self._font_default,
        )
        self._style_primary_button(batch_button)
        batch_button.pack(side="left", padx=self._scale_px(8), pady=self._scale_px(2))

        zoom_cb = customtkinter.CTkComboBox(
            action_controls_frame,
            variable=self._zoom_var,
            values=["画面に合わせる", "100%", "200%", "300%"],
            width=topbar_widths["zoom"],
            state="readonly",
            command=self._on_zoom_changed,
            font=self._font_default,
            fg_color=self._colors["bg_tertiary"],
            border_color=self._colors["border_light"],
            button_color=self._colors["primary"],
            button_hover_color=self._colors["hover"],
            text_color=self._colors["text_primary"],
            dropdown_fg_color=self._colors["bg_secondary"],
            dropdown_text_color=self._colors["text_primary"],
        )
        zoom_cb.pack(side="left", padx=(self._scale_px(4), self._scale_px(8)), pady=self._scale_px(2))
        zoom_cb.pack_forget()

        widgets = TopBarWidgets(
            top_container=top_container,
            top_guide_frame=top_guide_frame,
            top_action_guide_var=top_action_guide_var,
            top_action_guide_label=top_action_guide_label,
            top_row_primary=top_row_primary,
            select_button=select_button,
            help_button=help_button,
            settings_button=settings_button,
            preset_manage_button=preset_manage_button,
            preset_menu=preset_menu,
            preset_caption_label=preset_caption_label,
            preview_button=preview_button,
            save_button=save_button,
            batch_button=batch_button,
            zoom_cb=zoom_cb,
        )
        self._widgets = widgets
        return widgets

    def apply_density(self, window_width: int) -> None:
        widgets = self._widgets
        if widgets is None:
            return
        density = self._density_for_width(window_width)
        if density == self._get_topbar_density():
            return
        self._set_topbar_density(density)
        widths = self._scale_topbar_widths(density)
        widgets.select_button.configure(width=widths["select"])
        widgets.help_button.configure(width=widths["help"])
        widgets.settings_button.configure(width=widths["settings"])
        widgets.preset_menu.configure(width=widths["preset_menu"])
        widgets.preset_manage_button.configure(width=widths["preset_action"])
        widgets.preview_button.configure(width=widths["preview"])
        widgets.save_button.configure(width=widths["save"])
        widgets.batch_button.configure(
            width=widths["batch"],
            text=self._batch_button_text_for_density(density),
        )
        widgets.zoom_cb.configure(width=widths["zoom"])
        widgets.select_button.configure(text=self._select_button_text())

    def refresh_top_action_guide(self, text: str) -> None:
        widgets = self._widgets
        if widgets is None:
            return

        widgets.top_action_guide_var.set(text)
        if text:
            if widgets.top_guide_frame.winfo_manager() != "pack":
                widgets.top_guide_frame.pack(
                    side="top",
                    fill="x",
                    padx=self._scale_px(8),
                    pady=(self._scale_px(2), self._scale_px(1)),
                )
            if not widgets.top_action_guide_label.winfo_manager():
                widgets.top_action_guide_label.pack(fill="x", padx=(0, 0), pady=(0, 0))
            return

        if widgets.top_action_guide_label.winfo_manager():
            widgets.top_action_guide_label.pack_forget()
        if widgets.top_guide_frame.winfo_manager():
            widgets.top_guide_frame.pack_forget()

    def apply_ui_mode(self, *, is_pro_mode: bool, is_loading: bool) -> None:
        widgets = self._widgets
        if widgets is None:
            return
        widgets.select_button.configure(text=self._select_button_text())
        if is_loading:
            widgets.select_button.configure(state="disabled")
        elif widgets.select_button.cget("state") != "normal":
            widgets.select_button.configure(state="normal")

        if is_pro_mode:
            if widgets.batch_button.winfo_manager() != "pack":
                widgets.batch_button.pack(
                    side="left",
                    padx=self._scale_px(8),
                    pady=self._scale_px(8),
                )
            if widgets.preset_menu.winfo_manager() != "pack":
                widgets.preset_menu.pack(
                    side="right",
                    padx=(self._scale_px(4), 0),
                    pady=self._scale_px(2),
                )
            if widgets.preset_caption_label.winfo_manager() != "pack":
                widgets.preset_caption_label.pack(
                    side="right",
                    padx=(0, self._scale_px(4)),
                    pady=self._scale_px(2),
                )
            return

        if widgets.batch_button.winfo_manager():
            widgets.batch_button.pack_forget()
        if widgets.preset_menu.winfo_manager():
            widgets.preset_menu.pack_forget()
        if widgets.preset_caption_label.winfo_manager():
            widgets.preset_caption_label.pack_forget()
