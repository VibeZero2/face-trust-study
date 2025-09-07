@echo off
title Face Perception Study System
color 0A

echo ========================================
echo    FACE PERCEPTION STUDY SYSTEM
echo ========================================
echo.
echo Starting both programs...
echo.

echo [1/2] Starting Dashboard on port 5000...
start "Dashboard" cmd /k "cd /d C:\Users\Chris\CascadeProjects\face-viewer-dashboard && python dashboard_app.py"

echo Waiting for dashboard to start...
timeout /t 3 /nobreak > nul

echo [2/2] Starting Study Program on port 8080...
start "Study Program" cmd /k "cd /d C:\Users\Chris\CascadeProjects\facial-trust-study && python WORKING_STUDY.py"

echo Waiting for study program to start...
timeout /t 3 /nobreak > nul

echo.
echo ========================================
echo    BOTH PROGRAMS ARE STARTING
echo ========================================
echo.
echo Dashboard: http://localhost:5000
echo Study Program: http://localhost:8080
echo.

echo Opening dashboard in browser...
start http://localhost:5000

echo Opening study program in browser...
start http://localhost:8080

echo.
echo ========================================
echo    SYSTEM READY!
echo ========================================
echo.
echo Both programs should now be running.
echo Check the command windows for any errors.
echo.
echo Press any key to close this window...
pause > nul
