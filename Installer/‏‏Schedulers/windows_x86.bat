@echo off
setlocal EnableExtensions EnableDelayedExpansion

REM ===============================
REM Require Administrator
REM ===============================
net session >nul 2>&1
if not "%errorlevel%"=="0" (
    echo [ERROR] This script must be run as Administrator.
    exit /b 1
)

REM ===============================
REM Validate arguments
REM ===============================
if "%~1"=="" (
    echo [ERROR] Missing python file.
    echo Usage: %~nx0 ^<script.py^> ^<interval_minutes^>
    exit /b 1
)

if "%~2"=="" (
    echo [ERROR] Missing duration in minutes.
    echo Usage: %~nx0 ^<script.py^> ^<interval_minutes^>
    exit /b 1
)

set PY_FILE=%~f1
set INTERVAL=%~2

if not exist "%PY_FILE%" (
    echo [ERROR] Python file not found: %PY_FILE%
    exit /b 1
)

REM ===============================
REM Detect python / python3
REM ===============================
where python >nul 2>&1
if "%errorlevel%"=="0" (
    set PYTHON_CMD=python
) else (
    where python3 >nul 2>&1
    if "%errorlevel%"=="0" (
        set PYTHON_CMD=python3
    ) else (
        echo [ERROR] python or python3 not found in PATH.
        exit /b 1
    )
)

REM ===============================
REM Task name (safe for x86)
REM ===============================
set TASK_NAME=RunPython_%~n1_Every_%INTERVAL%min

REM ===============================
REM Create scheduled task
REM ===============================
schtasks /create ^
    /f ^
    /sc minute ^
    /mo %INTERVAL% ^
    /tn "%TASK_NAME%" ^
    /tr "\"%PYTHON_CMD%\" \"%PY_FILE%\"" ^
    /ru SYSTEM ^
    /rl HIGHEST

if not "%errorlevel%"=="0" (
    echo [ERROR] Failed to create scheduled task.
    exit /b 1
)

echo [SUCCESS] Task created successfully
echo   Name     : %TASK_NAME%
echo   Python   : %PYTHON_CMD%
echo   Script   : %PY_FILE%
echo   Interval : Every %INTERVAL% minutes

exit /b 0
