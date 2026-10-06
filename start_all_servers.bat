@echo off
title AI Maths Tutor — All Servers Launcher
color 0B
echo ========================================================
echo       AI MATHS TUTOR — ALL SERVERS LAUNCHER
echo ========================================================
echo.

echo [1/3] Starting FastAPI Backend AI Engine (Port 8000)...
start "1. AI Maths Backend Server" cmd /k "set PYTHONPATH=C:\Users\SK\OneDrive\Desktop\maths project&& cd /d C:\Users\SK\OneDrive\Desktop\maths project\backend&& python -m uvicorn main:app --reload --port 8000"

timeout /t 2 >nul

echo [2/3] Starting Cloudflare Public HTTPS Tunnel...
start "2. Cloudflare Public HTTPS Tunnel" cmd /k "cd /d C:\Users\SK\OneDrive\Desktop\maths project&& .\cloudflared.exe tunnel --url http://127.0.0.1:8000"

timeout /t 2 >nul

echo [3/3] Starting Local Frontend Server (Port 5500)...
start "3. AI Maths Frontend Server" cmd /k "cd /d C:\Users\SK\OneDrive\Desktop\maths project&& python -m http.server 5500"

echo.
echo ========================================================
echo SUCCESS! All 3 Servers are now running:
echo - Local Laptop View: http://127.0.0.1:5500/login.html
echo - Mobile & GitHub:   https://sameedkhan7.github.io
echo ========================================================
echo.
timeout /t 3 >nul
start http://127.0.0.1:5500/login.html
