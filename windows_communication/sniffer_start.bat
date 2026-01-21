@echo off
setlocal

REM --- 1. Setup Paths ---
if "%~1"=="" exit /b 1
set "USER_ARG=%~1"
set "HELPER=%~dp0net_helper.ps1"
REM Define a specific path for the result file
set "RESULT_FILE=%TEMP%\sniffer_result.json"

REM --- 2. Create Helper Script (Same as before) ---
echo $ErrorActionPreference = 'Stop' > "%HELPER%"
echo try { >> "%HELPER%"
echo     $a = Get-NetAdapter ^| Where-Object { $_.Status -eq 'Up' -and ($_.Name -match 'Wi-Fi^|WiFi^|Wireless') } ^| Select-Object -First 1 >> "%HELPER%"
echo     if (!$a) { $a = Get-NetAdapter ^| Where-Object { $_.Status -eq 'Up' } ^| Select-Object -First 1 } >> "%HELPER%"
echo     if (!$a) { exit 1 } >> "%HELPER%"
echo     $idx = $a.ifIndex >> "%HELPER%"
echo     $c = Get-WmiObject Win32_NetworkAdapterConfiguration -Filter "InterfaceIndex=$idx" >> "%HELPER%"
echo     $ip = $c.IPAddress ^| Where-Object { $_ -match '\d+\.\d+\.\d+\.\d+' } ^| Select-Object -First 1 >> "%HELPER%"
echo     $gw = $c.DefaultIPGateway ^| Where-Object { $_ -match '\d+\.\d+\.\d+\.\d+' } ^| Select-Object -First 1 >> "%HELPER%"
echo     $mk = $c.IPSubnet ^| Where-Object { $_ -match '\d+\.\d+\.\d+\.\d+' } ^| Select-Object -First 1 >> "%HELPER%"
echo     if (!$gw) { $gw = '0.0.0.0' } >> "%HELPER%"
echo     Write-Output "$ip;$gw;$mk;$idx" >> "%HELPER%"
echo } catch { exit 1 } >> "%HELPER%"

REM --- 3. Execute PowerShell ---
set "MY_IP="
for /f "tokens=1,2,3,4 delims=;" %%a in ('powershell -NoLogo -NoProfile -ExecutionPolicy Bypass -File "%HELPER%"') do (
    set "MY_IP=%%a"
    set "GATEWAY_IP=%%b"
    set "SUBNET_MASK=%%c"
    set "IF_INDEX=%%d"
)

REM Cleanup helper
del "%HELPER%"
if "%MY_IP%"=="" exit /b 1

REM --- 4. Run Python Side-Effect (Silent) ---
python arp_cacher.py "%USER_ARG%" >nul 2>&1

REM --- 5. WRITE TO FILE (The "Smart" Part) ---
REM We manually construct a JSON-like list string.
echo ["%MY_IP%", "%GATEWAY_IP%", "%SUBNET_MASK%", %IF_INDEX%] > "%RESULT_FILE%"

REM We don't echo anything to stdout anymore.
exit /b 0