@echo off
echo Pushing watchdog fix to GitHub...
git add dashboard\dashboard_app.py
git commit -m "FIX: Disable watchdog to resolve Render ModuleNotFoundError"
git push origin main
echo.
echo ✅ DONE! Check Render deployment in 5 minutes.
echo 📊 Dashboard: https://facial-trust-study.onrender.com/dashboard/
pause
