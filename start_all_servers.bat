@echo off
title AI Maths Tutor — All Servers Launcher
color 0B
echo ========================================================
echo       AI MATHS TUTOR — ALL SERVERS LAUNCHER
echo ========================================================
echo.

echo [*] Checking and cleaning old instances on Port 8000 & 5500...
powershell -NoProfile -Command "Get-NetTCPConnection -LocalPort 8000, 5500 -ErrorAction SilentlyContinue | Select-Object -ExpandProperty OwningProcess -Unique | ForEach-Object { Stop-Process -Id $_ -Force -ErrorAction SilentlyContinue }" >nul 2>&1
timeout /t 1 >nul

:: Detect Local Wi-Fi IPv4 for Mobile & Friend Laptop
for /f "delims=" %%a in ('powershell -NoProfile -Command "(Get-NetIPAddress -InterfaceAlias 'Wi-Fi*' -AddressFamily IPv4 -ErrorAction SilentlyContinue).IPAddress"') do set WIFI_IP=%%a
if "%WIFI_IP%"=="" set WIFI_IP=10.57.109.56

echo [1/3] Starting FastAPI Backend AI Engine (Port 8000)...
start "1. AI Maths Backend Server" cmd /k "cd /d "%~dp0backend" && set PYTHONPATH=%~dp0&& python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000"

timeout /t 2 >nul

echo [2/3] Starting Cloudflare Public HTTPS Tunnel...
start "2. Cloudflare Public HTTPS Tunnel" cmd /k "cd /d "%~dp0" && .\cloudflared.exe tunnel --url http://127.0.0.1:8000"

timeout /t 2 >nul

echo [3/3] Starting Local Frontend Server (Port 5500)...
start "3. AI Maths Frontend Server" cmd /k "cd /d "%~dp0" && python -m http.server 5500 --bind 0.0.0.0"

echo.
echo =====================================================================
echo  SUCCESS! All Servers are running:
echo.
echo  [1] Laptop Browser (Self):
echo      http://127.0.0.1:5500/login.html
echo.
echo  [2] Mobile Phone & Friend Laptop (Same Wi-Fi / Hotspot):
echo      http://%WIFI_IP%:5500/login.html
echo.
echo  [3] Internet / Remote Anywhere:
echo      See "Cloudflare Public HTTPS Tunnel" window for public URL
echo =====================================================================
echo.
timeout /t 2 >nul
start http://127.0.0.1:5500/login.html
