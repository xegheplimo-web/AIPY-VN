# Setup script for VietStore RAG
Write-Host "=== VietStore RAG Setup ===" -ForegroundColor Cyan

# Check Node.js
$nodeVersion = node --version 2>$null
if (-not $nodeVersion) {
    Write-Host "❌ Node.js not found. Please install Node.js >= 18." -ForegroundColor Red
    exit 1
}
Write-Host "✅ Node.js: $nodeVersion"

# Check Python
$pythonVersion = python --version 2>$null
if (-not $pythonVersion) {
    Write-Host "❌ Python not found. Please install Python >= 3.11." -ForegroundColor Red
    exit 1
}
Write-Host "✅ Python: $pythonVersion"

# Check Docker
$dockerVersion = docker --version 2>$null
if (-not $dockerVersion) {
    Write-Host "⚠️ Docker not found. You can still develop without Docker." -ForegroundColor Yellow
} else {
    Write-Host "✅ Docker: $dockerVersion"
}

# Install root dependencies
Write-Host "\n📦 Installing root dependencies..." -ForegroundColor Cyan
if (Get-Command pnpm -ErrorAction SilentlyContinue) {
    pnpm install
} else {
    npm install
}

# Start Docker services
Write-Host "\n🐳 Starting Docker services..." -ForegroundColor Cyan
docker compose up -d

Write-Host "\n✅ Setup complete!" -ForegroundColor Green
Write-Host "Next steps:"
Write-Host "  1. cd apps/api-server && uv run uvicorn src.main:app --reload"
Write-Host "  2. cd apps/web-customer && npm run dev"
