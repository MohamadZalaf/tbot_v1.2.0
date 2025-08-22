# -*- mode: python ; coding: utf-8 -*-

"""
PyInstaller Spec File for TradingBot_1.2.0.exe
==============================================
This spec file builds TradingBot_1.2.0.exe that includes:
- bot_ui.py (main interface)
- tbot_v1.2.0.py (embedded trading bot)
- config.py (configuration)
- icon.ico (application icon)

Usage: pyinstaller build_TradingBot_1.2.0.spec
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
        ('config.py', '.'),
        ('tbot_v1.2.0.py', '.'),
        ('icon.ico', '.') if os.path.exists('icon.ico') else None,
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
        'sys',
        'ta',
        'PIL',
        'configparser'
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

# Filter out None values from datas
a.datas = [item for item in a.datas if item is not None]

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='TradingBot_1.2.0',
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
    version='version_info.txt' if os.path.exists('version_info.txt') else None,
    icon='icon.ico' if os.path.exists('icon.ico') else None,
    # Windows specific options
    uac_admin=False,  # Don't require admin privileges
    uac_uiaccess=False,
)