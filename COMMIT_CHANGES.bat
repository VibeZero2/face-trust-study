@echo off
echo COMMITTING NAVIGATION CHANGES...
cd /d "C:\Users\Chris\CascadeProjects\facial-trust-study"
git add -A
git commit -m "FIX: Update navigation menu - Overview link and route corrections"
git push origin main
echo CHANGES COMMITTED AND PUSHED!
echo Render will deploy in ~5 minutes
pause
