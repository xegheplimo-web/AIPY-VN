# Update script for VietStore RAG
Write-Host "=== VietStore RAG Update ===" -ForegroundColor Cyan

# Update dependencies
Write-Host "\n📦 Updating root dependencies..." -ForegroundColor Cyan
if (Get-Command pnpm -ErrorAction SilentlyContinue) {
    pnpm update
} else {
    npm update
}

# Update Python dependencies
Write-Host "\n🐍 Updating Python dependencies..." -ForegroundColor Cyan
cd apps/api-server
uv sync

Write-Host "\n✅ Update complete!" -ForegroundColor Green
