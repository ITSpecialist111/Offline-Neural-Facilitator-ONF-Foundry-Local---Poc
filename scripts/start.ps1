
# Start the Offline Neural Facilitator (backend + frontend).
# Settings are read from .env (see .env.example). Host/port can be overridden
# via the ONF_HOST / ONF_PORT environment variables.
$onfHost = if ($env:ONF_HOST) { $env:ONF_HOST } else { "127.0.0.1" }
$onfPort = if ($env:ONF_PORT) { $env:ONF_PORT } else { "8000" }

# Start Backend
Write-Host "Starting Backend (Python 3.12) on ${onfHost}:${onfPort}..." -ForegroundColor Green
$backendProcess = Start-Process -FilePath "py" -ArgumentList "-3.12", "-m", "uvicorn", "backend.main:app", "--host", $onfHost, "--port", $onfPort, "--reload" -PassThru -NoNewWindow

# Start Frontend
Write-Host "Starting Frontend..." -ForegroundColor Cyan
Set-Location frontend
$frontendProcess = Start-Process -FilePath "npm.cmd" -ArgumentList "run", "dev" -PassThru -NoNewWindow
Set-Location ..

Write-Host "Both services started. Press Ctrl+C to stop." -ForegroundColor Yellow

# Wait for user input to kill
try {
    while ($true) {
        Start-Sleep -Seconds 1
        if ($backendProcess.HasExited) { Write-Host "Backend exited." -ForegroundColor Red; break }
        # Frontend via npm might spawn callbacks, checking process object might be tricky if it's a wrapper, but good enough.
    }
}
finally {
    Stop-Process -Id $backendProcess.Id -ErrorAction SilentlyContinue
    Stop-Process -Id $frontendProcess.Id -ErrorAction SilentlyContinue
    Write-Host "Services stopped."
}
