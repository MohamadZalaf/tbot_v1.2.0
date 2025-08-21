@echo off
echo 🤖 Trading Bot UI - Basic Builder
echo ===============================
echo Building executable with basic PyInstaller command...
echo.

REM Check if bot_ui.py exists
if not exist "bot_ui.py" (
    echo ❌ Error: bot_ui.py not found!
    pause
    exit /b 1
)

echo 🔨 Running PyInstaller...
echo Please wait 5-10 minutes...
echo.

REM Basic PyInstaller command
pyinstaller --onefile --noconsole --name=TradingBot_UI_v1.2.0 bot_ui.py

REM Check if successful
if exist "dist\TradingBot_UI_v1.2.0.exe" (
    echo.
    echo ✅ Build completed successfully!
    echo 📍 Location: dist\TradingBot_UI_v1.2.0.exe
    echo.
    echo 🔒 Your bot code is now protected and embedded!
    echo 📦 You can distribute the .exe file safely.
) else (
    echo.
    echo ❌ Build failed - executable not found
    echo 💡 Try installing missing packages or check for errors above
)

echo.
echo 🧹 Cleaning up temporary files...
if exist "build" rmdir /s /q "build"
if exist "__pycache__" rmdir /s /q "__pycache__"
if exist "*.spec" del "*.spec"

echo.
echo ============================================
pause