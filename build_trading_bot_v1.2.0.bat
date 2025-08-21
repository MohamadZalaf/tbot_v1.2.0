@echo off
chcp 65001 >nul
setlocal EnableDelayedExpansion

REM ===================================================================
REM 🏗️ Trading Bot Builder v1.2.0 - BAT Script
REM ===================================================================
REM Batch script to build Trading_tbot_v1.2.0.exe
REM 
REM Features:
REM - Automatic dependency installation
REM - File verification
REM - Error handling
REM - Progress display
REM - Build verification
REM 
REM Developer: Enhanced Builder System
REM Compatible with: tbot_v1.2.0.py, config.py, icon.ico
REM ===================================================================

title Trading Bot Builder v1.2.0

echo.
echo ============================================================
echo 🏗️  Trading Bot EXE Builder v1.2.0 - BAT Script
echo ============================================================
echo.

REM Check if Python is installed
echo 🐍 Checking Python installation...
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Error: Python is not installed or not in PATH
    echo    Please install Python 3.7+ from https://python.org
    pause
    exit /b 1
)

for /f "tokens=2" %%i in ('python --version 2^>^&1') do set PYTHON_VERSION=%%i
echo ✅ Python version: %PYTHON_VERSION%

REM Check if required files exist
echo.
echo 📁 Checking required files...

set MISSING_FILES=
if not exist "tbot_v1.2.0.py" (
    echo ❌ tbot_v1.2.0.py - Not found
    set MISSING_FILES=!MISSING_FILES! tbot_v1.2.0.py
)

if not exist "config.py" (
    echo ❌ config.py - Not found
    set MISSING_FILES=!MISSING_FILES! config.py
)

if not exist "icon.ico" (
    echo ⚠️  icon.ico - Not found (will build without icon)
) else (
    echo ✅ icon.ico found
)

if exist "tbot_v1.2.0.py" (
    for %%F in ("tbot_v1.2.0.py") do (
        echo ✅ tbot_v1.2.0.py (%%~zF bytes)
    )
)

if exist "config.py" (
    for %%F in ("config.py") do (
        echo ✅ config.py (%%~zF bytes)
    )
)

if not "%MISSING_FILES%"=="" (
    echo.
    echo ❌ Missing required files:%MISSING_FILES%
    pause
    exit /b 1
)

echo ✅ All required files found

REM Install PyInstaller
echo.
echo 🔧 Installing/Upgrading PyInstaller...
python -m pip install --upgrade pyinstaller
if errorlevel 1 (
    echo ❌ Failed to install PyInstaller
    pause
    exit /b 1
)
echo ✅ PyInstaller installation completed

REM Install dependencies
echo.
echo 📦 Installing dependencies...
echo    This may take a few minutes...

set DEPENDENCIES=telebot pandas numpy MetaTrader5 google-generativeai requests pytz python-dateutil

for %%D in (%DEPENDENCIES%) do (
    echo    Installing %%D...
    python -m pip install --upgrade %%D >nul 2>&1
    if errorlevel 1 (
        echo    ⚠️  %%D installation failed (may already exist)
    ) else (
        echo    ✅ %%D installed
    )
)

echo ✅ Dependencies installation completed

REM Clean previous builds
echo.
echo 🧹 Cleaning previous builds...

if exist "build" (
    rmdir /s /q "build" >nul 2>&1
    echo ✅ Removed build directory
)

if exist "dist" (
    rmdir /s /q "dist" >nul 2>&1
    echo ✅ Removed dist directory
)

if exist "*.spec" (
    del "*.spec" >nul 2>&1
    echo ✅ Removed spec files
)

REM Build executable
echo.
echo 🔨 Building executable...
echo    This may take several minutes, please wait...

set BUILD_START=%TIME%

REM Create PyInstaller command
set PYINSTALLER_CMD=python -m PyInstaller --onefile --console
set PYINSTALLER_CMD=%PYINSTALLER_CMD% --name "Trading_tbot_v1.2.0"
set PYINSTALLER_CMD=%PYINSTALLER_CMD% --add-data "config.py;."

REM Add icon if exists
if exist "icon.ico" (
    set PYINSTALLER_CMD=%PYINSTALLER_CMD% --icon "icon.ico"
)

REM Add hidden imports
set PYINSTALLER_CMD=%PYINSTALLER_CMD% --hidden-import telebot
set PYINSTALLER_CMD=%PYINSTALLER_CMD% --hidden-import pandas
set PYINSTALLER_CMD=%PYINSTALLER_CMD% --hidden-import numpy
set PYINSTALLER_CMD=%PYINSTALLER_CMD% --hidden-import MetaTrader5
set PYINSTALLER_CMD=%PYINSTALLER_CMD% --hidden-import google.generativeai
set PYINSTALLER_CMD=%PYINSTALLER_CMD% --hidden-import requests
set PYINSTALLER_CMD=%PYINSTALLER_CMD% --hidden-import pytz
set PYINSTALLER_CMD=%PYINSTALLER_CMD% --hidden-import dateutil

