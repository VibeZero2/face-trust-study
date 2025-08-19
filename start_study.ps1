Set-Location "C:\Users\Chris\CascadeProjects\facial-trust-study"
$env:PORT = "5001"
Write-Host "Starting facial trust study on port 5001..."
Write-Host "Navigate to: http://localhost:5001"
python app.py
