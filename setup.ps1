Write-Host "Setting up Odisha Krishi AI Platform..." -ForegroundColor Green
Write-Host ""

Write-Host "Checking if Python is installed..." -ForegroundColor Yellow
try {
    $pythonVersion = python --version 2>&1
    Write-Host "Python found: $pythonVersion" -ForegroundColor Green
}
catch {
    Write-Host "Python is not installed. Please install Python 3.9+ from https://python.org" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

Write-Host "Checking if Node.js is installed..." -ForegroundColor Yellow
try {
    $nodeVersion = node --version 2>&1
    Write-Host "Node.js found: $nodeVersion" -ForegroundColor Green
}
catch {
    Write-Host "Node.js is not installed. Please install Node.js 18+ from https://nodejs.org" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

Write-Host ""
Write-Host "Setting up Frontend..." -ForegroundColor Yellow
Set-Location frontend
npm install
if ($LASTEXITCODE -ne 0) {
    Write-Host "Failed to install frontend dependencies" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

Write-Host ""
Write-Host "Setting up Backend..." -ForegroundColor Yellow
Set-Location ..\backend
python -m venv venv
& .\venv\Scripts\Activate.ps1
pip install -r requirements.txt
if ($LASTEXITCODE -ne 0) {
    Write-Host "Failed to install backend dependencies" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

Write-Host ""
Write-Host "Setting up ML Service..." -ForegroundColor Yellow
Set-Location ..\ml-service
python -m venv venv
& .\venv\Scripts\Activate.ps1
pip install -r requirements.txt
if ($LASTEXITCODE -ne 0) {
    Write-Host "Failed to install ML service dependencies" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

Write-Host ""
Write-Host "Setup completed successfully!" -ForegroundColor Green
Write-Host ""
Write-Host "To run the application:" -ForegroundColor Cyan
Write-Host "1. Open 3 separate PowerShell windows" -ForegroundColor White
Write-Host "2. Run 'npm start' in the frontend directory" -ForegroundColor White
Write-Host "3. Run 'uvicorn app:app --reload --port 8000' in the backend directory" -ForegroundColor White
Write-Host "4. Run 'uvicorn app:app --reload --port 8001' in the ml-service directory" -ForegroundColor White
Write-Host ""
Read-Host "Press Enter to exit"
