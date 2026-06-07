# Setup environment variables for VietStore RAG
# Run this script to create .env file from .env.example

$envFile = "apps\api-server\.env"
$envExample = "apps\api-server\.env.example"

if (Test-Path $envFile) {
    Write-Host ".env file already exists. Skipping." -ForegroundColor Yellow
    $overwrite = Read-Host "Overwrite? (y/N)"
    if ($overwrite -ne "y") {
        exit
    }
}

Write-Host "Creating .env file from .env.example..." -ForegroundColor Green

# Copy example to .env
Copy-Item $envExample $envFile

Write-Host ".env file created successfully!" -ForegroundColor Green
Write-Host ""
Write-Host "IMPORTANT: Update the following values in .env:" -ForegroundColor Yellow
Write-Host "  - DATABASE_URL: Set your PostgreSQL credentials"
Write-Host "  - ECC_PRIVATE_KEY_PEM: Will be auto-generated on first run"
Write-Host "  - QDRANT_API_KEY: Set if using Qdrant cloud"
Write-Host ""
Write-Host "To start the application:"
Write-Host "  1. Start PostgreSQL: docker-compose up -d"
Write-Host "  2. Run migrations: cd apps/api-server && uv run alembic upgrade head"
Write-Host "  3. Start backend: cd apps/api-server && uv run uvicorn src.main:app --reload"
