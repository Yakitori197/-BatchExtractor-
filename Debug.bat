@echo off
title YoLab Batch Extractor - Debug
color 0A

cd /d "%~dp0"

echo.
echo ============================================================
echo           YoLab Batch Extractor - Debug Mode
echo ============================================================
echo.

:: Check Python
echo [1/3] Checking Python...
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not found!
    echo Please install from https://python.org
    pause
    exit /b
)
python --version
echo       OK
echo.

:: Setup venv
echo [2/3] Setting up environment...
if not exist venv (
    python -m venv venv
)
call venv\Scripts\activate.bat
echo       OK
echo.

:: Install packages if needed
echo [3/3] Checking packages...
pip show tkinter >nul 2>&1
echo       OK
echo.

echo ============================================================
echo              Launching GUI...
echo ============================================================
echo.

:: Launch BatchExtractor.py directly
python BatchExtractor.py

pause
