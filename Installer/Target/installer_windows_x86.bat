@echo off
setlocal EnableDelayedExpansion

:: ==========================================
:: Windows Installer for Arazim Local (x86 / 32-bit)
:: ==========================================

:: 1. Check for Administrator Privileges
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo =====================================================
    echo  ERROR: PERMISSION DENIED
    echo  Run as administrator.
    echo =====================================================
    pause
    exit /b 1
)

:: 2. Determine Architecture
if defined ProgramFiles(x86) (
    set "TARGET_ROOT=%ProgramFiles(x86)%"
    echo Detected 64-bit OS. Installing into x86 directory.
) else (
    set "TARGET_ROOT=%ProgramFiles%"
    echo Detected 32-bit OS. Installing into standard directory.
)

:: 3. Define Paths (Canonicalized)
pushd "%~dp0"
for %%I in ("..\Arazim Local") do set "SOURCE_DIR=%%~fI"
popd

set "TARGET_DIR=%TARGET_ROOT%\Arazim Local"

echo Source: "%SOURCE_DIR%"
echo Target: "%TARGET_DIR%"

:: 4. Check Source
if not exist "%SOURCE_DIR%" (
    echo.
    echo Error: Source directory not found at: "%SOURCE_DIR%"
    pause
    exit /b 1
)

:: 5. Create Target
if not exist "%TARGET_DIR%" (
    mkdir "%TARGET_DIR%"
)

:: 6. Copy Files
echo Copying files...
xcopy "%SOURCE_DIR%" "%TARGET_DIR%" /E /I /H /Y /K

if %errorLevel% neq 0 (
    echo Error: Failed to copy files.
    pause
    exit /b 1
)

echo.
echo =====================================================
echo  Installation Complete.
echo =====================================================
pause