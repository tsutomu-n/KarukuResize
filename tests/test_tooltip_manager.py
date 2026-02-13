from __future__ import annotations

from types import SimpleNamespace

from karuku_resizer.tools.tooltip_manager import TooltipManager


class DummyRoot:
    def __init__(self) -> None:
        self.bound_all_sequences: list[str] = []
        self.bound_sequences: list[str] = []
        self.containing_widget = None

    def after(self, _delay_ms: int, _callback):  # pragma: no cover - scheduling is not exercised here
        return "after-id"

    def after_cancel(self, _after_id: str) -> None:  # pragma: no cover
        return None

    def bind_all(self, sequence: str, _callback, add: str = "+") -> None:
        self.bound_all_sequences.append(f"{sequence}:{add}")

    def bind(self, sequence: str, _callback, add: str = "+") -> None:
        self.bound_sequences.append(f"{sequence}:{add}")

    def winfo_containing(self, _x_root: int, _y_root: int):
        return self.containing_widget


class DummyWidget:
    def __init__(
        self,
        *,
        bind_mode: str = "ok",
        children: list["DummyWidget"] | None = None,
        master: "DummyWidget | None" = None,
    ) -> None:
        self.bind_mode = bind_mode
        self._children = children or []
        self.bound_sequences: list[str] = []
        self.master = master
        for child in self._children:
            child.master = self

    def bind(self, sequence: str, _callback, add: str = "+") -> None:
        if self.bind_mode == "not_impl":
            raise NotImplementedError
        if self.bind_mode == "attr_error":
            raise AttributeError("bind unavailable")
        self.bound_sequences.append(f"{sequence}:{add}")

    def winfo_children(self) -> list["DummyWidget"]:
        return list(self._children)

    def winfo_exists(self) -> bool:
        return True


def test_register_binds_supported_widget() -> None:
    root = DummyRoot()
    manager = TooltipManager(root, enabled_provider=lambda: True)
    widget = DummyWidget()

    manager.register(widget, "sample")

    assert any(item.startswith("<Enter>") for item in widget.bound_sequences)
    assert any(item.startswith("<Leave>") for item in widget.bound_sequences)
    assert any(item.startswith("<FocusIn>") for item in widget.bound_sequences)
    assert any(item.startswith("<FocusOut>") for item in widget.bound_sequences)
    assert any(item.startswith("<Motion>") for item in root.bound_all_sequences)


def test_register_falls_back_to_child_widgets_when_parent_bind_is_not_supported() -> None:
    manager = TooltipManager(DummyRoot(), enabled_provider=lambda: True)
    child = DummyWidget()
    parent = DummyWidget(bind_mode="not_impl", children=[child])

    manager.register(parent, "sample")

    assert child.bound_sequences
    assert any(item.startswith("<Enter>") for item in child.bound_sequences)


def test_register_falls_back_recursively_for_nested_children() -> None:
    manager = TooltipManager(DummyRoot(), enabled_provider=lambda: True)
    grandchild = DummyWidget()
    child = DummyWidget(bind_mode="not_impl", children=[grandchild])
    parent = DummyWidget(bind_mode="not_impl", children=[child])

    manager.register(parent, "sample")

    assert grandchild.bound_sequences
    assert any(item.startswith("<Enter>") for item in grandchild.bound_sequences)


def test_register_uses_buttons_dict_when_available() -> None:
    manager = TooltipManager(DummyRoot(), enabled_provider=lambda: True)
    internal_button = DummyWidget()
    segmented_like = DummyWidget(bind_mode="not_impl")
    segmented_like._buttons_dict = {"one": internal_button}  # type: ignore[attr-defined]

    manager.register(segmented_like, "sample")

    assert internal_button.bound_sequences
    assert any(item.startswith("<Enter>") for item in internal_button.bound_sequences)


def test_register_does_not_raise_when_bind_is_unsupported_and_no_children() -> None:
    manager = TooltipManager(DummyRoot(), enabled_provider=lambda: True)
    unsupported_widget = DummyWidget(bind_mode="not_impl")

    manager.register(unsupported_widget, "sample")


def test_register_binds_child_widgets_even_if_parent_bind_is_supported() -> None:
    manager = TooltipManager(DummyRoot(), enabled_provider=lambda: True)
    child = DummyWidget()
    parent = DummyWidget(bind_mode="ok", children=[child])

    manager.register(parent, "sample")

    assert parent.bound_sequences
    assert child.bound_sequences


def test_register_keeps_text_for_bind_unsupported_widget() -> None:
    manager = TooltipManager(DummyRoot(), enabled_provider=lambda: True)
    unsupported = DummyWidget(bind_mode="not_impl")

    manager.register(unsupported, "sample")

    assert manager._texts.get(unsupported) == "sample"


def test_global_motion_falls_back_to_parent_tooltip() -> None:
    root = DummyRoot()
    manager = TooltipManager(root, enabled_provider=lambda: True)
    parent = DummyWidget(bind_mode="not_impl")

    manager.register(parent, "sample")
    child = DummyWidget(master=parent)
    root.containing_widget = child
    manager._on_global_motion(SimpleNamespace(x_root=10, y_root=20))

    assert manager._pending_widget is parent
