#!/usr/bin/env powershell
# PowerShell script to start the Stock Scanner backend

Write-Host "Starting Stock Scanner Backend..." -ForegroundColor Green
Write-Host ""

# Check if virtual environment exists
if (-not (Test-Path "venv\Scripts\Activate.ps1")) {
    Write-Host "ERROR: Virtual environment not found!" -ForegroundColor Red
    Write-Host "Please run: python -m venv venv" -ForegroundColor Yellow
    Write-Host "Then run: pip install -r requirements.txt" -ForegroundColor Yellow
    Read-Host "Press Enter to exit"
    exit 1
}

# Activate virtual environment
Write-Host "Activating virtual environment..." -ForegroundColor Blue
& ".\venv\Scripts\Activate.ps1"

# Check if dependencies are installed
try {
    python -c "import pydantic_settings" 2>$null
    if ($LASTEXITCODE -ne 0) {
        throw "Dependencies not installed"
    }
} catch {
    Write-Host "Installing/updating dependencies..." -ForegroundColor Yellow
    pip install -r requirements.txt
}

# Start the server
Write-Host ""
Write-Host "Starting FastAPI server..." -ForegroundColor Green
Write-Host "Server will be available at: http://localhost:8000" -ForegroundColor Cyan
Write-Host "API Documentation: http://localhost:8000/docs" -ForegroundColor Cyan
Write-Host ""
Write-Host "Press Ctrl+C to stop the server" -ForegroundColor Yellow
Write-Host ""

python run_server.py