@echo off
title Facial Trust Study System
color 0A

echo ========================================
echo    FACIAL TRUST STUDY SYSTEM
echo ========================================
echo.
echo Starting both applications...
echo.

echo [1/2] Starting Dashboard on port 3001...
start "Dashboard" cmd /k "cd /d %~dp0 && python -m dashboard.dashboard_app"

echo Waiting for dashboard to start...
timeout /t 3 /nobreak > nul

echo [2/2] Starting Study Program on port 3000...
start "Study Program" cmd /k "cd /d %~dp0 && python app.py"

echo.
echo ========================================
echo    SYSTEM STARTED SUCCESSFULLY
echo ========================================
echo.
echo Study Program: http://localhost:3000
echo Dashboard:     http://localhost:3001
echo.
pause
