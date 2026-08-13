#!/usr/bin/env pwsh
# Start the Flask backend with a local virtual environment (Windows PowerShell)
Set-StrictMode -Version Latest
Push-Location $PSScriptRoot\..\
if (-not (Test-Path -Path .venv)) {
    Write-Host "Creating virtual environment .venv..."
    python -m venv .venv
}
Write-Host "Activating virtual environment..."
. .\.venv\Scripts\Activate.ps1
Write-Host "Installing Python dependencies..."
pip install -r requirements.txt
Write-Host "Starting Flask API (http://127.0.0.1:5000)..."
python api\index.py
Pop-Location
