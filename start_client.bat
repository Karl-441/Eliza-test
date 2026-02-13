@echo off
title Eliza Client
cd /d "%~dp0"

if not exist "venv" (
    echo [ERROR] Virtual environment not found. Please run 'install.bat' first.
    pause
    exit /b
)

call "venv\Scripts\activate"
set PYTHONPATH=%~dp0

echo [INFO] Starting Client...
start "Eliza Client" python -m client.main
