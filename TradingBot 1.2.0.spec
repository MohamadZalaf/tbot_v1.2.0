# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['bot_ui.py'],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=['telebot', 'telebot.apihelper', 'telebot.types', 'pandas', 'numpy', 'MetaTrader5', 'google.generativeai', 'logging.handlers', 'tkinter.messagebox', 'tkinter.scrolledtext', 'tkinter.ttk', 'tkinter.simpledialog'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['matplotlib', 'scipy', 'jupyter', 'notebook', 'IPython', 'pytest', 'unittest'],
    noarchive=False,
    optimize=2,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [('O', None, 'OPTION'), ('O', None, 'OPTION')],
    name='TradingBot 1.2.0',
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
    version='version_info.txt',
)
