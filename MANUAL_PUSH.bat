@echo off
echo =====================================
echo   MANUAL GIT PUSH - WATCHDOG FIX
echo =====================================
echo.

cd /d "C:\Users\Chris\CascadeProjects\facial-trust-study"
echo Current directory: %CD%
echo.

echo Adding files...
git add dashboard\dashboard_app.py
git add .

echo.
echo Committing changes...
git commit -m "CRITICAL FIX: Disable watchdog imports to resolve Render ModuleNotFoundError"

echo.
echo Pushing to GitHub...
git push origin main

echo.
echo =====================================
echo   PUSH COMPLETE!
echo =====================================
echo.
echo ✅ Render will auto-deploy in ~5 minutes
echo 📊 Dashboard: https://facial-trust-study.onrender.com/dashboard/
echo 🔐 Login: admin / admin123
echo.
pause
