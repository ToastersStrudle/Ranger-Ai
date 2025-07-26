# Ranger AI Startup Script
Write-Host "🤖 Starting Ranger AI..." -ForegroundColor Green
Write-Host ""

# Check if Python is installed
try {
    $pythonVersion = python --version 2>&1
    Write-Host "✅ Python found: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "❌ Python not found! Please install Python 3.8 or higher." -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

# Check if main.py exists
if (-not (Test-Path "main.py")) {
    Write-Host "❌ main.py not found! Please run this script from the RangerAI directory." -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

# Check if config.json exists
if (-not (Test-Path "config.json")) {
    Write-Host "⚠️ config.json not found! Please run setup.py first." -ForegroundColor Yellow
    Write-Host "Run: python setup.py" -ForegroundColor Yellow
    Read-Host "Press Enter to exit"
    exit 1
}

# Start the bot
try {
    Write-Host "🚀 Launching Ranger AI..." -ForegroundColor Cyan
    python main.py
} catch {
    Write-Host "❌ Error starting Ranger AI: $_" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

Read-Host "Press Enter to exit" 