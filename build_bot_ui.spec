# -*- mode: python ; coding: utf-8 -*-

"""
PyInstaller Spec File for Trading Bot UI v1.2.0
===============================================
This spec file builds a standalone executable that includes:
- Complete bot functionality embedded
- All required dependencies
- No external .py or .ico files needed
- Optimized for distribution

Usage: pyinstaller build_bot_ui.spec
"""

import os
import sys

# Add current directory to path
current_dir = os.path.dirname(os.path.abspath('__file__'))

block_cipher = None

a = Analysis(
    ['bot_ui.py'],
    pathex=[current_dir],
    binaries=[],
    datas=[
        # No external data files needed - everything is embedded
    ],
    hiddenimports=[
        'telebot',
        'telebot.apihelper',
        'telebot.types',
        'pandas',
        'numpy',
        'MetaTrader5',
        'google.generativeai',
        'logging.handlers',
        'dataclasses',
        'datetime',
        'warnings',
        'tkinter',
        'tkinter.messagebox',
        'tkinter.scrolledtext',
        'tkinter.ttk',
        'tkinter.simpledialog',
        'threading',
        'time',
        'json',
        'base64',
        'typing',
        'glob',
        'io',
        'subprocess',
        'os',
        'sys'
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        # Exclude unnecessary modules to reduce size
        'matplotlib',
        'scipy',
        'jupyter',
        'notebook',
        'IPython',
        'pytest',
        'unittest',
        'doctest',
        'pydoc',
        'tkinter.test'
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='TradingBotUI_v1.2.0',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # No console window
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    # Executable properties
    version='version_info.txt',  # Optional version info file
    icon=None,  # No external icon file needed - embedded in code
    # Windows specific options
    uac_admin=False,  # Don't require admin privileges
    uac_uiaccess=False,
)

# Optional: Create version info file
version_info = """
VSVersionInfo(
  ffi=FixedFileInfo(
    filevers=(1, 2, 0, 0),
    prodvers=(1, 2, 0, 0),
    mask=0x3f,
    flags=0x0,
    OS=0x40004,
    fileType=0x1,
    subtype=0x0,
    date=(0, 0)
  ),
  kids=[
    StringFileInfo(
      [
      StringTable(
        u'040904B0',
        [StringStruct(u'CompanyName', u'Mohamad Zalaf'),
        StringStruct(u'FileDescription', u'Trading Bot UI Controller'),
        StringStruct(u'FileVersion', u'1.2.0.0'),
        StringStruct(u'InternalName', u'TradingBotUI'),
        StringStruct(u'LegalCopyright', u'Copyright © 2025 Mohamad Zalaf'),
        StringStruct(u'OriginalFilename', u'TradingBotUI_v1.2.0.exe'),
        StringStruct(u'ProductName', u'Advanced Trading Bot UI'),
        StringStruct(u'ProductVersion', u'1.2.0.0')])
      ]),
    VarFileInfo([VarStruct(u'Translation', [1033, 1200])])
  ]
)
"""

# Write version info to file
with open('version_info.txt', 'w', encoding='utf-8') as f:
    f.write(version_info)