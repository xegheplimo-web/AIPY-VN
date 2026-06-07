# Run script for VietStore RAG
param(
    [Parameter()]
    [ValidateSet("backend", "frontend", "all")]
    [string]$Service = "all"
)

Write-Host "=== VietStore RAG Run ===" -ForegroundColor Cyan

if ($Service -eq "backend" -or $Service -eq "all") {
    Write-Host "\n🚀 Starting backend..." -ForegroundColor Cyan
    Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd apps/api-server; `$env:PYTHONPATH='A:\AIPY\vietstore-rag\apps\api-server'; uv run uvicorn src.main:app --reload --port 9000"
}

if ($Service -eq "frontend" -or $Service -eq "all") {
    Write-Host "\n🚀 Starting frontend..." -ForegroundColor Cyan
    Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd apps/web-customer; npm run dev"
}

Write-Host "\n✅ Services started!" -ForegroundColor Green
Write-Host "  Backend: http://127.0.0.1:9000"
Write-Host "  Frontend: http://localhost:3000"
Write-Host "  API Docs: http://localhost:8000/docs"
