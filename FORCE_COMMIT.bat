@echo off
echo FORCE COMMITTING ALL CHANGES...
cd /d "C:\Users\Chris\CascadeProjects\facial-trust-study"
git add .
git commit -m "FORCE: Fix navigation menu and all pending changes"
git push origin main --force
echo.
echo FORCED PUSH COMPLETE!
echo Render deploying in 5 minutes...
echo.
pause
