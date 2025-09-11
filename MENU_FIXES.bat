@echo off
echo =====================================
echo   MENU AND NAVIGATION FIXES
echo =====================================
echo.

cd /d "C:\Users\Chris\CascadeProjects\facial-trust-study"
echo Current directory: %CD%
echo.

echo Adding menu navigation fixes...
git add dashboard\templates\base.html

echo.
echo Committing changes...
git commit -m "FIX: Update menu navigation - fix Overview link and use correct route names"

echo.
echo Pushing to GitHub...
git push origin main

echo.
echo =====================================
echo   MENU FIXES DEPLOYED!
echo =====================================
echo.
echo ✅ Fixed menu navigation issues:
echo   - Overview link now points to dashboard
echo   - Updated menu to use existing routes
echo   - Removed non-existent routes
echo.
echo 📊 Dashboard: https://facial-trust-study.onrender.com/dashboard/
echo.
pause
