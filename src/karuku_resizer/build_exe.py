"""Utility to build a standalone Windows executable using PyInstaller.

This script is intended for developer convenience. It wraps the PyInstaller
CLI invocation so that contributors can simply run

    uv run karukuresize-build-exe

and obtain `dist/KarukuResize.exe`.

The generated executable bundles the GUI application (`gui_app:main`) in
one file mode without a console window. Adjust the `PYINSTALLER_ARGS` list
below to tweak the build (e.g., add data files or remove `--onefile`).
"""
from __future__ import annotations

import sys
import os
from pathlib import Path

try:
    from PyInstaller.__main__ import run as pyinstaller_run  # type: ignore
except ModuleNotFoundError as exc:  # pragma: no cover
    msg = (
        "PyInstaller is not installed in the current environment. "
        "Run 'uv add --group dev pyinstaller' first."
    )
    raise SystemExit(msg) from exc

# ---------------------------------------------------------------------------
# Build configuration
# ---------------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parents[2]
DIST_DIR = PROJECT_ROOT / "dist"

NAME = "KarukuResize"
MODULE = "karuku_resizer.gui_app"
ICON_PATH = PROJECT_ROOT / "assets" / "app.ico"  # optional icon

# Base arguments
PYINSTALLER_ARGS: list[str] = [
    "--name",
    NAME,
    "--noconfirm",
    "--windowed",
    "--onefile",
]

# Add icon if it exists
if ICON_PATH.is_file():
    PYINSTALLER_ARGS.extend(["--icon", str(ICON_PATH)])

# Entry point script path
SCRIPT_PATH = PROJECT_ROOT / "src" / "karuku_resizer" / "gui_app.py"
HOOKS_DIR = PROJECT_ROOT / "src" / "karuku_resizer" / "tools"

# AVIFプラグインは環境依存で取りこぼしが起きやすいため明示的に追加
PYINSTALLER_ARGS.extend(["--hidden-import", "pillow_avif"])
if HOOKS_DIR.is_dir():
    PYINSTALLER_ARGS.extend(["--additional-hooks-dir", str(HOOKS_DIR)])
PYINSTALLER_ARGS.append(str(SCRIPT_PATH))


def _expected_binary_path() -> Path:
    suffix = ".exe" if sys.platform.startswith("win") else ""
    return DIST_DIR / f"{NAME}{suffix}"


def main() -> None:  # noqa: D401
    """Invoke PyInstaller with the predefined arguments."""
    print("Running PyInstaller with arguments:\n", " ".join(PYINSTALLER_ARGS))
    # Ensure we are executed from project root so that relative paths resolve.
    old_cwd = Path.cwd()
    try:
        os.chdir(PROJECT_ROOT)
        pyinstaller_run(PYINSTALLER_ARGS)
        exe_path = _expected_binary_path()
        if exe_path.exists():
            print(f"\nSuccess! Built executable at: {exe_path}")
        else:
            print(
                "PyInstaller finished but expected output was not found: "
                f"{exe_path}. Check output."
            )
    finally:
        os.chdir(old_cwd)


if __name__ == "__main__":  # pragma: no cover
    main()
