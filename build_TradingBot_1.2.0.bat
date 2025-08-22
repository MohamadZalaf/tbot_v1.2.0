@echo off
chcp 65001 >nul
echo.
echo ========================================
echo 🤖 بناء بوت التداول v1.2.0
echo ========================================
echo.

REM التحقق من وجود الملفات المطلوبة
echo 📋 فحص الملفات المطلوبة...

if not exist "bot_ui.py" (
    echo ❌ bot_ui.py - غير موجود
    pause
    exit /b 1
) else (
    echo ✅ bot_ui.py - موجود
)

if not exist "tbot_v1.2.0.py" (
    echo ❌ tbot_v1.2.0.py - غير موجود
    pause
    exit /b 1
) else (
    echo ✅ tbot_v1.2.0.py - موجود
)

if not exist "config.py" (
    echo ❌ config.py - غير موجود
    pause
    exit /b 1
) else (
    echo ✅ config.py - موجود
)

REM إنشاء الأيقونة إذا لم تكن موجودة
if not exist "icon.ico" (
    echo 🎨 إنشاء ملف الأيقونة...
    python3 create_simple_icon.py
    if not exist "icon.ico" (
        echo ⚠️ فشل في إنشاء الأيقونة - سيتم البناء بدونها
    )
) else (
    echo ✅ icon.ico - موجود
)

echo.
echo 🔧 بدء عملية البناء...
echo.

REM تنظيف الملفات القديمة
if exist "dist\TradingBot_1.2.0.exe" (
    echo 🗑️ حذف الملف التنفيذي القديم...
    del "dist\TradingBot_1.2.0.exe"
)

if exist "build" (
    echo 🗑️ حذف مجلد البناء القديم...
    rmdir /s /q "build"
)

REM بناء التطبيق
echo 🚀 تشغيل PyInstaller...
pyinstaller build_TradingBot_1.2.0.spec

if exist "dist\TradingBot_1.2.0.exe" (
    echo.
    echo ✅ تم بناء TradingBot_1.2.0.exe بنجاح!
    echo 📁 الملف موجود في: dist\TradingBot_1.2.0.exe
    echo.
    echo 📊 معلومات الملف:
    dir "dist\TradingBot_1.2.0.exe"
    echo.
    echo 🎉 البناء مكتمل بنجاح!
) else (
    echo.
    echo ❌ فشل في بناء الملف التنفيذي
    echo 📋 يرجى مراجعة رسائل الخطأ أعلاه
)

echo.
echo تنظيف الملفات المؤقتة...
if exist "create_simple_icon.py" del "create_simple_icon.py"
if exist "create_icon.py" del "create_icon.py"

echo.
pause