"""Operation result dialog helpers for ResizeApp."""

from __future__ import annotations

import logging
from datetime import datetime
from tkinter import messagebox
from typing import Any, Callable, Dict, List, Optional, Tuple, cast

import customtkinter

ColorMap = Dict[str, Tuple[str, str]]


def copy_text_to_clipboard(app: Any, text: str) -> bool:
    try:
        app.clipboard_clear()
        app.clipboard_append(text)
        app.update_idletasks()
        return True
    except Exception:
        logging.exception("Failed to copy text to clipboard")
        return False


def build_failure_report_text(
    *,
    title: str,
    summary_text: str,
    failed_details: List[str],
) -> str:
    timestamp = datetime.now().isoformat(timespec="seconds")
    lines = [f"[{timestamp}] {title}", summary_text]
    if failed_details:
        grouped = group_failure_details(failed_details)
        lines.append("")
        lines.append("原因別サマリー:")
        for group_name, count in grouped.items():
            lines.append(f"- {group_name}: {count}件")
        lines.append("")
        lines.append(f"失敗一覧 ({len(failed_details)}件):")
        lines.extend(f"- {detail}" for detail in failed_details)
    return "\n".join(lines)


def failure_reason_group(detail_text: str) -> str:
    lower = detail_text.lower()
    if any(token in lower for token in ("permission", "アクセス拒否", "access denied", "readonly")):
        return "権限"
    if any(token in lower for token in ("no such file", "見つかり", "not found", "path")):
        return "パス/存在"
    if any(token in lower for token in ("cannot identify image", "format", "unsupported", "decode", "壊れ", "破損")):
        return "形式/破損"
    if any(token in lower for token in ("memory", "メモリ", "resource", "リソース")):
        return "リソース"
    return "その他"


def group_failure_details(failed_details: List[str]) -> Dict[str, int]:
    grouped: Dict[str, int] = {}
    for detail in failed_details:
        key = failure_reason_group(detail)
        grouped[key] = grouped.get(key, 0) + 1
    return dict(sorted(grouped.items(), key=lambda item: (-item[1], item[0])))


def failure_center_text(
    failed_details: List[str],
    *,
    file_load_failure_preview_limit: int,
    include_details: bool = True,
) -> str:
    if not failed_details:
        return "失敗はありません。"
    grouped = group_failure_details(failed_details)
    lines: List[str] = ["原因別サマリー:"]
    for group_name, count in grouped.items():
        lines.append(f"- {group_name}: {count}件")
    if not include_details:
        return "\n".join(lines)
    lines.append("")
    lines.append("失敗一覧:")
    preview = failed_details[:file_load_failure_preview_limit]
    lines.extend(f"- {detail}" for detail in preview)
    remaining = len(failed_details) - len(preview)
    if remaining > 0:
        lines.append(f"...ほか {remaining} 件")
    return "\n".join(lines)


