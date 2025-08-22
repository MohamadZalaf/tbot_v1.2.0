#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
🔨 Build Script for Trading Bot UI v1.2.0
=========================================
This script builds a standalone executable for the Trading Bot UI
with all dependencies embedded and no external file requirements.

Features:
- Automated PyInstaller build process
- Dependency checking
- Error handling and logging
- Optimized executable creation
- Arabic interface support

Developer: Mohamad Zalaf ©️2025
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path

def check_dependencies():
    """Check if all required dependencies are installed"""
    required_packages = [
        'pyinstaller',
        'telebot',
        'pandas', 
        'numpy',
        'google-generativeai',
        'Pillow'
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            if package == 'telebot':
                import telebot
            elif package == 'pyinstaller':
                import PyInstaller
            elif package == 'pandas':
                import pandas
            elif package == 'numpy':
                import numpy

            elif package == 'google-generativeai':
                import google.generativeai
            elif package == 'Pillow':
                import PIL
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        print("❌ المكتبات التالية مفقودة:")
        for package in missing_packages:
            print(f"   - {package}")
        print("\nيرجى تثبيتها باستخدام:")
        print(f"pip install {' '.join(missing_packages)}")
        return False
    
    print("✅ جميع المكتبات المطلوبة متوفرة")
    return True

def clean_build_directories():
    """Clean previous build directories"""
    directories_to_clean = ['build', 'dist', '__pycache__']
    
    for directory in directories_to_clean:
        if os.path.exists(directory):
            try:
                shutil.rmtree(directory)
                print(f"🧹 تم تنظيف مجلد: {directory}")
            except Exception as e:
                print(f"⚠️  تحذير: فشل في تنظيف {directory}: {e}")

def create_version_info():
    """Create version info file for the executable"""
    version_info_content = """# UTF-8
#
# For more details about fixed file info 'ffi' see:
# http://msdn.microsoft.com/en-us/library/ms646997.aspx
VSVersionInfo(
  ffi=FixedFileInfo(
    # filevers and prodvers should be always a tuple with four items: (1, 2, 3, 4)
    # Set not needed items to zero 0.
    filevers=(1, 2, 0, 0),
    # prodvers should be always a tuple with four items: (1, 2, 3, 4)
    # Set not needed items to zero 0.
    prodvers=(1, 2, 0, 0),
    # Contains a bitmask that specifies the valid bits 'flags'r
    mask=0x3f,
    # Contains a bitmask that specifies the Boolean attributes of the file.
    flags=0x0,
    # The operating system for which this file was designed.
    # 0x4 - NT and there is no need to change it.
    OS=0x40004,
    # The general type of file.
    # 0x1 - the file is an application.
    fileType=0x1,
    # The function of the file.
    # 0x0 - the function is not defined for this fileType
    subtype=0x0,
    # Creation date and time stamp.
    date=(0, 0)
  ),
  kids=[
    StringFileInfo(
      [
      StringTable(
        u'040904B0',
        [        StringStruct(u'CompanyName', u'Mohamad Zalaf ©2025'),
        StringStruct(u'FileDescription', u'بوت التداول المتقدم - واجهة التحكم'),
        StringStruct(u'FileVersion', u'1.2.0.0'),
        StringStruct(u'InternalName', u'TradingBot'),
        StringStruct(u'LegalCopyright', u'Copyright © 2025 Mohamad Zalaf'),
        StringStruct(u'OriginalFilename', u'TradingBot 1.2.0.exe'),
        StringStruct(u'ProductName', u'Advanced Trading Bot UI Controller'),
        StringStruct(u'ProductVersion', u'1.2.0.0')])
      ]),
    VarFileInfo([VarStruct(u'Translation', [1033, 1200])])
  ]
)"""
    
    with open('version_info.txt', 'w', encoding='utf-8') as f:
        f.write(version_info_content)
    
    print("📝 تم إنشاء ملف معلومات الإصدار")

def create_icon():
    """Create icon for the executable"""
    try:
        from PIL import Image, ImageDraw
        
        # إنشاء صورة 256x256 بخلفية زرقاء
        size = 256
        img = Image.new('RGBA', (size, size), (33, 150, 243, 255))
        draw = ImageDraw.Draw(img)
        
        # رسم دائرة خارجية
        margin = 20
        draw.ellipse([margin, margin, size-margin, size-margin], 
                    fill=(25, 118, 210, 255), outline=(13, 71, 161, 255), width=4)
        
        # رسم شكل بوت بسيط
        # رسم مربع للرأس
        head_size = 80
        head_x = (size - head_size) // 2
        head_y = size // 2 - 50
        draw.rectangle([head_x, head_y, head_x + head_size, head_y + head_size], 
                      fill=(255, 255, 255, 255), outline=(200, 200, 200, 255), width=3)
        
        # رسم العيون
        eye_size = 12
        eye1_x = head_x + 20
        eye2_x = head_x + head_size - 20 - eye_size
        eye_y = head_y + 25
        draw.ellipse([eye1_x, eye_y, eye1_x + eye_size, eye_y + eye_size], 
                    fill=(33, 150, 243, 255))
        draw.ellipse([eye2_x, eye_y, eye2_x + eye_size, eye_y + eye_size], 
                    fill=(33, 150, 243, 255))
        
        # رسم الفم
        mouth_y = head_y + 50
        draw.rectangle([head_x + 25, mouth_y, head_x + head_size - 25, mouth_y + 6], 
                      fill=(33, 150, 243, 255))
        
        # رسم الجسم
        body_width = 60
        body_height = 40
        body_x = (size - body_width) // 2
        body_y = head_y + head_size + 10
        draw.rectangle([body_x, body_y, body_x + body_width, body_y + body_height], 
                      fill=(255, 255, 255, 255), outline=(200, 200, 200, 255), width=3)
        
        # حفظ الأيقونة
        img.save('icon.ico', format='ICO', sizes=[(256, 256), (128, 128), (64, 64), (32, 32), (16, 16)])
        print("🎨 تم إنشاء ملف icon.ico بنجاح")
        return True
        
    except Exception as e:
        print(f"⚠️ فشل في إنشاء الأيقونة: {e}")
        return False

def build_executable():
    """Build the executable using PyInstaller"""
    print("🔨 بدء عملية البناء...")
    
    # التحقق من وجود الأيقونة أو إنشاؤها
    if not os.path.exists('icon.ico'):
        print("🎨 إنشاء أيقونة البوت...")
        create_icon()
    else:
        print("🎨 تم العثور على ملف icon.ico موجود")
    
    # PyInstaller command with optimized settings
    cmd = [
        'pyinstaller',
        '--onefile',                    # Single executable file
        '--windowed',                   # No console window
        '--name=TradingBot 1.2.0',   # Executable name
        '--distpath=dist',              # Output directory
        '--workpath=build',             # Work directory
        '--clean',                      # Clean cache
        '--noconfirm',                  # Don't ask for confirmation
        '--optimize=2',                 # Optimize bytecode
        '--version-file=version_info.txt',  # Version info
        
        # Hidden imports for all required modules
        '--hidden-import=telebot',
        '--hidden-import=telebot.apihelper', 
        '--hidden-import=telebot.types',
        '--hidden-import=pandas',
        '--hidden-import=numpy',
        '--hidden-import=google.generativeai',
        '--hidden-import=google.generativeai.types',
        '--hidden-import=google.generativeai.types.citation_types',
        '--hidden-import=google.generativeai.caching',
        '--hidden-import=google.ai.generativelanguage',
        '--hidden-import=logging.handlers',
        '--hidden-import=tkinter.messagebox',
        '--hidden-import=tkinter.scrolledtext',
        '--hidden-import=tkinter.ttk',
        '--hidden-import=tkinter.simpledialog',
        
        # Additional hidden imports for google-generativeai
        '--hidden-import=google.ai.generativelanguage',
        '--hidden-import=google.ai.generativelanguage_v1beta',
        '--hidden-import=google.generativeai.string_utils',
        '--hidden-import=grpc',
        '--hidden-import=grpcio',
        '--hidden-import=google.protobuf',
        '--hidden-import=google.auth',
        '--hidden-import=google.auth.transport',
        '--hidden-import=google.auth.transport.requests',
        
        # Collect all submodules for problematic packages
        '--collect-all=google.generativeai',
        '--collect-all=google.ai.generativelanguage',
        
        # Exclude unnecessary modules
        '--exclude-module=matplotlib',
        '--exclude-module=scipy',
        '--exclude-module=jupyter',
        '--exclude-module=notebook',
        '--exclude-module=IPython',
        '--exclude-module=pytest',
        '--exclude-module=unittest',
        
        'bot_ui.py'  # Main script
    ]
    
    # إضافة الأيقونة إذا كانت موجودة
    if os.path.exists('icon.ico'):
        cmd.insert(-1, '--icon=icon.ico')
        print("🎨 سيتم استخدام أيقونة icon.ico")
    else:
        print("⚠️ لم يتم العثور على icon.ico - سيتم استخدام الأيقونة الافتراضية")
    
    try:
        print("⚙️  تشغيل PyInstaller...")
        result = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8')
        
        if result.returncode == 0:
            print("✅ تم بناء الملف التنفيذي بنجاح!")
            
            # Check if executable was created
            exe_path = os.path.join('dist', 'TradingBot 1.2.0.exe')
            exe_path_linux = os.path.join('dist', 'TradingBot 1.2.0')
            # Check both Windows and Linux executable paths
            if os.path.exists(exe_path):
                current_exe_path = exe_path
            elif os.path.exists(exe_path_linux):
                current_exe_path = exe_path_linux
                # Rename to add .exe extension
                new_exe_path = exe_path_linux + '.exe'
                os.rename(exe_path_linux, new_exe_path)
                current_exe_path = new_exe_path
            else:
                current_exe_path = None
            
            if current_exe_path:
                file_size = os.path.getsize(current_exe_path) / (1024 * 1024)  # Size in MB
                print(f"📁 الملف التنفيذي: {current_exe_path}")
                print(f"📏 حجم الملف: {file_size:.1f} MB")
                print(f"🎯 الملف جاهز للاستخدام!")
                
                # Create a simple README for the executable
                readme_content = """
🤖 بوت التداول المتقدم v1.2.0 - واجهة التحكم
===========================================

📋 معلومات الملف التنفيذي:
• الاسم: TradingBot 1.2.0.exe
• الإصدار: 1.2.0
• المطور: Mohamad Zalaf ©2025

🚀 طريقة الاستخدام:
1. شغل الملف التنفيذي TradingBot 1.2.0.exe
2. أدخل كلمة المرور: 041768454
3. استخدم واجهة التحكم لإدارة البوت

🔧 الميزات المتوفرة:
• تشغيل وإيقاف البوت
• إدارة المستخدمين (حظر/إلغاء حظر)
• إعدادات مفاتيح Gemini API
• إعدادات اتصال MetaTrader5
• مراقبة عدد المستخدمين في الوقت الفعلي

📁 الملفات المطلوبة:
• لا توجد ملفات خارجية مطلوبة
• جميع الأكواد مدمجة في الملف التنفيذي
• ملفات JSON ستُنشأ تلقائياً عند الحاجة

⚠️ ملاحظات مهمة:
• تأكد من تثبيت MetaTrader5 للاستفادة من جميع الميزات
• احتفظ بنسخة احتياطية من بيانات المستخدمين
• كلمة مرور الواجهة: 041768454
• كلمة مرور البوت: tra12345678

🆘 الدعم:
في حالة وجود مشاكل، راجع ملف bot.log للتفاصيل
"""
                
                with open('dist/README_Arabic.txt', 'w', encoding='utf-8') as f:
                    f.write(readme_content)
                
                print("📖 تم إنشاء ملف README باللغة العربية")
                return True
            else:
                print("❌ فشل في العثور على الملف التنفيذي")
                return False
        else:
            print("❌ فشل في بناء الملف التنفيذي:")
            print(result.stderr)
            return False
            
    except Exception as e:
        print(f"❌ خطأ في عملية البناء: {e}")
        return False

def main():
    """Main build function"""
    print("🤖 بناء واجهة بوت التداول المتقدم v1.2.0")
    print("=" * 50)
    
    # Check if bot_ui.py exists
    if not os.path.exists('bot_ui.py'):
        print("❌ ملف bot_ui.py غير موجود!")
        return False
    
    # Check dependencies
    print("🔍 فحص المكتبات المطلوبة...")
    if not check_dependencies():
        return False
    
    # Clean previous builds
    print("🧹 تنظيف ملفات البناء السابقة...")
    clean_build_directories()
    
    # Create version info
    print("📝 إنشاء معلومات الإصدار...")
    create_version_info()
    
    # Build executable
    print("🔨 بناء الملف التنفيذي...")
    success = build_executable()
    
    if success:
        print("\n" + "=" * 50)
        print("🎉 تم الانتهاء من البناء بنجاح!")
        print("📁 الملف التنفيذي متوفر في مجلد: dist/")
        print("🚀 يمكنك الآن تشغيل: TradingBot 1.2.0.exe")
        print("=" * 50)
    else:
        print("\n" + "=" * 50)
        print("❌ فشل في بناء الملف التنفيذي")
        print("📋 راجع الأخطاء أعلاه لمزيد من التفاصيل")
        print("=" * 50)
    
    return success

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n🛑 تم إلغاء عملية البناء بواسطة المستخدم")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ خطأ غير متوقع: {e}")
        sys.exit(1)