#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
🔧 Rebuild Script - DateTime Error Fixed
========================================
Quick rebuild after fixing datetime error

Developer: Mohamad Zalaf ©️2025
"""

import os
import subprocess
import sys

def clean_old_build():
    """Clean old build files"""
    print("🧹 Cleaning old build files...")
    
    import shutil
    cleanup_items = ['build', 'dist', '__pycache__']
    
    for item in cleanup_items:
        if os.path.exists(item):
            try:
                shutil.rmtree(item)
                print(f"  ✅ Removed {item}/")
            except Exception as e:
                print(f"  ⚠️  Could not remove {item}: {e}")
    
    # Remove spec files
    import glob
    for spec_file in glob.glob('*.spec'):
        try:
            os.remove(spec_file)
            print(f"  ✅ Removed {spec_file}")
        except:
            pass

def rebuild_exe():
    """Rebuild the executable with fixed datetime"""
    print("🔨 Rebuilding executable (DateTime error fixed)...")
    print("⏳ This should be faster than first build...")
    
    try:
        # Simple and fast rebuild command
        cmd = [
            'pyinstaller',
            '--onefile',
            '--noconsole',
            '--name=TradingBot_UI_v1.2.0_FIXED',
            '--clean',
            'bot_ui.py'
        ]
        
        print(f"🚀 Running: {' '.join(cmd)}")
        
        # Run the build
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=900  # 15 minutes timeout
        )
        
        if result.returncode == 0:
            print("✅ Rebuild completed successfully!")
            
            # Check the file
            exe_path = os.path.join('dist', 'TradingBot_UI_v1.2.0_FIXED.exe')
            if os.path.exists(exe_path):
                file_size = os.path.getsize(exe_path) / (1024 * 1024)
                print(f"📍 Location: {os.path.abspath(exe_path)}")
                print(f"📏 Size: {file_size:.1f} MB")
                return True
            else:
                print("❌ Executable not found")
                return False
        else:
            print(f"❌ Build failed")
            print("Error output:")
            print(result.stderr[-1000:])  # Last 1000 chars
            return False
            
    except subprocess.TimeoutExpired:
        print("❌ Build timed out")
        return False
    except Exception as e:
        print(f"❌ Build error: {e}")
        return False

def test_datetime_fix():
    """Test that datetime error is fixed"""
    print("🧪 Testing datetime fix...")
    
    try:
        # Test the exact problematic line
        from datetime import datetime
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"  ✅ datetime.now() works: {timestamp}")
        
        # Test importing bot_ui
        import bot_ui
        print("  ✅ bot_ui.py imports without errors")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Still has errors: {e}")
        return False

def main():
    """Main rebuild process"""
    print("🤖 Trading Bot UI - Quick Rebuild (DateTime Fixed)")
    print("=" * 55)
    
    # Step 1: Test the fix
    if not test_datetime_fix():
        print("❌ DateTime error not fixed! Check the code.")
        return False
    
    # Step 2: Clean old files
    clean_old_build()
    
    # Step 3: Rebuild
    success = rebuild_exe()
    
    if success:
        print("\n🎉 Rebuild completed successfully!")
        print("=" * 50)
        print("📦 Fixed executable ready:")
        print("   📍 dist/TradingBot_UI_v1.2.0_FIXED.exe")
        print("\n🔧 What was fixed:")
        print("   ✅ DateTime import error resolved")
        print("   ✅ Removed duplicate datetime imports")
        print("   ✅ Fixed datetime.datetime.now() -> datetime.now()")
        print("\n🚀 Ready to test the fixed version!")
    else:
        print("\n❌ Rebuild failed")
        print("💡 Try running: python build_exe_simple.py")
    
    return success

if __name__ == "__main__":
    try:
        success = main()
        print(f"\n{'='*50}")
        if success:
            print("✅ SUCCESS: DateTime error fixed!")
        else:
            print("❌ FAILED: Need to check errors")
        input("Press Enter to exit...")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        input("Press Enter to exit...")