def show_operation_result_dialog(
    app: Any,
    *,
    colors: ColorMap,
    file_load_failure_preview_limit: int,
    title: str,
    summary_text: str,
    failed_details: List[str],
    failed_count: Optional[int] = None,
    retry_callback: Optional[Callable[[], None]] = None,
) -> None:
    if app._result_dialog is not None and app._result_dialog.winfo_exists():
        try:
            app._result_dialog.grab_release()
        except Exception:
            pass
        app._result_dialog.destroy()

    dialog = customtkinter.CTkToplevel(app)
    app._result_dialog = dialog
    dialog.title(title)
    dialog.geometry("760x430")
    dialog.resizable(False, False)
    dialog.transient(app)
    dialog.grab_set()
    dialog.configure(fg_color=colors["bg_primary"])
    dialog.grid_columnconfigure(0, weight=1)

    customtkinter.CTkLabel(
        dialog,
        text=title,
        font=app.font_bold,
        text_color=colors["text_primary"],
        anchor="w",
    ).grid(row=0, column=0, sticky="ew", padx=16, pady=(14, 6))

    customtkinter.CTkLabel(
        dialog,
        text=summary_text,
        justify="left",
        anchor="w",
        font=app.font_default,
        text_color=colors["text_secondary"],
        wraplength=720,
    ).grid(row=1, column=0, sticky="ew", padx=16, pady=(0, 8))

    if failed_count is None:
        failed_count = len(failed_details)

    summary_text_for_box = failure_center_text(
        failed_details,
        file_load_failure_preview_limit=file_load_failure_preview_limit,
        include_details=False,
    )
    details_text = failure_center_text(
        failed_details,
        file_load_failure_preview_limit=file_load_failure_preview_limit,
        include_details=True,
    )

    next_row = 2
    if failed_count and failed_count > 0 and retry_callback is not None:
        retry_hint = f"失敗ファイルが {failed_count} 件あります。再試行すると失敗したファイルのみ再実行できます。"
        customtkinter.CTkLabel(
            dialog,
            text=f"⚠ {retry_hint}",
            justify="left",
            anchor="w",
            font=app.font_default,
            text_color=colors["warning"],
            wraplength=720,
        ).grid(row=next_row, column=0, sticky="ew", padx=16, pady=(0, 8))
        next_row += 1

    details_box = customtkinter.CTkTextbox(
        dialog,
        height=120,
        corner_radius=8,
        border_width=1,
        border_color=colors["border_light"],
        fg_color=colors["input_bg"],
        text_color=cast(Any, colors["text_primary"]),
        font=app.font_small,
        wrap="word",
    )
    details_box.grid(row=next_row, column=0, sticky="nsew", padx=16, pady=(0, 10))
    details_box.insert("1.0", summary_text_for_box)
    details_box.configure(state="disabled")
    details_box_height_collapsed = 120
    details_box_height_expanded = 220

    next_row += 1
    status_label: Optional[customtkinter.CTkLabel] = None
    has_retry_button = retry_callback is not None and failed_count is not None and failed_count > 0
    if has_retry_button:
        status_label = customtkinter.CTkLabel(
            dialog,
            text="",
            font=app.font_small,
            text_color=colors["text_secondary"],
            justify="left",
            anchor="w",
            wraplength=720,
        )
        status_label.grid(row=next_row, column=0, sticky="ew", padx=16, pady=(0, 8))
        next_row += 1

    button_row = customtkinter.CTkFrame(dialog, fg_color="transparent")
    button_row.grid(row=next_row, column=0, sticky="ew", padx=16, pady=(0, 14))
    button_row.grid_columnconfigure(0, weight=1)

    def _close() -> None:
        if dialog.winfo_exists():
            dialog.grab_release()
            dialog.destroy()
        app._result_dialog = None

    retry_in_progress = False
    retry_button: Optional[Any] = None
    copy_button: Optional[Any] = None
    close_button: Optional[Any] = None
    details_expanded = False
    details_toggle_button: Optional[Any] = None

    if failed_details:
        def _toggle_details() -> None:
            nonlocal details_expanded
            if details_toggle_button is None:
                return
            if details_expanded:
                details_box.configure(state="normal")
                details_box.delete("1.0", "end")
                details_box.insert("1.0", summary_text_for_box)
                details_box.configure(state="disabled", height=details_box_height_collapsed)
                details_expanded = False
                details_toggle_button.configure(text="失敗一覧を表示")
            else:
                details_box.configure(state="normal")
                details_box.delete("1.0", "end")
                details_box.insert("1.0", details_text)
                details_box.configure(state="disabled", height=details_box_height_expanded)
                details_expanded = True
                details_toggle_button.configure(text="失敗一覧を隠す")

        details_toggle_button = customtkinter.CTkButton(
            button_row,
            text="失敗一覧を表示",
            width=140,
            command=_toggle_details,
            font=app.font_default,
        )
        app._style_secondary_button(details_toggle_button)
        details_toggle_button.pack(side="left", padx=(0, 8))

    def _start_retry() -> None:
        nonlocal retry_in_progress
        if retry_button is None or retry_in_progress or retry_callback is None:
            return
        retry_in_progress = True
        retry_button.configure(state="disabled", text="再試行中...")
        if copy_button is not None:
            copy_button.configure(state="disabled")
        if status_label is not None:
            status_label.configure(text="再試行を開始しました。処理完了までお待ちください。")
        if close_button is not None:
            close_button.configure(state="disabled")
        try:
            retry_callback()
        except Exception:
            retry_in_progress = False
            logging.exception("Failed to start retry process")
            if retry_button is not None:
                retry_button.configure(state="normal", text="失敗のみ再試行")
            if copy_button is not None:
                copy_button.configure(state="normal")
            if close_button is not None:
                close_button.configure(state="normal")
            if status_label is not None:
                status_label.configure(text="再試行の開始に失敗しました。再度お試しください。")

    if has_retry_button:
        retry_button = customtkinter.CTkButton(
            button_row,
            text="失敗のみ再試行",
            width=150,
            command=_start_retry,
            font=app.font_default,
        )
        app._style_primary_button(retry_button)
        retry_button.pack(side="right", padx=(8, 0))

    if failed_details:
        copy_button = customtkinter.CTkButton(
            button_row,
            text="失敗一覧をコピー",
            width=140,
            command=lambda: messagebox.showinfo(
                "コピー",
                "失敗一覧をクリップボードにコピーしました。"
                if copy_text_to_clipboard(
                    app,
                    build_failure_report_text(
                        title=title,
                        summary_text=summary_text,
                        failed_details=failed_details,
                    ),
                )
                else "クリップボードへのコピーに失敗しました。",
                parent=dialog,
            ),
            font=app.font_default,
        )
        app._style_secondary_button(copy_button)
        copy_button.pack(side="right", padx=(8, 0))

    close_button = customtkinter.CTkButton(
        button_row,
        text="閉じる",
        width=110,
        command=_close,
        font=app.font_default,
    )
    app._style_secondary_button(close_button)
    close_button.pack(side="right", padx=(0, 0))
