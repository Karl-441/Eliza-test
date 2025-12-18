@echo off
if not exist venv (
    echo [ERROR] Virtual environment not found. Please run 'install.bat' first.
    pause
    exit /b
)
call venv\Scripts\activate
echo [INFO] Starting Model Downloader...
python scripts/download_models.py
pause
