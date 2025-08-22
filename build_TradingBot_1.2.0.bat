@echo off
chcp 65001 >nul
echo.
echo ========================================
echo Building Trading Bot v1.2.0
echo ========================================
echo.

REM Check for required files
echo Checking required files...

if not exist "bot_ui.py" (
    echo [ERROR] bot_ui.py - not found
    pause
    exit /b 1
) else (
    echo [OK] bot_ui.py - found
)

if not exist "tbot_v1.2.0.py" (
    echo [ERROR] tbot_v1.2.0.py - not found
    pause
    exit /b 1
) else (
    echo [OK] tbot_v1.2.0.py - found
)

if not exist "config.py" (
    echo [ERROR] config.py - not found
    pause
    exit /b 1
) else (
    echo [OK] config.py - found
)

REM Create icon if not exists
if not exist "icon.ico" (
    echo Creating icon file...
    python3 create_simple_icon.py
    if not exist "icon.ico" (
        echo [WARNING] Failed to create icon - building without it
    )
) else (
    echo [OK] icon.ico - found
)

echo.
echo Starting build process...
echo.

REM Clean old files
if exist "dist\TradingBot_1.2.0.exe" (
    echo Deleting old executable...
    del "dist\TradingBot_1.2.0.exe"
)

if exist "build" (
    echo Deleting old build folder...
    rmdir /s /q "build"
)

REM Build application
echo Running PyInstaller...
pyinstaller build_TradingBot_1.2.0.spec

if exist "dist\TradingBot_1.2.0.exe" (
    echo.
    echo [SUCCESS] TradingBot_1.2.0.exe built successfully!
    echo [INFO] File location: dist\TradingBot_1.2.0.exe
    echo.
    echo File information:
    dir "dist\TradingBot_1.2.0.exe"
    echo.
    echo [SUCCESS] Build completed successfully!
) else (
    echo.
    echo [ERROR] Failed to build executable
    echo [INFO] Please review error messages above
)

echo.
echo Cleaning temporary files...
if exist "create_simple_icon.py" del "create_simple_icon.py"
if exist "create_icon.py" del "create_icon.py"

echo.
pause