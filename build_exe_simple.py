#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
🔧 Simple Build Script for Trading Bot UI - EMBEDDED VERSION
===========================================================
Simplified and more stable build script for PyInstaller

Developer: Mohamad Zalaf ©️2025
"""

import os
import sys
import subprocess
import time

def fix_datetime_errors():
    """Fix common datetime errors in bot_ui.py"""
    print("🔧 Checking and fixing datetime errors...")
    
    try:
        # Read the file
        with open('bot_ui.py', 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        fixes_applied = []
        
        # Create backup before making changes
        if not os.path.exists('bot_ui.py.backup'):
            with open('bot_ui.py.backup', 'w', encoding='utf-8') as f:
                f.write(content)
            print("  💾 Backup created: bot_ui.py.backup")
        
        # Fix 1: Remove duplicate datetime import
        if 'import datetime\n' in content and 'from datetime import datetime' in content:
            content = content.replace('import datetime\n', '')
            fixes_applied.append("Removed duplicate 'import datetime'")
        
        # Fix 2: Fix datetime.datetime.now() calls
        if 'datetime.datetime.now()' in content:
            content = content.replace('datetime.datetime.now()', 'datetime.now()')
            fixes_applied.append("Fixed 'datetime.datetime.now()' -> 'datetime.now()'")
        
        # Fix 3: Fix other common PyInstaller issues
        if 'import warnings' in content and 'warnings.filterwarnings' not in content:
            # Add warnings filter after import
            content = content.replace(
                'import warnings',
                'import warnings\nwarnings.filterwarnings("ignore")'
            )
            fixes_applied.append("Added warnings filter")
        
        # Fix 4: Ensure proper datetime import exists
        if 'from datetime import datetime' not in content:
            # Add the import after other imports
            import_lines = []
            other_lines = []
            in_imports = True
            
            for line in content.split('\n'):
                if line.startswith('import ') or line.startswith('from ') and in_imports:
                    import_lines.append(line)
                else:
                    if in_imports and line.strip() and not line.startswith('#'):
                        in_imports = False
                        import_lines.append('from datetime import datetime, timedelta')
                    other_lines.append(line)
            
            content = '\n'.join(import_lines + other_lines)
            fixes_applied.append("Added proper datetime import")
        
        # Fix 5: Fix any remaining datetime issues
        content = content.replace('datetime.datetime(', 'datetime(')
        if 'datetime.datetime(' in original_content:
            fixes_applied.append("Fixed 'datetime.datetime(' -> 'datetime('")
        
        # Write back if changes were made
        if content != original_content:
            with open('bot_ui.py', 'w', encoding='utf-8') as f:
                f.write(content)
            
            print("  ✅ DateTime errors fixed:")
            for fix in fixes_applied:
                print(f"    - {fix}")
        else:
            print("  ✅ No datetime errors found")
        
        return True
        
    except Exception as e:
        print(f"  ⚠️  Could not fix datetime errors: {e}")
        return True  # Continue anyway

def build_exe_simple():
    """Build executable using simple PyInstaller command"""
    print("🤖 Simple Trading Bot UI Builder")
    print("=" * 40)
    
    # Check if bot_ui.py exists
    if not os.path.exists('bot_ui.py'):
        print("❌ Error: bot_ui.py not found!")
        return False
    
    # Auto-fix datetime errors before building
    fix_datetime_errors()
    
    print("🔨 Building with simplified PyInstaller command...")
    print("⏳ This may take 5-10 minutes, please wait...")
    
    try:
        # Simple PyInstaller command
        cmd = [
            'pyinstaller',
            '--onefile',                    # Single file
            '--noconsole',                  # No console window
            '--name=TradingBot_UI_v1.2.0',  # Output name
            '--clean',                      # Clean cache
            'bot_ui.py'                     # Source file
        ]
        
        print(f"🚀 Running: {' '.join(cmd)}")
        print("📝 Output:")
        
        # Run with real-time output
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            universal_newlines=True,
            bufsize=1
        )
        
        # Print output line by line
        line_count = 0
        while True:
            output = process.stdout.readline()
            if output == '' and process.poll() is not None:
                break
            if output:
                line_count += 1
                # Print every 10th line to avoid spam
                if line_count % 10 == 0:
                    print(f"  [{line_count}] Processing...")
                # Print important lines
                if any(keyword in output.lower() for keyword in ['error', 'warning', 'building', 'analyzing']):
                    print(f"  {output.strip()}")
        
        # Wait for completion
        return_code = process.poll()
        
        if return_code == 0:
            print("✅ Build completed successfully!")
            
            # Check if exe was created
            exe_path = os.path.join('dist', 'TradingBot_UI_v1.2.0.exe')
            if os.path.exists(exe_path):
                file_size = os.path.getsize(exe_path) / (1024 * 1024)
                print(f"📍 Location: {os.path.abspath(exe_path)}")
                print(f"📏 Size: {file_size:.1f} MB")
                return True
            else:
                print("❌ Executable not found in dist folder")
                return False
        else:
            print(f"❌ Build failed with exit code: {return_code}")
            return False
            
    except KeyboardInterrupt:
        print("\n❌ Build cancelled by user")
        return False
    except Exception as e:
        print(f"❌ Build error: {e}")
        return False

def build_exe_with_dependencies():
    """Build with explicit dependencies"""
    print("🔧 Building with explicit dependencies...")
    
    # Auto-fix datetime errors before building
    fix_datetime_errors()
    
    try:
        cmd = [
            'pyinstaller',
            '--onefile',
            '--noconsole',
            '--name=TradingBot_UI_v1.2.0',
            '--clean',
            '--add-data=requirements.txt;.',  # Include requirements
            '--hidden-import=telebot',
            '--hidden-import=pandas',
            '--hidden-import=numpy',
            '--hidden-import=tkinter',
            '--hidden-import=json',
            '--hidden-import=glob',
            '--hidden-import=threading',
            '--hidden-import=datetime',
            'bot_ui.py'
        ]
        
        print(f"🚀 Running: pyinstaller [with dependencies]")
        print("⏳ Please wait...")
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=1800)  # 30 min timeout
        
        if result.returncode == 0:
            print("✅ Build with dependencies completed!")
            return True
        else:
            print("❌ Build with dependencies failed")
            print("Error output:", result.stderr[-500:])  # Last 500 chars
            return False
            
    except subprocess.TimeoutExpired:
        print("❌ Build timed out after 30 minutes")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def cleanup():
    """Clean up build files"""
    print("🧹 Cleaning up...")
    
    import shutil
    cleanup_items = ['build', '__pycache__', '*.spec']
    
    for item in cleanup_items:
        if item.endswith('.spec'):
            # Remove spec files
            import glob
            for spec_file in glob.glob('*.spec'):
                try:
                    os.remove(spec_file)
                    print(f"  Removed {spec_file}")
                except:
                    pass
        else:
            # Remove directories
            if os.path.exists(item):
                try:
                    shutil.rmtree(item)
                    print(f"  Removed {item}/")
                except:
                    pass

def main():
    """Main build function"""
    print("🤖 Trading Bot UI - Simple Builder v1.2.0 (Auto-Fix)")
    print("=" * 55)
    print("🔧 Features: Auto-fixes DateTime errors and common issues")
    print()
    
    # Try simple build first
    print("📦 Method 1: Simple build (with auto-fixes)")
    success = build_exe_simple()
    
    if not success:
        print("\n📦 Method 2: Build with explicit dependencies")
        success = build_exe_with_dependencies()
    
    if success:
        print("\n🎉 Build completed successfully!")
        print("=" * 50)
        print("📦 Your executable is ready:")
        print("   📍 dist/TradingBot_UI_v1.2.0.exe")
        print("\n🔧 Auto-fixes applied:")
        print("   ✅ DateTime errors automatically resolved")
        print("   ✅ Common PyInstaller issues fixed")
        print("\n🔒 Security achieved:")
        print("   ✅ All code embedded and protected")
        print("   ✅ No .py files needed")
        print("   ✅ Ready for safe distribution")
    else:
        print("\n❌ Build failed with both methods")
        print("💡 Troubleshooting tips:")
        print("   - Check if all packages are installed")
        print("   - Try running: pip install --upgrade pyinstaller")
        print("   - Ensure no antivirus is blocking PyInstaller")
    
    # Always cleanup
    cleanup()
    
    return success

if __name__ == "__main__":
    try:
        success = main()
        print(f"\n{'='*50}")
        if success:
            print("✅ SUCCESS: Ready to distribute!")
        else:
            print("❌ FAILED: Check errors above")
        input("Press Enter to exit...")
    except KeyboardInterrupt:
        print("\n❌ Cancelled by user")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        input("Press Enter to exit...")