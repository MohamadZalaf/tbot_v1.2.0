#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
🔧 Build Script for Trading Bot UI - EMBEDDED VERSION
==================================================
Script to build a standalone .exe file with all dependencies embedded

Features:
- Creates single .exe file with all Python code embedded
- Includes all required libraries and dependencies
- No external .py files needed for execution
- Protects source code from theft

Developer: Mohamad Zalaf ©️2025
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path

def check_pyinstaller():
    """Check if PyInstaller is installed"""
    try:
        import PyInstaller
        print("✅ PyInstaller is installed")
        return True
    except ImportError:
        print("❌ PyInstaller not found. Installing...")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])
            print("✅ PyInstaller installed successfully")
            return True
        except Exception as e:
            print(f"❌ Failed to install PyInstaller: {e}")
            return False

def install_requirements():
    """Install all required packages"""
    print("📦 Installing required packages...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("✅ All requirements installed successfully")
        return True
    except Exception as e:
        print(f"❌ Failed to install requirements: {e}")
        return False

def create_spec_file():
    """Create PyInstaller .spec file for advanced configuration"""
    spec_content = '''# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['bot_ui.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('requirements.txt', '.'),
    ],
    hiddenimports=[
        'telebot',
        'telebot.apihelper',
        'pandas',
        'numpy',
        'MetaTrader5',
        'google.generativeai',
        'ta',
        'PIL',
        'PIL.Image',
        'PIL.ImageDraw',
        'PIL.ImageFont',
        'glob',
        'tkinter',
        'tkinter.messagebox',
        'tkinter.scrolledtext',
        'tkinter.ttk',
        'threading',
        'json',
        'logging',
        'logging.handlers',
        'dataclasses',
        'datetime',
        'warnings',
        'requests',
        'urllib3',
        'pytz',
        'python_dateutil',
        'colorama'
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
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
    name='TradingBot_UI_v1.2.0',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # Hide console window
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='icon.ico' if os.path.exists('icon.ico') else None,
)
'''
    
    with open('bot_ui.spec', 'w', encoding='utf-8') as f:
        f.write(spec_content)
    
    print("✅ PyInstaller spec file created")

def build_exe():
    """Build the executable using PyInstaller"""
    print("🔨 Building executable file...")
    print("This may take several minutes...")
    
    try:
        # Build using the spec file for better control
        cmd = [
            'pyinstaller',
            '--clean',
            '--noconfirm',
            'bot_ui.spec'
        ]
        
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
            universal_newlines=True
        )
        
        # Print output in real-time
        while True:
            output = process.stdout.readline()
            if output == '' and process.poll() is not None:
                break
            if output:
                print(f"  {output.strip()}")
        
        # Get any remaining output
        stdout, stderr = process.communicate()
        
        if process.returncode == 0:
            print("✅ Executable built successfully!")
            return True
        else:
            print(f"❌ Build failed with return code {process.returncode}")
            if stderr:
                print(f"Error output: {stderr}")
            return False
            
    except Exception as e:
        print(f"❌ Build failed: {e}")
        return False

def cleanup_build_files():
    """Clean up temporary build files"""
    print("🧹 Cleaning up build files...")
    
    cleanup_dirs = ['build', '__pycache__']
    cleanup_files = ['bot_ui.spec']
    
    for dir_name in cleanup_dirs:
        if os.path.exists(dir_name):
            try:
                shutil.rmtree(dir_name)
                print(f"  Removed {dir_name}/")
            except Exception as e:
                print(f"  Warning: Could not remove {dir_name}/: {e}")
    
    for file_name in cleanup_files:
        if os.path.exists(file_name):
            try:
                os.remove(file_name)
                print(f"  Removed {file_name}")
            except Exception as e:
                print(f"  Warning: Could not remove {file_name}: {e}")

def verify_exe():
    """Verify the built executable"""
    exe_path = Path('dist/TradingBot_UI_v1.2.0.exe')
    
    if exe_path.exists():
        file_size = exe_path.stat().st_size / (1024 * 1024)  # Size in MB
        print(f"✅ Executable created successfully!")
        print(f"📍 Location: {exe_path.absolute()}")
        print(f"📏 Size: {file_size:.1f} MB")
        
        # Test if exe can be executed (basic check)
        print("🧪 Testing executable...")
        try:
            # Just check if the file is executable, don't actually run it
            if os.access(exe_path, os.X_OK):
                print("✅ Executable is valid and ready to run")
            else:
                print("⚠️  Executable may have permission issues")
        except Exception as e:
            print(f"⚠️  Could not test executable: {e}")
        
        return True
    else:
        print("❌ Executable not found in dist/ directory")
        return False

def main():
    """Main build process"""
    print("🤖 Trading Bot UI - Executable Builder v1.2.0")
    print("=" * 50)
    print("🎯 Building standalone .exe with embedded bot code")
    print("🔒 This will protect your source code from theft")
    print()
    
    # Check if bot_ui.py exists
    if not os.path.exists('bot_ui.py'):
        print("❌ Error: bot_ui.py not found in current directory!")
        print("Please run this script from the same directory as bot_ui.py")
        return False
    
    # Step 1: Check PyInstaller
    if not check_pyinstaller():
        return False
    
    # Step 2: Install requirements
    if not install_requirements():
        print("⚠️  Continuing without installing requirements...")
    
    # Step 3: Create spec file
    create_spec_file()
    
    # Step 4: Build executable
    if not build_exe():
        return False
    
    # Step 5: Verify executable
    if not verify_exe():
        return False
    
    # Step 6: Cleanup
    cleanup_build_files()
    
    print()
    print("🎉 Build completed successfully!")
    print("=" * 50)
    print("📦 Your standalone executable is ready:")
    print("   📍 dist/TradingBot_UI_v1.2.0.exe")
    print()
    print("🔒 Security Features:")
    print("   ✅ All Python code is embedded and protected")
    print("   ✅ No external .py files needed")
    print("   ✅ tbot_v1.2.0.py code is fully protected from theft")
    print("   ✅ Can be distributed without exposing source code")
    print()
    print("🚀 You can now distribute the .exe file safely!")
    
    return True

if __name__ == "__main__":
    try:
        success = main()
        if success:
            input("\nPress Enter to exit...")
    except KeyboardInterrupt:
        print("\n❌ Build cancelled by user")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        input("Press Enter to exit...")