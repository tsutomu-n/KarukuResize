from __future__ import annotations

from typing import Any

from karuku_resizer.ui_file_list_panel import FileListRefs, apply_file_list_selection


class _FakeButton:
    def __init__(self) -> None:
        self.config: dict[str, Any] = {}

    def configure(self, **kwargs: Any) -> None:
        self.config.update(kwargs)


def _dummy_refs() -> FileListRefs:
    return FileListRefs(
        main_content=object(),  # type: ignore[arg-type]
        file_list_frame=object(),  # type: ignore[arg-type]
        file_filter_var=object(),  # type: ignore[arg-type]
        file_filter_segment=object(),  # type: ignore[arg-type]
        file_buttons=[_FakeButton(), _FakeButton()],  # type: ignore[list-item]
        empty_state_label=object(),  # type: ignore[arg-type]
        font_small=None,
    )


def test_apply_file_list_selection_accepts_incomplete_colors() -> None:
    refs = _dummy_refs()

    apply_file_list_selection(
        refs,
        previous_job_index=0,
        current_job_index=1,
        visible_job_indices=[0, 1],
        colors={"bg_secondary": "#fff"},
    )

    prev_cfg = refs.file_buttons[0].config
    current_cfg = refs.file_buttons[1].config
    assert prev_cfg["border_color"] == "#D9E2EC"
    assert current_cfg["border_color"] == "#D9E2EC"
    assert "text_color" in current_cfg
