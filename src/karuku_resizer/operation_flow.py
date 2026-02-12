from __future__ import annotations

from dataclasses import dataclass
from typing import Callable


@dataclass(frozen=True)
class OperationScopeHooks:
    set_controls_enabled: Callable[[bool], None]
    show_progress_with_cancel: Callable[[str, Callable[[], None], float], None]
    hide_progress_with_cancel: Callable[[], None]
    show_stage: Callable[[str], None]
    hide_stage: Callable[[], None]


class OperationScope:
    def __init__(
        self,
        *,
        hooks: OperationScopeHooks,
        stage_text: str,
        cancel_text: str,
        cancel_command: Callable[[], None],
        initial_progress: float,
    ) -> None:
        self._hooks = hooks
        self._stage_text = stage_text
        self._cancel_text = cancel_text
        self._cancel_command = cancel_command
        self._initial_progress = initial_progress
        self._active = False

    @property
    def active(self) -> bool:
        return self._active

    @property
    def stage_text(self) -> str:
        return self._stage_text

    def begin(self) -> None:
        if self._active:
            return
        self._hooks.set_controls_enabled(False)
        self._hooks.show_progress_with_cancel(
            self._cancel_text,
            self._cancel_command,
            self._initial_progress,
        )
        if self._stage_text:
            self._hooks.show_stage(self._stage_text)
        self._active = True

    def set_stage(self, stage_text: str) -> None:
        self._stage_text = stage_text
        if not self._active:
            return
        if stage_text:
            self._hooks.show_stage(stage_text)
        else:
            self._hooks.hide_stage()

    def close(self) -> None:
        if not self._active:
            return
        self._hooks.hide_progress_with_cancel()
        self._hooks.set_controls_enabled(True)
        self._hooks.hide_stage()
        self._active = False

    def __enter__(self) -> "OperationScope":
        self.begin()
        return self

    def __exit__(self, exc_type, exc, tb) -> bool:
        self.close()
        return False
