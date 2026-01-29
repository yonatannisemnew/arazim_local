@echo off
setlocal EnableDelayedExpansion

:: 1. Find Python safely
set "PYTHON_CMD="
for /f "tokens=*" %%i in ('where python 2^>nul') do (
    if not defined PYTHON_CMD set "PYTHON_CMD=%%i"
)

if not defined PYTHON_CMD (
    echo [ERROR] Python not found in PATH
    exit /b 1
)

:: 2. Execute with quotes to handle spaces in "Program Files"
:: %~1 removes existing quotes so we can add them back cleanly
echo Running: "!PYTHON_CMD!" "%~1" %2
"!PYTHON_CMD!" "%~1" %2

if !errorlevel! neq 0 (
    echo [ERROR] Python script failed with exit code !errorlevel!
    exit /b !errorlevel!
)