@echo off
echo =====================================
echo   SCIPY FIX - REQUIREMENTS UPDATE
echo =====================================
echo.

cd /d "C:\Users\Chris\CascadeProjects\facial-trust-study"
echo Current directory: %CD%
echo.

echo Adding requirements fix...
git add requirements.txt

echo.
echo Committing changes...
git commit -m "FIX: Ensure scipy is properly installed in requirements.txt"

echo.
echo Pushing to GitHub...
git push origin main

echo.
echo =====================================
echo   SCIPY FIX PUSHED!
echo =====================================
echo.
echo ✅ Render will redeploy with scipy in ~5 minutes
echo 📊 Dashboard: https://facial-trust-study.onrender.com/dashboard/
echo.
pause
