@echo off
git add .
git commit -m "FIX: Make watchdog import optional for Render deployment"
git push origin main
echo Deployment fix pushed to GitHub!
pause
