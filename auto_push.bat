@echo off
setlocal EnableDelayedExpansion
chcp 65001 >nul

REM --- Configuration ---
set "SCRIPT_DIR=%~dp0"
REM Remove trailing backslash if present
if "%SCRIPT_DIR:~-1%"=="\" set "SCRIPT_DIR=%SCRIPT_DIR:~0,-1%"

set "LOGFILE=%SCRIPT_DIR%\auto_git_eliza.log"
set "TARGET_DIR=%SCRIPT_DIR%"

REM Navigate to the script directory
cd /d "%TARGET_DIR%"

echo --------------------------------------------------- >> "%LOGFILE%"
echo [%date% %time%] Starting Auto-Push Process for Eliza-test >> "%LOGFILE%"

REM --- 1. Validate Git Repository ---
if not exist ".git" (
    echo [%date% %time%] [ERROR] .git directory not found in %TARGET_DIR% >> "%LOGFILE%"
    goto :End
)

REM Get git root
for /f "delims=" %%i in ('git rev-parse --show-toplevel 2^>nul') do set "REPO_ROOT=%%i"
echo [%date% %time%] Repository Root: %REPO_ROOT% >> "%LOGFILE%"

REM --- 2. Detect Current Branch ---
set "BRANCH="
for /f "delims=" %%i in ('git branch --show-current 2^>nul') do set "BRANCH=%%i"

if "%BRANCH%"=="" (
    echo [%date% %time%] [ERROR] Could not detect current branch. >> "%LOGFILE%"
    goto :End
)
echo [%date% %time%] Detected Branch: %BRANCH% >> "%LOGFILE%"

REM --- 3. Add and Commit Changes ---
echo [%date% %time%] Checking for changes... >> "%LOGFILE%"
git add . >> "%LOGFILE%" 2>&1

REM Check if there are changes (staged or unstaged)
REM git diff --quiet checks unstaged changes. git diff --cached --quiet checks staged.
REM Since we just ran git add ., we only need to check staged changes.
git diff --cached --quiet
if %errorlevel% equ 0 (
    echo [%date% %time%] No changes to commit. >> "%LOGFILE%"
) else (
    echo [%date% %time%] Committing changes... >> "%LOGFILE%"
    git commit -m "Auto-commit: %date% %time%" >> "%LOGFILE%" 2>&1
)

REM --- 4. Pull (Rebase) ---
echo [%date% %time%] Pulling updates from remote [%BRANCH%]... >> "%LOGFILE%"
git pull origin %BRANCH% --rebase >> "%LOGFILE%" 2>&1
if %errorlevel% neq 0 (
    echo [%date% %time%] [ERROR] Pull failed - Conflicts likely. Aborting push. >> "%LOGFILE%"
    goto :End
)

REM --- 5. Push ---
echo [%date% %time%] Pushing to remote [%BRANCH%]... >> "%LOGFILE%"
git push origin %BRANCH% >> "%LOGFILE%" 2>&1

if %errorlevel% neq 0 (
    echo [%date% %time%] [ERROR] Push Failed - Exit Code: %errorlevel% >> "%LOGFILE%"
) else (
    echo [%date% %time%] [SUCCESS] Push Successful >> "%LOGFILE%"
)

:End
echo --------------------------------------------------- >> "%LOGFILE%"
endlocal
