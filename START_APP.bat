@echo off
title Facial Trust Study - Starting...
color 0A

echo ========================================
echo    STARTING FACIAL TRUST STUDY
echo ========================================
echo.

echo [1/3] Installing required packages...
pip install -r requirements.txt

echo.
echo [2/3] Starting the application...
start "" http://localhost:3000

python app.py

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo ❌ Failed to start the application. Check for errors above.
    pause
    exit /b 1
)

echo.
echo ========================================
echo    APPLICATION STARTED SUCCESSFULLY
echo ========================================
echo.
echo Study:      http://localhost:3000
echo Dashboard:  http://localhost:3000/dashboard
echo.
pause
