@echo off
echo [INFO] Starting Eliza AI Installation...

:: Check for Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python is not installed. Please install Python 3.10+ and try again.
    pause
    exit /b
)

:: Create Venv
if not exist venv (
    echo [INFO] Creating virtual environment...
    python -m venv venv
)

:: Activate Venv
call venv\Scripts\activate

:: Install Dependencies
echo [INFO] Installing dependencies...
pip install --upgrade pip
:: Try to install prebuilt llama-cpp-python for CPU
pip install llama-cpp-python --extra-index-url https://abetlen.github.io/llama-cpp-python/whl/cpu
pip install -r requirements.txt

:: Create Directories if missing (already done by code but good to have)
if not exist models\llm mkdir models\llm
if not exist models\asr mkdir models\asr

echo [INFO] Installation Complete.
echo [IMPORTANT] Please download a GGUF model (e.g., Qwen1.5-4B-Chat-GGUF) and place it in 'models/llm/'.
echo [IMPORTANT] Update 'config/settings.json' or 'server/core/config.py' with the model filename.

pause
