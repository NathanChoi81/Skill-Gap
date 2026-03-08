# Launch backend and frontend in two separate windows. Run from repo root: .\scripts\launch-dev.ps1
$Root = (Get-Item $PSScriptRoot).Parent.FullName
$BackendDir = Join-Path $Root "backend"
$FrontendDir = Join-Path $Root "frontend"

# Free port 8001 so the new backend can bind (optional; close the backend window to stop).
try {
    $conn = Get-NetTCPConnection -LocalPort 8001 -ErrorAction SilentlyContinue
    if ($conn) {
        $conn | ForEach-Object { Stop-Process -Id $_.OwningProcess -Force -ErrorAction SilentlyContinue }
        Write-Host "Stopped existing process on port 8001." -ForegroundColor Yellow
        Start-Sleep -Seconds 2
    }
} catch {}

Write-Host "Starting backend in new window..." -ForegroundColor Cyan
$backendCmd = @"
Set-Location '$BackendDir'
if (Test-Path '.venv\Scripts\Activate.ps1') { . '.venv\Scripts\Activate.ps1' }
elseif (Test-Path 'venv\Scripts\Activate.ps1') { . 'venv\Scripts\Activate.ps1' }
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8001
"@
Start-Process powershell -ArgumentList "-NoExit", "-Command", $backendCmd

Start-Sleep -Seconds 2

Write-Host "Starting frontend in new window..." -ForegroundColor Cyan
$frontendCmd = @"
Set-Location '$FrontendDir'
npm run dev
"@
Start-Process powershell -ArgumentList "-NoExit", "-Command", $frontendCmd

Write-Host "Backend: http://localhost:8001" -ForegroundColor Green
Write-Host "Frontend: http://localhost:5173" -ForegroundColor Green
Write-Host "Close the two new windows to stop." -ForegroundColor Yellow
