# Run all tests (backend pytest + frontend unit). Run from repo root: .\scripts\run-tests.ps1
$Root = (Get-Item $PSScriptRoot).Parent.FullName
$BackendDir = Join-Path $Root "backend"
$FrontendDir = Join-Path $Root "frontend"
$Failed = 0

Write-Host "`n=== Backend tests (pytest) ===" -ForegroundColor Cyan
Push-Location $BackendDir
try {
    if (Test-Path '.venv\Scripts\Activate.ps1') { . '.venv\Scripts\Activate.ps1' }
    elseif (Test-Path 'venv\Scripts\Activate.ps1') { . 'venv\Scripts\Activate.ps1' }
    python -m pytest tests -v --tb=short
    if ($LASTEXITCODE -ne 0) { $Failed = 1 }
} finally {
    Pop-Location
}

Write-Host "`n=== Frontend unit tests (vitest) ===" -ForegroundColor Cyan
Push-Location $FrontendDir
try {
    npm run test
    if ($LASTEXITCODE -ne 0) { $Failed = 1 }
} finally {
    Pop-Location
}

if ($Failed -eq 1) {
    Write-Host "`nOne or more test runs failed." -ForegroundColor Red
    exit 1
}
Write-Host "`nAll tests passed." -ForegroundColor Green
exit 0
