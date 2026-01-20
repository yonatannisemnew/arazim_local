@echo off
setlocal EnableDelayedExpansion

:: ==========================================
:: Windows Installer for Arazim Local (x64)
:: ==========================================

:: 1. Check for Administrator Privileges
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo =====================================================
    echo  ERROR: PERMISSION DENIED
    echo  Please right-click this script and select:
    echo  "Run as administrator"
    echo =====================================================
    pause
    exit /b 1
)

:: 2. Define Paths
:: Resolve absolute path to source to avoid "..\..\" issues
:: Assumes installer is in a SUBDIRECTORY (e.g., \installers\). 
:: If installer is in root, change "..\Arazim Local" to ".\Arazim Local"
pushd "%~dp0"
for %%I in ("..\Arazim Local") do set "SOURCE_DIR=%%~fI"
popd

set "TARGET_DIR=%ProgramFiles%\Arazim Local"

echo Starting installation of Arazim Local...
echo Source: "%SOURCE_DIR%"
echo Target: "%TARGET_DIR%"

:: 3. Check if source exists
:: Note: We remove the trailing backslash for the check to be safe
if not exist "%SOURCE_DIR%" (
    echo.
    echo =====================================================
    echo  ERROR: Source directory not found!
    echo  Expected at: "%SOURCE_DIR%"
    echo =====================================================
    pause
    exit /b 1
)

:: 4. Create target directory
if not exist "%TARGET_DIR%" (
    echo Creating target directory...
    mkdir "%TARGET_DIR%"
)

:: 5. Copy files
echo Copying files...
:: /E = Recursive, /I = Assume dir, /H = Hidden, /Y = Yes to overwrite, /K = Keep attributes
xcopy "%SOURCE_DIR%" "%TARGET_DIR%" /E /I /H /Y /K

if %errorLevel% neq 0 (
    echo.
    echo =====================================================
    echo  ERROR: Failed to copy files.
    echo =====================================================
    pause
    exit /b 1
)

echo.
echo =====================================================
echo  Installation Complete.
echo  Files are located in: "%TARGET_DIR%"
echo =====================================================

pause