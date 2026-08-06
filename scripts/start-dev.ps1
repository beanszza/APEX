# APEX Development Startup Script (PowerShell)

$ErrorActionPreference = "Stop"

Write-Host "==================================================" -ForegroundColor Cyan
Write-Host " Starting APEX Analytics Microservice (:5011)" -ForegroundColor Cyan
Write-Host "==================================================" -ForegroundColor Cyan

# 1. Activate virtual environment if present
if (Test-Path ".venv\Scripts\Activate.ps1") {
    Write-Host "[APEX] Activating virtual environment..." -ForegroundColor Green
    & .venv\Scripts\Activate.ps1
} else {
    Write-Host "[APEX] Warning: Virtual environment .venv not found. Running with global python." -ForegroundColor Yellow
}

# 2. Check databases
Write-Host "[APEX] Verifying database connectivity..." -ForegroundColor Green
python scripts/ensure-dbs.py

# 3. Launch Uvicorn server
Write-Host "[APEX] Starting Uvicorn server on http://localhost:5011..." -ForegroundColor Green
uvicorn app.main:app --reload --port 5011
