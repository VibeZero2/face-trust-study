@echo off
title Facial Trust Study
color 0A

echo ========================================
echo    FACIAL TRUST STUDY SYSTEM
echo ========================================
echo.
echo Starting application on port 3000...
echo.

echo [1/1] Starting Facial Trust Study...
start "Facial Trust Study" cmd /k "cd /d %~dp0 && python app.py"

echo.
echo ========================================
echo    APPLICATION STARTED SUCCESSFULLY
echo ========================================
echo.
echo Study:      http://localhost:3000
echo Dashboard:  http://localhost:3000/dashboard
echo.
pause
