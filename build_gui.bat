@echo off
chcp 65001 >nul
title Building Trading Bot UI v1.2.0

echo.
echo 🤖 بناء واجهة بوت التداول المتقدم v1.2.0
echo ==========================================
echo.

REM Check if Python is available
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Python غير متوفر في النظام
    echo يرجى تثبيت Python أولاً
    pause
    exit /b 1
)

REM Check if bot_ui.py exists
if not exist "bot_ui.py" (
    echo ❌ ملف bot_ui.py غير موجود!
    pause
    exit /b 1
)

echo ✅ تم العثور على ملف bot_ui.py
echo.

REM Run the build script
echo 🔨 بدء عملية البناء...
python build_gui.py

if %errorlevel% equ 0 (
    echo.
    echo 🎉 تم الانتهاء من البناء بنجاح!
    echo.
    echo 📁 الملف التنفيذي متوفر في: dist\TradingBotUI_v1.2.0.exe
    echo 📖 ملف التعليمات متوفر في: dist\README_Arabic.txt
    echo.
    echo 🚀 يمكنك الآن تشغيل الملف التنفيذي
    echo.
    
    REM Ask if user wants to open the dist folder
    set /p open_folder="هل تريد فتح مجلد الملف التنفيذي؟ (y/n): "
    if /i "%open_folder%"=="y" (
        start explorer dist
    )
) else (
    echo.
    echo ❌ فشل في بناء الملف التنفيذي
    echo راجع الأخطاء أعلاه لمزيد من التفاصيل
    echo.
)

echo.
pause