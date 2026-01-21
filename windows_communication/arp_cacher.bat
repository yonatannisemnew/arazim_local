@echo off
setlocal

REM --- 1. Setup Paths ---
if "%~1"=="" exit /b 1
set "USER_ARG=%~1"

python arp_cacher.py "%USER_ARG%" >nul 2>&1
exit /b 0