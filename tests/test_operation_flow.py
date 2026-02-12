from __future__ import annotations

from karuku_resizer.operation_flow import OperationScope, OperationScopeHooks


def test_operation_scope_begin_and_close() -> None:
    events: list[tuple] = []

    scope = OperationScope(
        hooks=OperationScopeHooks(
            set_controls_enabled=lambda enabled: events.append(("controls", enabled)),
            show_progress_with_cancel=lambda text, _command, progress: events.append(
                ("show_progress", text, progress)
            ),
            hide_progress_with_cancel=lambda: events.append(("hide_progress",)),
            show_stage=lambda text: events.append(("show_stage", text)),
            hide_stage=lambda: events.append(("hide_stage",)),
        ),
        stage_text="探索中",
        cancel_text="読み込み中止",
        cancel_command=lambda: None,
        initial_progress=0.05,
    )

    scope.begin()
    scope.close()

    assert events == [
        ("controls", False),
        ("show_progress", "読み込み中止", 0.05),
        ("show_stage", "探索中"),
        ("hide_progress",),
        ("controls", True),
        ("hide_stage",),
    ]


def test_operation_scope_set_stage_after_begin() -> None:
    events: list[tuple] = []

    scope = OperationScope(
        hooks=OperationScopeHooks(
            set_controls_enabled=lambda enabled: events.append(("controls", enabled)),
            show_progress_with_cancel=lambda text, _command, progress: events.append(
                ("show_progress", text, progress)
            ),
            hide_progress_with_cancel=lambda: events.append(("hide_progress",)),
            show_stage=lambda text: events.append(("show_stage", text)),
            hide_stage=lambda: events.append(("hide_stage",)),
        ),
        stage_text="保存中",
        cancel_text="キャンセル",
        cancel_command=lambda: None,
        initial_progress=0.0,
    )

    scope.begin()
    scope.set_stage("キャンセル中")
    scope.close()

    assert ("show_stage", "保存中") in events
    assert ("show_stage", "キャンセル中") in events


def test_operation_scope_is_idempotent() -> None:
    counters = {
        "controls": 0,
        "show_progress": 0,
        "hide_progress": 0,
        "hide_stage": 0,
    }

    scope = OperationScope(
        hooks=OperationScopeHooks(
            set_controls_enabled=lambda _enabled: counters.__setitem__(
                "controls", counters["controls"] + 1
            ),
            show_progress_with_cancel=lambda _text, _command, _progress: counters.__setitem__(
                "show_progress", counters["show_progress"] + 1
            ),
            hide_progress_with_cancel=lambda: counters.__setitem__(
                "hide_progress", counters["hide_progress"] + 1
            ),
            show_stage=lambda _text: None,
            hide_stage=lambda: counters.__setitem__("hide_stage", counters["hide_stage"] + 1),
        ),
        stage_text="探索中",
        cancel_text="読み込み中止",
        cancel_command=lambda: None,
        initial_progress=0.05,
    )

    scope.begin()
    scope.begin()
    scope.close()
    scope.close()

    assert counters["controls"] == 2
    assert counters["show_progress"] == 1
    assert counters["hide_progress"] == 1
    assert counters["hide_stage"] == 1
