from __future__ import annotations

from pathlib import Path

from karuku_resizer.resize_core import _build_arg_parser, _build_cli_summary, _interpret_resize_result


def test_cli_parser_accepts_json_flag() -> None:
    parser = _build_arg_parser()
    args = parser.parse_args(["-s", "in", "-d", "out", "--json"])
    assert args.json is True
    assert args.recursive is True


def test_build_cli_summary_shape() -> None:
    summary = _build_cli_summary(
        status="success",
        source=Path("input"),
        dest=Path("output"),
        total_files=10,
        processed_count=10,
        failed_count=0,
        dry_run=False,
        output_format="jpeg",
        width=1280,
        quality=85,
        recursive=True,
        extensions=[".jpg", ".jpeg", ".png"],
        elapsed_seconds=1.23456,
        failed_files=[],
        failures_file="",
        message="ok",
    )

    assert summary["status"] == "success"
    assert summary["source"] == "input"
    assert summary["dest"] == "output"
    assert summary["options"]["format"] == "jpeg"
    assert summary["options"]["width"] == 1280
    assert summary["options"]["recursive"] is True
    assert summary["options"]["extensions"] == [".jpg", ".jpeg", ".png"]
    assert summary["elapsed_seconds"] == 1.235
    assert summary["failed_files"] == []


def test_interpret_resize_result() -> None:
    assert _interpret_resize_result((True, False, None)) == (True, "")
    assert _interpret_resize_result((False, "bad file")) == (False, "bad file")
    assert _interpret_resize_result((False, False, None)) == (False, "処理失敗（詳細はログ参照）")
