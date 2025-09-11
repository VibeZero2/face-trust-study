@echo off
echo CLEANING UP TEMPORARY FILES...
cd /d "C:\Users\Chris\CascadeProjects\facial-trust-study"

REM Delete all temporary batch and script files
del /f /q "auto_commit.py" 2>nul
del /f /q "COMMIT_CHANGES.bat" 2>nul
del /f /q "commit_fix.bat" 2>nul
del /f /q "FIX_NOW.bat" 2>nul
del /f /q "FORCE_COMMIT.bat" 2>nul
del /f /q "FORCE_PUSH.py" 2>nul
del /f /q "MANUAL_PUSH.bat" 2>nul
del /f /q "MENU_FIXES.bat" 2>nul
del /f /q "push_fix.py" 2>nul
del /f /q "push_now.cmd" 2>nul
del /f /q "QUICK_FIX.py" 2>nul
del /f /q "SCIPY_FIX.bat" 2>nul
del /f /q "SCIPY_TEMP_FIX.bat" 2>nul
del /f /q "h origin main" 2>nul
del /f /q "olves ModuleNotFoundError" 2>nul

echo Committing navigation fixes and cleanup...
git add dashboard\templates\base.html
git commit -m "FIX: Navigation menu using url_for() for proper routing in unified setup + cleanup temp files"
git push origin main

echo Deleting this cleanup script...
del /f /q "FINAL_CLEANUP.bat"

echo.
echo ✅ CLEANUP COMPLETE!
echo ✅ Navigation fixes committed and pushed!
echo 🔄 Render deploying in ~5 minutes
echo 📊 Dashboard: https://facial-trust-study.onrender.com/dashboard/
echo.
pause
