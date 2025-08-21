@echo off
chcp 65001 > nul
title Trading Bot v1.2.0 - التثبيت الآلي

echo.
echo ====================================================================
echo    🤖 بوت التداول المتقدم v1.2.0 - برنامج التثبيت الآلي
echo ====================================================================
echo.
echo 🚀 بدء عملية التثبيت...
echo.

:: التحقق من وجود Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Python غير مثبت على النظام!
    echo 📥 يرجى تحميل وتثبيت Python من: https://python.org
    echo.
    pause
    exit /b 1
)

echo ✅ تم العثور على Python
python --version

echo.
echo 📦 تثبيت المكتبات المطلوبة...
echo.

:: تثبيت المكتبات
pip install --upgrade pip
if %errorlevel% neq 0 (
    echo ⚠️ فشل في تحديث pip
    goto :install_requirements
)

:install_requirements
echo.
echo 🔄 تثبيت متطلبات البوت...
pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo ❌ فشل في تثبيت بعض المكتبات!
    echo 🔧 جاري المحاولة مرة أخرى...
    echo.
    
    :: تثبيت المكتبات الأساسية واحدة بواحدة
    pip install MetaTrader5
    pip install google-generativeai
    pip install pyTelegramBotAPI
    pip install pandas
    pip install numpy
    pip install matplotlib
    pip install plotly
    pip install ta
    pip install requests
    pip install beautifulsoup4
    pip install Pillow
    pip install opencv-python
    pip install scipy
    pip install seaborn
    
    echo.
    echo ⚠️ إذا واجهت مشاكل، تأكد من:
    echo   • وجود اتصال إنترنت مستقر
    echo   • تشغيل Terminal كمسؤول (Administrator)
    echo   • تحديث Python لآخر إصدار
)

echo.
echo 📁 إنشاء مجلدات البيانات...
if not exist "trading_data" mkdir trading_data
if not exist "trading_data\user_feedback" mkdir trading_data\user_feedback
if not exist "trading_data\trade_logs" mkdir trading_data\trade_logs
if not exist "logs" mkdir logs

echo ✅ تم إنشاء مجلدات البيانات

echo.
echo 🔧 التحقق من متطلبات النظام...
echo.

:: التحقق من MetaTrader5
echo 🔍 البحث عن MetaTrader5...
if exist "C:\Program Files\MetaTrader 5\terminal64.exe" (
    echo ✅ تم العثور على MetaTrader5 في: C:\Program Files\MetaTrader 5\
) else if exist "C:\Program Files (x86)\MetaTrader 5\terminal.exe" (
    echo ✅ تم العثور على MetaTrader5 في: C:\Program Files (x86)\MetaTrader 5\
) else (
    echo ⚠️ لم يتم العثور على MetaTrader5
    echo 📥 يرجى تحميل وتثبيت MT5 من: https://www.metatrader5.com
)

echo.
echo ====================================================================
echo                        ✅ تم الانتهاء من التثبيت!
echo ====================================================================
echo.
echo 📋 خطوات ما بعد التثبيت:
echo.
echo 1️⃣  افتح ملف tbot_v1.2.0.py
echo 2️⃣  عدّل GEMINI_API_KEY (ضع مفتاح Gemini AI الخاص بك)
echo 3️⃣  عدّل BOT_TOKEN (ضع رمز بوت Telegram الخاص بك)
echo 4️⃣  تأكد من تشغيل MetaTrader5 وتسجيل الدخول
echo 5️⃣  شغّل البوت باستخدام: python tbot_v1.2.0.py
echo.
echo 🔗 روابط مفيدة:
echo   • إنشاء بوت Telegram: https://t.me/BotFather
echo   • الحصول على Gemini API: https://ai.google.dev
echo   • تحميل MetaTrader5: https://www.metatrader5.com
echo.
echo 💡 نصيحة: اقرأ ملف README.md للحصول على دليل مفصل
echo.
echo ====================================================================
echo.
pause