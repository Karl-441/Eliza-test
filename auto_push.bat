@echo off
setlocal EnableDelayedExpansion
chcp 65001 >nul

REM --- Configuration ---
set "SCRIPT_DIR=%~dp0"
if "%SCRIPT_DIR:~-1%"=="\" set "SCRIPT_DIR=%SCRIPT_DIR:~0,-1%"
set "LOGFILE=%SCRIPT_DIR%\auto_git_eliza.log"
set "TARGET_DIR=%SCRIPT_DIR%"

REM Navigate to the script directory
cd /d "%TARGET_DIR%"

call :Log "==================================================="
call :Log "Starting Auto-Push Process for Eliza-test"
call :Log "Target Directory: %TARGET_DIR%"

REM --- 1. Validate Git Repository ---
if not exist ".git" (
    call :Log "[ERROR] .git directory not found."
    goto :End
)

for /f "delims=" %%i in ('git rev-parse --show-toplevel 2^>nul') do set "REPO_ROOT=%%i"
call :Log "Repository Root: %REPO_ROOT%"

REM --- 2. Detect Current Branch ---
set "BRANCH="
for /f "delims=" %%i in ('git branch --show-current 2^>nul') do set "BRANCH=%%i"

if "%BRANCH%"=="" (
    call :Log "[ERROR] Could not detect current branch."
    goto :End
)
call :Log "Detected Branch: %BRANCH%"

REM --- 3. Add and Commit Changes ---
call :Log "Checking for local changes..."
git add .

REM Check staged changes
git diff --cached --quiet
if %errorlevel% equ 0 (
    call :Log "No changes to commit."
) else (
    call :Log "Changes detected. Files to be committed:"
    
    REM Show status to console and log
    echo ------------------------------------------
    git status --short
    echo ------------------------------------------
    git status --short >> "%LOGFILE%"
    
    call :Log "Committing changes..."
    git commit -m "Auto-commit: %date% %time%" >> "%LOGFILE%" 2>&1
    
    if !errorlevel! equ 0 (
        call :Log "Commit successful."
    ) else (
        call :Log "[ERROR] Commit failed."
        goto :End
    )
)

REM --- 4. Pull (Rebase) ---
call :Log "Pulling updates from remote [%BRANCH%]..."
REM Capture output to temp file to show in log, but also want to see it? 
REM For pull, usually it's fast. Let's redirect to log and check error.
REM User wants feedback, so let's print "Pulling..." and result.
git pull origin %BRANCH% --rebase >> "%LOGFILE%" 2>&1
if %errorlevel% neq 0 (
    call :Log "[ERROR] Pull failed - Conflicts likely. Please resolve manually."
    goto :End
) else (
    call :Log "Pull (Rebase) successful/Up-to-date."
)

REM --- 5. Push ---
REM Check what will be pushed
for /f "tokens=*" %%a in ('git diff --stat origin/%BRANCH%..HEAD 2^>nul') do (
    set "HAS_PUSH_CHANGES=1"
)
if defined HAS_PUSH_CHANGES (
    call :Log "Files to be pushed:"
    echo ------------------------------------------
    git diff --stat origin/%BRANCH%..HEAD
    echo ------------------------------------------
    git diff --stat origin/%BRANCH%..HEAD >> "%LOGFILE%"
) else (
    REM Check if ahead
    git rev-list origin/%BRANCH%..HEAD --count > temp_ahead.txt
    set /p AHEAD_COUNT=<temp_ahead.txt
    del temp_ahead.txt
    if "!AHEAD_COUNT!"=="0" (
        call :Log "Local branch is up to date with remote. Nothing to push."
        goto :End
    )
)

call :Log "Pushing to remote [%BRANCH%]... (Progress will be shown below)"
echo.
REM Run git push directly to show progress bar in terminal
git push origin %BRANCH%
set PUSH_EXIT_CODE=%errorlevel%
echo.

if %PUSH_EXIT_CODE% neq 0 (
    call :Log "[ERROR] Push Failed - Exit Code: %PUSH_EXIT_CODE%"
) else (
    call :Log "[SUCCESS] Push Successful!"
)

:End
call :Log "Process Finished."
call :Log "==================================================="
echo.
echo Log saved to: %LOGFILE%
pause
exit /b

REM --- Subroutines ---
:Log
echo [%date% %time%] %~1
echo [%date% %time%] %~1 >> "%LOGFILE%"
exit /b
