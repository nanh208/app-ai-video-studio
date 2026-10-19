# OpenMontage Studio Launcher for PowerShell
Write-Host "========================================================" -ForegroundColor Cyan
Write-Host "              OPENMONTAGE STUDIO LAUNCHER               " -ForegroundColor Yellow
Write-Host "========================================================" -ForegroundColor Cyan

Set-Location -Path $PSScriptRoot

Write-Host "Starting Remotion Studio on http://localhost:3000..." -ForegroundColor Green
Start-Process -FilePath "cmd.exe" -ArgumentList "/k cd remotion-composer && npx remotion studio" -WindowStyle Minimized

Start-Sleep -Seconds 3

Write-Host "Starting Backlot Board on http://127.0.0.1:4750..." -ForegroundColor Green
Start-Process -FilePath "cmd.exe" -ArgumentList "/k .\.venv\Scripts\python.exe -m backlot serve --port 4750" -WindowStyle Minimized

Start-Sleep -Seconds 2

Start-Process "http://127.0.0.1:4750"

Write-Host "`nOpenMontage Studio is now running!" -ForegroundColor Cyan
Write-Host "1. Backlot Living Storyboard: http://127.0.0.1:4750" -ForegroundColor White
Write-Host "2. Remotion Video Editor:     http://localhost:3000`n" -ForegroundColor White
