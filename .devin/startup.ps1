# ============================================================================
# .devin/startup.ps1 - AI Coding Auto-Startup System (PowerShell Wrapper)
# Thin wrapper that delegates to startup.py for cross-platform reliability
# ============================================================================
#Requires -Version 5.1
param(
    [string]$ProjectRoot = (Split-Path $PSScriptRoot -Parent)
)

$pyScript = Join-Path $PSScriptRoot "startup.py"

# Prefer python3 or python
$python = Get-Command python3 -ErrorAction SilentlyContinue
if (-not $python) { $python = Get-Command python -ErrorAction SilentlyContinue }
if (-not $python) { $python = Get-Command py -ErrorAction SilentlyContinue }

if (-not $python) {
    Write-Host "ERROR: Python not found in PATH. Cannot run startup script." -ForegroundColor Red
    exit 1
}

& $python.Source $pyScript
exit $LASTEXITCODE
