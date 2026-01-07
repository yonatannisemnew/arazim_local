@echo off
setlocal EnableDelayedExpansion

:: ==============================================================================
:: Script Name: schedule.bat
:: Description: Schedules a Python script to run every T minutes using Windows Task Scheduler.
:: Usage: schedule.bat
:: ==============================================================================


set "SCRIPT_PATH=run_binary.py"
set "INTERVAL=15"
set "SCRIPT_DIR=%~dp1"
set "SCRIPT_NAME=%~n1"
set "LOG_FILE=%SCRIPT_DIR%%SCRIPT_NAME%.log"

:: Check if file exists
if not exist "%SCRIPT_PATH%" (
    echo Error: File "%SCRIPT_PATH%" not found.
    exit /b 1
)

:: Find Python Executable
where python >nul 2>nul
if %errorlevel% neq 0 (
    echo Error: 'python' command not found. Is Python installed and added to PATH?
    exit /b 1
)
:: Capture the full path of the python executable
for /f "tokens=*" %%i in ('where python') do set "PYTHON_EXE=%%i" & goto :found_python

:found_python

:: Construct the Command
:: We define a unique Task Name based on the file name
set "TASK_NAME=Python_Task_%SCRIPT_NAME%"

:: We wrap the execution in 'cmd /c' to allow for logging (>>).
:: Note: The crazy escaping (\") is required because this entire string is passed to schtasks.
set "TR_COMMAND=cmd /c \"\"%PYTHON_EXE%\" \"%SCRIPT_PATH%\" ^>^> \"%LOG_FILE%\" 2^>^&1\""

:: Create the Scheduled Task
echo ---------------------------------------------------
echo Creating Task: %TASK_NAME%
echo Script Path:   %SCRIPT_PATH%
echo Log File:      %LOG_FILE%
echo Frequency:     Every %INTERVAL% minutes
echo ---------------------------------------------------

:: /sc minute = Schedule type (Minutes)
:: /mo %INTERVAL% = Modifier (how many minutes)
:: /tr ... = Task Run (the command)
:: /f = Force overwrite if task exists
schtasks /create /sc minute /mo %INTERVAL% /tn "%TASK_NAME%" /tr "%TR_COMMAND%" /f

if %errorlevel% equ 0 (
    echo.
    echo Success! Task scheduled successfully.
) else (
    echo.
    echo Error: Failed to create task. 
    echo TIP: You may need to run this batch file as Administrator.
)

pause