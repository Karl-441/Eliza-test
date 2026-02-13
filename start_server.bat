@echo off
title Eliza Server
cd /d "%~dp0"

if not exist "venv" (
    echo [ERROR] Virtual environment not found. Please run 'install.bat' first.
    pause
    exit /b
)

call "venv\Scripts\activate"
set PYTHONPATH=%~dp0

echo [INFO] Starting Main Server...
start "Eliza Main Server" cmd /k "python -m server.app"

echo [INFO] Waiting for Main Server...
timeout /t 3 /nobreak >nul

if exist "server\Models\TTS\api_v2.py" (
    echo [INFO] Starting TTS Module...
    start "Eliza TTS Module" /D "server\Models\TTS" cmd /k "..\..\..\venv\Scripts\python.exe api_v2.py"
)

echo [INFO] Services started.
