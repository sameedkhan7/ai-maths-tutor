@echo off
title AI Maths Tutor - Backend Server
color 0A
echo ========================================================
echo         AI MATHS TUTOR - BACKEND LAUNCHER
echo ========================================================
echo.

:: Set PYTHONPATH so modules resolve cleanly
set PYTHONPATH=C:\Users\SK\OneDrive\Desktop\maths project

:: Move to backend folder
if exist "%~dp0backend" (
    cd /d "%~dp0backend"
) else (
    cd /d "C:\Users\SK\OneDrive\Desktop\maths project\backend"
)

echo [1/2] Checking Python packages...
python -m pip install -r requirements.txt groq python-dotenv --quiet

echo.
echo [2/2] Starting FastAPI Server on http://127.0.0.1:8000 ...
echo [INFO] Swagger Docs: http://127.0.0.1:8000/docs
echo [INFO] Server ko band karne ke liye is window ko close kar dein ya Ctrl+C dabayein.
echo ========================================================
echo.

python -m uvicorn main:app --reload --port 8000

pause
