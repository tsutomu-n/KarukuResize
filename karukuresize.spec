# -*- mode: python ; coding: utf-8 -*-

import sys
import os
from PyInstaller.utils.hooks import collect_data_files, collect_submodules
from pathlib import Path

# プロジェクトのルートディレクトリ
ROOT_DIR = Path(__file__).parent

# アプリケーション情報
APP_NAME = 'KarukuResize'
APP_VERSION = '0.2.1'
APP_DESCRIPTION = '日本語対応の画像リサイズ・圧縮ツール'

# データファイルの収集
customtkinter_datas = collect_data_files('customtkinter')
tkinterdnd2_datas = collect_data_files('tkinterdnd2')

# 追加のデータファイル
added_files = [
    ('karuku_light_theme.json', '.'),
    ('japanese_font_utils.py', '.'),
    ('error_handler.py', '.'),
    ('validators.py', '.'),
    ('thread_safe_gui.py', '.'),
    ('drag_drop_handler.py', '.'),
    ('progress_tracker.py', '.'),
    ('settings_manager.py', '.'),
    ('error_dialog.py', '.'),
    ('image_preview.py', '.'),
    ('preset_manager.py', '.'),
    ('history_manager.py', '.'),
    ('statistics_viewer.py', '.'),
    ('preset_dialog.py', '.'),
    ('history_viewer.py', '.'),
    ('resize_core.py', '.'),
    ('karukuresize', 'karukuresize'),
]

# 隠しインポート
hidden_imports = [
    'PIL._tkinter_finder',
    'darkdetect',
    'matplotlib.backends.backend_tkagg',
    'loguru',
    'tqdm',
    'emoji',
    'dateutil',
]

# Analysis設定
a = Analysis(
    ['resize_images_gui.py'],
    pathex=[str(ROOT_DIR)],
    binaries=[],
    datas=added_files + customtkinter_datas + tkinterdnd2_datas,
    hiddenimports=hidden_imports,
    hookspath=['./'],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'pytest',
        'flake8',
        'black',
        'ruff',
        'pre-commit',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=None,
    noarchive=False,
)

# PYZアーカイブ
pyz = PYZ(a.pure, a.zipped_data, cipher=None)

# Windows用の設定
if sys.platform == 'win32':
    # Windows長パス対応のためのマニフェスト
    manifest = '''
    <?xml version="1.0" encoding="UTF-8" standalone="yes"?>
    <assembly xmlns="urn:schemas-microsoft-com:asm.v1" manifestVersion="1.0">
      <assemblyIdentity
        version="1.0.0.0"
        processorArchitecture="*"
        name="KarukuResize"
        type="win32"
      />
      <description>KarukuResize - 日本語対応の画像リサイズ・圧縮ツール</description>
      <trustInfo xmlns="urn:schemas-microsoft-com:asm.v3">
        <security>
          <requestedPrivileges>
            <requestedExecutionLevel level="asInvoker" uiAccess="false"/>
          </requestedPrivileges>
        </security>
      </trustInfo>
      <compatibility xmlns="urn:schemas-microsoft-com:compatibility.v1">
        <application>
          <supportedOS Id="{8e0f7a12-bfb3-4fe8-b9a5-48fd50a15a9a}"/> <!-- Windows 10/11 -->
        </application>
      </compatibility>
      <application xmlns="urn:schemas-microsoft-com:asm.v3">
        <windowsSettings>
          <longPathAware xmlns="http://schemas.microsoft.com/SMI/2016/WindowsSettings">true</longPathAware>
          <dpiAware xmlns="http://schemas.microsoft.com/SMI/2005/WindowsSettings">true</dpiAware>
          <dpiAwareness xmlns="http://schemas.microsoft.com/SMI/2016/WindowsSettings">PerMonitorV2</dpiAwareness>
        </windowsSettings>
      </application>
    </assembly>
    '''
    
    # EXE設定
    exe = EXE(
        pyz,
        a.scripts,
        [],
        exclude_binaries=True,
        name=APP_NAME,
        debug=False,
        bootloader_ignore_signals=False,
        strip=False,
        upx=True,
        console=False,  # GUIアプリケーションなのでコンソールは非表示
        disable_windowed_traceback=False,
        argv_emulation=False,
        target_arch=None,
        codesign_identity=None,
        entitlements_file=None,
        uac_admin=False,
        uac_uiaccess=False,
        manifest=manifest,
        version='version_info.txt' if os.path.exists('version_info.txt') else None,
    )
else:
    # macOS/Linux用の設定
    exe = EXE(
        pyz,
        a.scripts,
        [],
        exclude_binaries=True,
        name=APP_NAME.lower(),
        debug=False,
        bootloader_ignore_signals=False,
        strip=False,
        upx=True,
        console=False,
        disable_windowed_traceback=False,
        argv_emulation=False,
        target_arch=None,
        codesign_identity=None,
        entitlements_file=None,
    )

# 配布用ディレクトリ
coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name=APP_NAME,
)

# macOS用のアプリバンドル
if sys.platform == 'darwin':
    app = BUNDLE(
        coll,
        name=f'{APP_NAME}.app',
        icon=None,  # アイコンファイルがある場合はここに指定
        bundle_identifier='com.karukuresize.app',
        version=APP_VERSION,
        info_plist={
            'NSPrincipalClass': 'NSApplication',
            'NSAppleScriptEnabled': False,
            'CFBundleDocumentTypes': [
                {
                    'CFBundleTypeName': 'Image Files',
                    'CFBundleTypeRole': 'Viewer',
                    'CFBundleTypeExtensions': ['jpg', 'jpeg', 'png', 'gif', 'bmp', 'webp', 'tiff', 'tif'],
                }
            ],
            'NSHighResolutionCapable': 'True',
        },
    )