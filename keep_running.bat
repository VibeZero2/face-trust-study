@echo off
cd /d "C:\Users\Chris\CascadeProjects\facial-trust-study"
:loop
python app.py
echo Flask stopped, restarting in 5 seconds...
timeout /t 5
goto loop
