# Face Perception Study System - One Click Startup
Write-Host "========================================" -ForegroundColor Green
Write-Host "   FACE PERCEPTION STUDY SYSTEM" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""

Write-Host "Starting both programs..." -ForegroundColor Yellow
Write-Host ""

# Start Dashboard
Write-Host "[1/2] Starting Dashboard on port 5000..." -ForegroundColor Cyan
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd 'C:\Users\Chris\CascadeProjects\face-viewer-dashboard'; python dashboard_app.py" -WindowStyle Normal

Start-Sleep -Seconds 3

# Start Study Program
Write-Host "[2/2] Starting Study Program on port 8080..." -ForegroundColor Cyan
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd 'C:\Users\Chris\CascadeProjects\facial-trust-study'; python WORKING_STUDY.py" -WindowStyle Normal

Start-Sleep -Seconds 3

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "   BOTH PROGRAMS ARE STARTING" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "Dashboard: http://localhost:5000" -ForegroundColor White
Write-Host "Study Program: http://localhost:8080" -ForegroundColor White
Write-Host ""

# Open browsers
Write-Host "Opening dashboard in browser..." -ForegroundColor Yellow
Start-Process "http://localhost:5000"

Write-Host "Opening study program in browser..." -ForegroundColor Yellow
Start-Process "http://localhost:8080"

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "   SYSTEM READY!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "Both programs should now be running." -ForegroundColor White
Write-Host "Check the PowerShell windows for any errors." -ForegroundColor White
Write-Host ""
Read-Host "Press Enter to close this window"
