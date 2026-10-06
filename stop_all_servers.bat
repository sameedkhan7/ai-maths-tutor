@echo off
title Stop All AI Maths Tutor Servers
color 0C
echo ========================================================
echo       STOPPING ALL AI MATHS TUTOR SERVERS
echo ========================================================
echo.

taskkill /FI "WINDOWTITLE eq 1. AI Maths Backend Server*" /F >nul 2>&1
taskkill /FI "WINDOWTITLE eq 2. Cloudflare Public HTTPS Tunnel*" /F >nul 2>&1
taskkill /FI "WINDOWTITLE eq 3. AI Maths Frontend Server*" /F >nul 2>&1
taskkill /IM cloudflared.exe /F >nul 2>&1

echo [OK] All servers have been stopped!
echo.
pause
