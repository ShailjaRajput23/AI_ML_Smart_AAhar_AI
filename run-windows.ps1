param(
  [string]$Port = "5051"
)

$ErrorActionPreference = "Stop"

Write-Host "SmartAahar Windows launcher" -ForegroundColor Cyan

if (-not (Test-Path ".venv311")) {
  Write-Host "Creating virtual environment (.venv311)..." -ForegroundColor Yellow
  py -3.11 -m venv .venv311
}

Write-Host "Activating virtual environment..." -ForegroundColor Yellow
. .\.venv311\Scripts\Activate.ps1

Write-Host "Installing dependencies (requirements-windows.txt)..." -ForegroundColor Yellow
python -m pip install --upgrade pip
pip install -r requirements-windows.txt

if (-not $env:SECRET_KEY) { $env:SECRET_KEY = "replace_with_long_random_secret" }
if (-not $env:SESSION_TIMEOUT_MINUTES) { $env:SESSION_TIMEOUT_MINUTES = "10" }
if (-not $env:MIN_FOOD_CONFIDENCE) { $env:MIN_FOOD_CONFIDENCE = "0.70" }
if (-not $env:MONGO_URI) { $env:MONGO_URI = "mongodb://localhost:27017/" }

Write-Host "Starting Flask app on port $Port..." -ForegroundColor Green
flask --app app run --debug --port $Port
