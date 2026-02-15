# -*- mode: python ; coding: utf-8 -*-

from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent
SCRIPT_PATH = PROJECT_ROOT / "src" / "karuku_resizer" / "gui_app.py"
HOOKS_DIR = PROJECT_ROOT / "src" / "karuku_resizer" / "tools"
ICON_PATH = PROJECT_ROOT / "assets" / "app.ico"
ICON_ARG = str(ICON_PATH) if ICON_PATH.is_file() else None

a = Analysis(
    [str(SCRIPT_PATH)],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=['pillow_avif'],
    hookspath=[str(HOOKS_DIR)],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='KarukuResize',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=ICON_ARG,
)
