@echo off
echo FORCE PUSHING NAVIGATION FIXES...
cd /d "C:\Users\Chris\CascadeProjects\facial-trust-study"

REM Force add all changes
git add -A
git status
git commit -m "CRITICAL FIX: Navigation menu using url_for() to fix 404 errors in unified deployment"
git push origin main

echo.
echo NAVIGATION FIXES PUSHED!
echo Render deploying in ~5 minutes...
pause
