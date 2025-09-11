@echo off
echo =====================================
echo   TEMPORARY SCIPY FIX FOR RENDER
echo =====================================
echo.

cd /d "C:\Users\Chris\CascadeProjects\facial-trust-study"
echo Current directory: %CD%
echo.

echo Adding scipy mock fix...
git add dashboard\analysis\stats.py

echo.
echo Committing changes...
git commit -m "TEMP FIX: Mock scipy functions to bypass Render build issue"

echo.
echo Pushing to GitHub...
git push origin main

echo.
echo =====================================
echo   TEMPORARY FIX DEPLOYED!
echo =====================================
echo.
echo ✅ Dashboard should work now (without advanced stats)
echo 📊 Dashboard: https://facial-trust-study.onrender.com/dashboard/
echo 🔐 Login: admin / admin123
echo.
echo NOTE: Statistical analysis will show placeholder values
echo until we fix the scipy installation issue.
echo.
pause
