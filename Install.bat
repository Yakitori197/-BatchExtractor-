@echo off
title Build EXE - YoLab Batch Extractor
color 0A

cd /d "%~dp0"

echo.
echo ============================================================
echo           Building EXE - YoLab Batch Extractor
echo ============================================================
echo.

:: Check Python
echo [1/5] Checking Python...
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
echo [2/5] Setting up environment...
if not exist venv (
    python -m venv venv
)
call venv\Scripts\activate.bat
echo       OK
echo.

:: Install packages (show progress)
echo [3/5] Installing packages (this may take 1-2 minutes)...
echo.
python -m pip install --upgrade pip
pip install pyinstaller
echo.
echo       OK
echo.

:: Build EXE (show progress)
echo [4/5] Building EXE (please wait about 1-2 minutes)...
echo.

pyinstaller --noconfirm --onefile --windowed --name "BatchExtractor" BatchExtractor.py

if errorlevel 1 (
    echo.
    echo [ERROR] Build failed!
    pause
    exit /b
)

echo.
echo       OK
echo.

:: Copy EXE to project root with Chinese name
echo [5/5] Creating executable in project folder...
python copy_exe.py
echo.

:: Clean up build folders
rmdir /s /q build 2>nul
rmdir /s /q __pycache__ 2>nul
del /f /q *.spec 2>nul

echo.
echo ============================================================
echo              Build Complete!
echo ============================================================
echo.
echo You can now double-click the EXE in this folder to run!
echo (Make sure 7-Zip is installed on this computer)
echo.

pause
