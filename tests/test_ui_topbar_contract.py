"""Contract tests for top bar controller wiring."""

from __future__ import annotations

from typing import Any, Callable, Dict

from karuku_resizer.ui_topbar import TopBarController, TopBarWidgets


class _FakeWidget:
    def __init__(self, text: str = "") -> None:
        self.width = 0
        self.text = text
        self.state = "normal"
        self.visible = False
        self.packed_kwargs: dict[str, Any] | None = None
        self.forget_count = 0

    def configure(self, **kwargs: Any) -> None:
        if "width" in kwargs:
            self.width = kwargs["width"]
        if "text" in kwargs:
            self.text = kwargs["text"]
        if "state" in kwargs:
            self.state = kwargs["state"]

    def cget(self, option: str) -> Any:
        if option == "state":
            return self.state
        raise KeyError(option)

    def pack(self, **kwargs: Any) -> None:
        self.visible = True
        self.packed_kwargs = kwargs

    def pack_forget(self) -> None:
        self.visible = False
        self.forget_count += 1

    def winfo_manager(self) -> str:
        return "pack" if self.visible else ""


def _build_controller(
    *,
    is_pro_mode: bool = True,
    initial_density: str = "normal",
) -> tuple[TopBarController, list[str], _FakeWidget, dict[str, str]]:
    density_log: list[str] = []

    def scale_topbar_widths(_density: str) -> Dict[str, int]:
        return {
            "select": 100,
            "help": 80,
            "settings": 70,
            "preset_menu": 120,
            "preset_action": 60,
            "preview": 90,
            "save": 90,
            "batch": 100,
            "zoom": 110,
        }

    select_state = {"is_pro_mode": is_pro_mode}
    select_button = _FakeWidget("画像/フォルダを選択" if is_pro_mode else "画像を選択")
    help_button = _FakeWidget("使い方")
    settings_button = _FakeWidget("設定")
    preset_manage_button = _FakeWidget("管理")
    preset_menu = _FakeWidget()
    preset_caption_label = _FakeWidget("プリセット")
    preview_button = _FakeWidget("プレビュー")
    save_button = _FakeWidget("保存")
    batch_button = _FakeWidget("一括適用保存")
    zoom_cb = _FakeWidget()
    zoom_cb.visible = True
    top_guide_frame = _FakeWidget()
    top_action_guide_label = _FakeWidget()
    top_action_guide_var = type("Var", (), {"set": lambda self, value: None})()
    top_row_primary = _FakeWidget()

    widgets = TopBarWidgets(
        top_container=_FakeWidget(),
        top_guide_frame=top_guide_frame,
        top_action_guide_var=top_action_guide_var,  # type: ignore[arg-type]
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

    controller = TopBarController(
        on_select=lambda: None,
        on_help=lambda: None,
        on_settings=lambda: None,
        on_preset_manage=lambda: None,
        on_preset_changed=lambda value: None,
        on_preview=lambda: None,
        on_save=lambda: None,
        on_batch=lambda: None,
        on_zoom_changed=lambda value: None,
        scale_px=lambda value: value,
        scale_topbar_widths=scale_topbar_widths,
        style_primary_button=lambda widget: None,
        style_secondary_button=lambda widget: None,
        style_card_frame=lambda frame: None,
        font_default=None,
        font_small=None,
        colors={"text_secondary": "#000", "bg_secondary": "#fff", "bg_tertiary": "#fff", "primary": "#000", "hover": "#000", "text_primary": "#000", "border_light": "#fff"},
        get_topbar_density=lambda: initial_density,
        set_topbar_density=lambda density: density_log.append(density),
        select_button_text=lambda: "画像/フォルダ/compact" if select_state["is_pro_mode"] else "画像を選択",
        icon_folder=None,
        icon_circle_help=None,
        icon_settings=None,
        icon_refresh=None,
        icon_save=None,
        icon_folder_open=None,
        preset_var=None,
        zoom_var=None,
    )
    controller._widgets = widgets
    return controller, density_log, select_button, {"help": help_button, "settings": settings_button, "preset_manage": preset_manage_button, "preset_menu": preset_menu, "preset_caption": preset_caption_label, "preview": preview_button, "save": save_button, "batch": batch_button, "zoom": zoom_cb, "select": select_button}


def test_apply_density_updates_width_and_label() -> None:
    controller, density_log, _, widgets = _build_controller(initial_density="normal")
    controller.apply_density(1366)

    assert density_log == ["compact"]
    assert widgets["select"].width == 100
    assert widgets["batch"].text == "一括適用保存"


def test_apply_ui_mode_hides_and_shows_non_pro_elements() -> None:
    controller, _, _, widgets = _build_controller(is_pro_mode=True)
    for key in ("preset_manage", "preset_menu", "preset_caption", "batch"):
        widgets[key].visible = False

    controller.apply_ui_mode(is_pro_mode=True, is_loading=False)
    assert widgets["batch"].visible
    assert widgets["preset_menu"].visible
    assert widgets["preset_caption"].visible

    controller.apply_ui_mode(is_pro_mode=False, is_loading=False)
    assert not widgets["batch"].visible
    assert not widgets["preset_menu"].visible
    assert not widgets["preset_caption"].visible
