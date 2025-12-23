@echo off
setlocal
title Eliza Model Downloader

set "TARGET_DIR=D:\Github\Eliza-test\server\Models\llm"
if not exist "%TARGET_DIR%" mkdir "%TARGET_DIR%"
cd /d "%TARGET_DIR%"

echo Downloading qwen2.5-1.5b-instruct-q4_k_m.gguf...
echo URL: https://huggingface.co/Qwen/Qwen2.5-1.5B-Instruct-GGUF/resolve/main/qwen2.5-1.5b-instruct-q4_k_m.gguf
curl -L -o "qwen2.5-1.5b-instruct-q4_k_m.gguf" "https://huggingface.co/Qwen/Qwen2.5-1.5B-Instruct-GGUF/resolve/main/qwen2.5-1.5b-instruct-q4_k_m.gguf" --fail
if %errorlevel% neq 0 (
    echo Error downloading qwen2.5-1.5b-instruct-q4_k_m.gguf. Retrying...
    curl -L -o "qwen2.5-1.5b-instruct-q4_k_m.gguf" "https://huggingface.co/Qwen/Qwen2.5-1.5B-Instruct-GGUF/resolve/main/qwen2.5-1.5b-instruct-q4_k_m.gguf" --retry 3
)
if exist "qwen2.5-1.5b-instruct-q4_k_m.gguf" echo [OK] qwen2.5-1.5b-instruct-q4_k_m.gguf downloaded.

echo Downloading llama-3-8b-instruct-q4_k_m.gguf...
echo URL: https://huggingface.co/QuantFactory/Meta-Llama-3-8B-Instruct-GGUF/resolve/main/Meta-Llama-3-8B-Instruct.Q4_K_M.gguf
curl -L -o "llama-3-8b-instruct-q4_k_m.gguf" "https://huggingface.co/QuantFactory/Meta-Llama-3-8B-Instruct-GGUF/resolve/main/Meta-Llama-3-8B-Instruct.Q4_K_M.gguf" --fail
if %errorlevel% neq 0 (
    echo Error downloading llama-3-8b-instruct-q4_k_m.gguf. Retrying...
    curl -L -o "llama-3-8b-instruct-q4_k_m.gguf" "https://huggingface.co/QuantFactory/Meta-Llama-3-8B-Instruct-GGUF/resolve/main/Meta-Llama-3-8B-Instruct.Q4_K_M.gguf" --retry 3
)
if exist "llama-3-8b-instruct-q4_k_m.gguf" echo [OK] llama-3-8b-instruct-q4_k_m.gguf downloaded.

echo Downloading mistral-7b-instruct-v0.3-q4_k_m.gguf...
echo URL: https://huggingface.co/MaziyarPanahi/Mistral-7B-Instruct-v0.3-GGUF/resolve/main/Mistral-7B-Instruct-v0.3.Q4_K_M.gguf
curl -L -o "mistral-7b-instruct-v0.3-q4_k_m.gguf" "https://huggingface.co/MaziyarPanahi/Mistral-7B-Instruct-v0.3-GGUF/resolve/main/Mistral-7B-Instruct-v0.3.Q4_K_M.gguf" --fail
if %errorlevel% neq 0 (
    echo Error downloading mistral-7b-instruct-v0.3-q4_k_m.gguf. Retrying...
    curl -L -o "mistral-7b-instruct-v0.3-q4_k_m.gguf" "https://huggingface.co/MaziyarPanahi/Mistral-7B-Instruct-v0.3-GGUF/resolve/main/Mistral-7B-Instruct-v0.3.Q4_K_M.gguf" --retry 3
)
if exist "mistral-7b-instruct-v0.3-q4_k_m.gguf" echo [OK] mistral-7b-instruct-v0.3-q4_k_m.gguf downloaded.

echo.
echo All downloads processed.
pause