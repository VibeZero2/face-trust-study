@echo off
echo Fixing git pager configuration...
cd /d "C:\Users\Chris\CascadeProjects\facial-trust-study"

REM Disable git pager to prevent terminal corruption
git config --global core.pager ""
git config --global pager.branch false
git config --global pager.log false
git config --global pager.status false

echo Git pager disabled - no more terminal corruption!

echo Deploying navigation fix...
git add dashboard\templates\base.html
git commit -m "NAVIGATION FIX: Hardcoded dashboard paths"
git push origin main

echo.
echo ✅ DONE! Navigation fix deployed!
echo 📊 Dashboard will work in 3 minutes
pause
