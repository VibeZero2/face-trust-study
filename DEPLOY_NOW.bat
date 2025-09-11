@echo off
echo DEPLOYING DASHBOARD FIXES...
cd /d "C:\Users\Chris\CascadeProjects\facial-trust-study"

git config core.pager ""
git add dashboard\templates\base.html
git commit -m "DASHBOARD FIX: Hardcoded navigation paths"
git push origin main

echo.
echo ✅ DASHBOARD NAVIGATION FIX DEPLOYED!
echo 📊 Render will update in ~3 minutes
echo 🔧 All menu links should work after deployment
echo.
pause
