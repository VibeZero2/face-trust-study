@echo off
setlocal

echo Starting Facial Trust Study...
echo =============================

:: Set Python path to include the project directory
set PYTHONPATH=%CD%;%PYTHONPATH%

:: Install required packages
echo Installing required packages...
pip install -r requirements.txt

:: Create necessary directories
mkdir data\responses 2>nul

:: Start the application
echo Starting the application...
start "" http://localhost:3000
python -c "from app import app; app.run(host='0.0.0.0', port=3000, debug=True)"

pause
