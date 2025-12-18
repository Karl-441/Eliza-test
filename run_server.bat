@echo off
title Eliza Server Launcher
cd /d "%~dp0"

if not exist "venv" (
    echo [ERROR] Virtual environment not found. Please run 'install.bat' first.
    pause
    exit /b
)

call "%~dp0venv\Scripts\activate"
set PYTHONPATH=%~dp0

echo [INFO] Installing server dependencies...
"%~dp0venv\Scripts\python.exe" -m pip install --disable-pip-version-check -r "%~dp0server\requirements.txt"

echo [INFO] Starting Main Server...
start /min "Eliza Main Server" "%~dp0venv\Scripts\python.exe" "%~dp0server\app.py" >> "%~dp0server\server_error.log" 2>&1

echo [INFO] Waiting for Main Server to initialize...
timeout /t 5 /nobreak >nul

echo [INFO] Starting TTS Module...
if exist "%~dp0server\Models\TTS\api_v2.py" (
    start /min "Eliza TTS Module" /D "%~dp0server\Models\TTS" "%~dp0venv\Scripts\python.exe" api_v2.py >> "%~dp0server\tts_error.log" 2>&1
) else (
    echo [ERROR] TTS Module not found at server\Models\TTS\api_v2.py
    echo [ERROR] Check if the file exists or if the path is correct.
    pause
)

echo [INFO] All services startup sequence initiated.
exit
