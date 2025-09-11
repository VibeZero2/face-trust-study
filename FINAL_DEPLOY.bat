@echo off
echo FINAL TEMPLATE DEPLOYMENT...
cd /d "C:\Users\Chris\CascadeProjects\facial-trust-study"

git config core.pager ""
git add dashboard\templates\base.html
git commit -m "FINAL TEMPLATE FIX: Working navigation with dashboard paths"
git push origin main

echo.
echo ✅ FINAL TEMPLATE DEPLOYED!
echo 📊 Dashboard navigation will work in ~3 minutes
echo.
pause
