@echo off
echo FIXING NAVIGATION ISSUES...
cd /d "C:\Users\Chris\CascadeProjects\facial-trust-study"
git add dashboard\templates\base.html
git commit -m "Fix menu navigation - Overview and route links"
git push origin main
echo DONE! Navigation fixed.
pause
