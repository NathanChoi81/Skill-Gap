# Run from anywhere. Ensures we're in backend dir and port 8000 is free, then starts the API.
$BackendDir = $PSScriptRoot
Set-Location $BackendDir

# Free port 8000 so the correct app runs
$conn = Get-NetTCPConnection -LocalPort 8000 -ErrorAction SilentlyContinue
if ($conn) {
    $conn | ForEach-Object { Stop-Process -Id $_.OwningProcess -Force -ErrorAction SilentlyContinue }
    Write-Host "Stopped process on port 8000." -ForegroundColor Yellow
    Start-Sleep -Seconds 1
}

Write-Host "Starting from: $(Get-Location)" -ForegroundColor Cyan
Write-Host "Open http://localhost:8000/ and http://localhost:8000/debug-session" -ForegroundColor Green
if (Test-Path '.venv\Scripts\Activate.ps1') { . '.venv\Scripts\Activate.ps1' }
elseif (Test-Path 'venv\Scripts\Activate.ps1') { . 'venv\Scripts\Activate.ps1' }
# Bind to 127.0.0.1 so localhost:8000 hits this server (avoids IPv6/other-interface confusion)
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
