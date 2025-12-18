@echo off
title Eliza Client Launcher

if not exist "%~dp0venv" (
    echo [INFO] Creating virtual environment...
    py -3 -m venv "%~dp0venv"
)

call "%~dp0venv\Scripts\activate"
"%~dp0venv\Scripts\python.exe" -m pip install --disable-pip-version-check -r "%~dp0client\requirements.txt"
set PYTHONPATH=%~dp0
echo [INFO] Starting Client...
start /min "Eliza Client" "%~dp0venv\Scripts\python.exe" -m client.main >> "%~dp0client_error.log" 2>&1
exit