REM Exclude unnecessary modules
set PYINSTALLER_CMD=%PYINSTALLER_CMD% --exclude-module matplotlib
set PYINSTALLER_CMD=%PYINSTALLER_CMD% --exclude-module scipy
set PYINSTALLER_CMD=%PYINSTALLER_CMD% --exclude-module IPython

REM Add main file
set PYINSTALLER_CMD=%PYINSTALLER_CMD% "tbot_v1.2.0.py"

REM Run PyInstaller
echo Running: %PYINSTALLER_CMD%
%PYINSTALLER_CMD%

if errorlevel 1 (
    echo ❌ Build failed!
    pause
    exit /b 1
)

set BUILD_END=%TIME%
echo ✅ Build completed

REM Verify build
echo.
echo 🔍 Verifying build...

if not exist "dist\Trading_tbot_v1.2.0.exe" (
    echo ❌ Executable not found in dist directory
    pause
    exit /b 1
)

for %%F in ("dist\Trading_tbot_v1.2.0.exe") do (
    set FILE_SIZE=%%~zF
    set /a FILE_SIZE_MB=!FILE_SIZE!/1024/1024
    echo ✅ Executable created: dist\Trading_tbot_v1.2.0.exe
    echo 📊 File size: !FILE_SIZE! bytes (!FILE_SIZE_MB! MB)
)

REM Copy additional files
echo.
echo 📋 Copying additional files...

if exist "config.py" (
    copy "config.py" "dist\" >nul 2>&1
    echo ✅ Copied config.py
)

if not exist "dist\trading_data" (
    mkdir "dist\trading_data" >nul 2>&1
    echo ✅ Created trading_data directory
)

REM Create README
echo.
echo 📄 Creating README...

(
echo # Trading Bot v1.2.0 - Executable Package
echo.
echo ## 📦 Package Contents
echo - Trading_tbot_v1.2.0.exe - Main executable file
echo - config.py - Configuration file
echo - trading_data/ - Data directory ^(created automatically^)
echo.
echo ## 🚀 How to Run
echo 1. Double-click Trading_tbot_v1.2.0.exe
echo 2. Or run from command line: Trading_tbot_v1.2.0.exe
echo.
echo ## ⚙️ Requirements
echo - Windows 10/11 ^(64-bit^)
echo - Internet connection for Telegram API
echo - MetaTrader 5 ^(for trading data^)
echo.
echo ## 🔧 Configuration
echo Edit config.py to change:
echo - Telegram Bot Token
echo - Gemini AI API Key
echo - Other settings
echo.
echo ## 📝 Notes
echo - First run may take longer ^(Windows Defender scan^)
echo - Keep config.py in the same directory as the exe
echo - The bot will create trading_data folder automatically
echo.
echo ## 🆘 Troubleshooting
echo - If antivirus blocks the file, add it to exceptions
echo - Run as administrator if needed
echo - Check internet connection
echo - Verify config.py settings
echo.
echo Built on: %DATE% %TIME%
echo Builder: Trading Bot Builder v1.2.0 ^(BAT Script^)
) > "dist\README.txt"

echo ✅ Created README.txt

REM Final summary
echo.
echo ============================================================
echo 🎉 BUILD COMPLETED SUCCESSFULLY!
echo ============================================================
echo.
echo 📦 Executable: dist\Trading_tbot_v1.2.0.exe

if exist "dist\Trading_tbot_v1.2.0.exe" (
    for %%F in ("dist\Trading_tbot_v1.2.0.exe") do (
        set FILE_SIZE=%%~zF
        set /a FILE_SIZE_MB=!FILE_SIZE!/1024/1024
        echo 📊 Size: !FILE_SIZE! bytes ^(!FILE_SIZE_MB! MB^)
    )
)

echo 📁 Output directory: dist\
echo.
echo 🚀 Ready to distribute!
echo.
echo 💡 Tips:
echo    • Test the executable before distribution
echo    • Include config.py with your bot token
echo    • The exe includes all dependencies
echo    • First run may trigger antivirus scan
echo.

REM Ask if user wants to open dist folder
set /p OPEN_FOLDER="🗂️  Open dist folder? (y/n): "
if /i "%OPEN_FOLDER%"=="y" (
    explorer "dist"
)

echo.
echo ✅ Build process completed successfully!
pause