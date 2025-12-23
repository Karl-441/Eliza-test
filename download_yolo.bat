@echo off
setlocal

echo [Eliza] Checking environment...

:: Check for Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [Error] Python is not installed or not in PATH.
    pause
    exit /b 1
)

echo [Eliza] Installing dependencies...
pip install requests tqdm ultralytics opencv-python

echo [Eliza] Starting YOLO Model Download...
python server/scripts/download_yolo.py

if %errorlevel% neq 0 (
    echo [Error] Download failed.
    pause
    exit /b 1
)

echo [Eliza] YOLO Model Deployment Complete.
pause
