@echo off
title AI Maths Tutor — Fullstack Server Launcher
color 0B
echo ========================================================
echo       AI MATHS TUTOR — FULLSTACK SERVER LAUNCHER
echo ========================================================
echo.

echo [1/2] Starting FastAPI Backend on http://127.0.0.1:8000 ...
start "AI Maths Backend (Port 8000)" cmd /k "set PYTHONPATH=C:\Users\SK\OneDrive\Desktop\maths project&& cd /d C:\Users\SK\OneDrive\Desktop\maths project\backend&& python -m uvicorn main:app --reload --port 8000"

echo [2/2] Starting Frontend Web Server on http://127.0.0.1:5500 ...
start "AI Maths Frontend (Port 5500)" cmd /k "cd /d C:\Users\SK\OneDrive\Desktop\maths project&& python -m http.server 5500"

echo.
echo ========================================================
echo SUCCESS! Both Servers are live:
echo - Frontend URL: http://127.0.0.1:5500/login.html
echo - Backend API:  http://127.0.0.1:8000/docs
echo ========================================================
echo.
timeout /t 3 >nul
start http://127.0.0.1:5500/login.html
