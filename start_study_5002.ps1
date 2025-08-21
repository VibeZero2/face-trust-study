Set-Location "C:\Users\Chris\CascadeProjects\facial-trust-study"
$env:PORT = "5002"
Write-Host "Starting facial trust study on port 5002..."
Write-Host "Navigate to: http://localhost:5002"
python app.py
