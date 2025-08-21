#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
🏗️ Trading Bot Builder v1.2.0 - Enhanced EXE Builder
====================================================
Advanced Python script to build Trading_tbot_v1.2.0.exe

Features:
- Auto-detection of required files
- Comprehensive error handling
- Progress tracking
- Automatic dependency installation
- Icon embedding
- File size optimization
- Build verification

Developer: Enhanced Builder System
Compatible with: tbot_v1.2.0.py, config.py, bot_ui.py
"""

import os
import sys
import subprocess
import shutil
import json
import time
from pathlib import Path

class TradingBotBuilder:
    def __init__(self):
        self.project_dir = Path.cwd()
        self.build_dir = self.project_dir / "build"
        self.dist_dir = self.project_dir / "dist"
        self.required_files = {
            'main_bot': 'tbot_v1.2.0.py',
            'config': 'config.py',
            'icon': 'icon.ico',
            'ui': 'bot_ui.py'
        }
        self.output_name = 'Trading_tbot_v1.2.0.exe'
        
    def print_header(self):
        """Print builder header"""
        print("=" * 60)
        print("🏗️  Trading Bot EXE Builder v1.2.0")
        print("=" * 60)
        print()
    
    def check_python_version(self):
        """Check if Python version is compatible"""
        print("🐍 Checking Python version...")
        version = sys.version_info
        if version.major < 3 or (version.major == 3 and version.minor < 7):
            print("❌ Error: Python 3.7+ is required")
            print(f"   Current version: {version.major}.{version.minor}.{version.micro}")
            return False
        
        print(f"✅ Python version: {version.major}.{version.minor}.{version.micro}")
        return True
    
    def check_required_files(self):
        """Check if all required files exist"""
        print("\n📁 Checking required files...")
        missing_files = []
        
        for file_type, filename in self.required_files.items():
            file_path = self.project_dir / filename
            if file_path.exists():
                size = file_path.stat().st_size
                print(f"✅ {filename} ({size:,} bytes)")
            else:
                print(f"❌ {filename} - Not found")
                missing_files.append(filename)
        
        if missing_files:
            print(f"\n❌ Missing files: {', '.join(missing_files)}")
            return False
        
        print("✅ All required files found")
        return True
    
    def install_pyinstaller(self):
        """Install or upgrade PyInstaller"""
        print("\n🔧 Checking PyInstaller...")
        try:
            import PyInstaller
            print(f"✅ PyInstaller already installed: {PyInstaller.__version__}")
            return True
        except ImportError:
            print("📦 Installing PyInstaller...")
            try:
                subprocess.run([sys.executable, "-m", "pip", "install", "--upgrade", "pyinstaller"], 
                             check=True, capture_output=True, text=True)
                print("✅ PyInstaller installed successfully")
                return True
            except subprocess.CalledProcessError as e:
                print(f"❌ Failed to install PyInstaller: {e}")
                return False
    
    def install_dependencies(self):
        """Install required dependencies"""
        print("\n📦 Installing dependencies...")
        dependencies = [
            "telebot",
            "pandas",
            "numpy",
            "MetaTrader5",
            "google-generativeai",
            "requests",
            "pytz",
            "python-dateutil"
        ]
        
        for dep in dependencies:
            try:
                print(f"   Installing {dep}...")
                subprocess.run([sys.executable, "-m", "pip", "install", "--upgrade", dep], 
                             check=True, capture_output=True, text=True)
                print(f"   ✅ {dep} installed")
            except subprocess.CalledProcessError:
                print(f"   ⚠️  {dep} installation failed (may already exist)")
        
        print("✅ Dependencies installation completed")
    
    def clean_previous_builds(self):
        """Clean previous build artifacts"""
        print("\n🧹 Cleaning previous builds...")
        
        # Remove build directory
        if self.build_dir.exists():
            shutil.rmtree(self.build_dir)
            print("✅ Removed build directory")
        
        # Remove dist directory
        if self.dist_dir.exists():
            shutil.rmtree(self.dist_dir)
            print("✅ Removed dist directory")
        
        # Remove spec files
        spec_files = list(self.project_dir.glob("*.spec"))
        for spec_file in spec_files:
            spec_file.unlink()
            print(f"✅ Removed {spec_file.name}")
    
    def create_build_spec(self):
        """Create PyInstaller spec file"""
        print("\n📝 Creating build specification...")
        
        spec_content = f'''# -*- mode: python ; coding: utf-8 -*-

a = Analysis(
    ['{self.required_files["main_bot"]}'],
    pathex=['{self.project_dir}'],
    binaries=[],
    datas=[
        ('{self.required_files["config"]}', '.'),
        ('trading_data', 'trading_data'),
    ],
    hiddenimports=[
        'telebot',
        'pandas',
        'numpy',
        'MetaTrader5',
        'google.generativeai',
        'requests',
        'pytz',
        'dateutil',
        'json',
        'logging',
        'threading',
        'time',
        'os',
        'sys',
        'sqlite3',
        'tkinter',
        'tkinter.ttk',
        'tkinter.messagebox',
        'tkinter.scrolledtext',
        'tkinter.filedialog'
    ],
    hookspath=[],
    hooksconfig={{}},
    runtime_hooks=[],
    excludes=[
        'matplotlib',
        'scipy',
        'IPython',
        'jupyter',
        'notebook'
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=None,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=None)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='{self.output_name.replace(".exe", "")}',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='{self.required_files["icon"]}' if Path('{self.required_files["icon"]}').exists() else None,
)
'''
        
        spec_file = self.project_dir / f"{self.output_name.replace('.exe', '.spec')}"
        with open(spec_file, 'w', encoding='utf-8') as f:
            f.write(spec_content)
        
        print(f"✅ Created {spec_file.name}")
        return spec_file
    
    def build_executable(self, spec_file):
        """Build the executable using PyInstaller"""
        print("\n🔨 Building executable...")
        print("This may take several minutes...")
        
        start_time = time.time()
        
        try:
            # Run PyInstaller
            cmd = [sys.executable, "-m", "PyInstaller", "--clean", str(spec_file)]
            
            print("Running PyInstaller...")
            process = subprocess.run(cmd, capture_output=True, text=True, cwd=self.project_dir)
            
            if process.returncode == 0:
                build_time = time.time() - start_time
                print(f"✅ Build completed in {build_time:.1f} seconds")
                return True
            else:
                print("❌ Build failed!")
                print("STDOUT:", process.stdout)
                print("STDERR:", process.stderr)
                return False
                
        except Exception as e:
            print(f"❌ Build error: {e}")
            return False
    
    def verify_build(self):
        """Verify the built executable"""
        print("\n🔍 Verifying build...")
        
        exe_path = self.dist_dir / self.output_name
        
        if not exe_path.exists():
            print(f"❌ Executable not found: {exe_path}")
            return False
        
        # Check file size
        file_size = exe_path.stat().st_size
        print(f"✅ Executable created: {exe_path}")
        print(f"📊 File size: {file_size:,} bytes ({file_size/1024/1024:.1f} MB)")
        
        # Check if file is executable
        if os.access(exe_path, os.X_OK):
            print("✅ File is executable")
        else:
            print("⚠️  File may not be executable")
        
        return True
    
    def create_readme(self):
        """Create README file for the executable"""
        print("\n📄 Creating README...")
        
        readme_content = f'''# Trading Bot v1.2.0 - Executable Package

## 📦 Package Contents
- {self.output_name} - Main executable file
- config.py - Configuration file (if needed)
- trading_data/ - Data directory (created automatically)

## 🚀 How to Run
1. Double-click {self.output_name}
2. Or run from command line: ./{self.output_name}

## ⚙️ Requirements
- Windows 10/11 (64-bit)
- Internet connection for Telegram API
- MetaTrader 5 (for trading data)

## 🔧 Configuration
Edit config.py if you need to change:
- Telegram Bot Token
- Gemini AI API Key
- Other settings

## 📝 Notes
- First run may take longer (Windows Defender scan)
- Keep config.py in the same directory as the exe
- The bot will create trading_data folder automatically

## 🆘 Troubleshooting
- If antivirus blocks the file, add it to exceptions
- Run as administrator if needed
- Check internet connection
- Verify config.py settings

Built on: {time.strftime('%Y-%m-%d %H:%M:%S')}
Builder: Trading Bot Builder v1.2.0
'''
        
        readme_path = self.dist_dir / "README.txt"
        with open(readme_path, 'w', encoding='utf-8') as f:
            f.write(readme_content)
        
        print(f"✅ Created {readme_path}")
    
    def copy_additional_files(self):
        """Copy additional required files to dist directory"""
        print("\n📋 Copying additional files...")
        
        # Copy config.py if it exists
        config_src = self.project_dir / self.required_files['config']
        config_dst = self.dist_dir / self.required_files['config']
        
        if config_src.exists():
            shutil.copy2(config_src, config_dst)
            print(f"✅ Copied {self.required_files['config']}")
        
        # Create trading_data directory
        trading_data_dir = self.dist_dir / "trading_data"
        trading_data_dir.mkdir(exist_ok=True)
        print("✅ Created trading_data directory")
    
    def print_summary(self):
        """Print build summary"""
        print("\n" + "=" * 60)
        print("🎉 BUILD COMPLETED SUCCESSFULLY!")
        print("=" * 60)
        
        exe_path = self.dist_dir / self.output_name
        if exe_path.exists():
            file_size = exe_path.stat().st_size
            print(f"📦 Executable: {exe_path}")
            print(f"📊 Size: {file_size:,} bytes ({file_size/1024/1024:.1f} MB)")
        
        print(f"📁 Output directory: {self.dist_dir}")
        print("\n🚀 Ready to distribute!")
        print("\n💡 Tips:")
        print("   • Test the executable before distribution")
        print("   • Include config.py with your bot token")
        print("   • The exe includes all dependencies")
        print("   • First run may trigger antivirus scan")
    
    def build(self):
        """Main build process"""
        self.print_header()
        
        # Pre-build checks
        if not self.check_python_version():
            return False
            
        if not self.check_required_files():
            return False
        
        if not self.install_pyinstaller():
            return False
        
        # Install dependencies
        self.install_dependencies()
        
        # Build process
        self.clean_previous_builds()
        spec_file = self.create_build_spec()
        
        if not self.build_executable(spec_file):
            return False
        
        if not self.verify_build():
            return False
        
        # Post-build tasks
        self.copy_additional_files()
        self.create_readme()
        self.print_summary()
        
        return True

def main():
    """Main function"""
    builder = TradingBotBuilder()
    
    try:
        success = builder.build()
        if success:
            print("\n✅ Build process completed successfully!")
            sys.exit(0)
        else:
            print("\n❌ Build process failed!")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n\n⚠️  Build interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()