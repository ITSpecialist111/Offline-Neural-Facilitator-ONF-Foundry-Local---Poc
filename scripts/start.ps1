param(
    [switch]$NoBrowser,
    [switch]$SkipFoundry
)

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
Set-Location $root

if (-not (Get-Command py -ErrorAction SilentlyContinue)) {
    throw "Python launcher not found. Install Python 3.12 first."
}
if (-not (Get-Command npm.cmd -ErrorAction SilentlyContinue)) {
    throw "npm not found. Install Node.js 18 or newer first."
}
if (-not (Test-Path "frontend/node_modules")) {
    throw "Frontend dependencies are missing. Run .\scripts\setup.ps1 first."
}

if (-not $SkipFoundry -and (Get-Command foundry -ErrorAction SilentlyContinue)) {
    Write-Host "Starting Foundry Local..." -ForegroundColor DarkCyan
    & foundry service start

    # Loading is intentionally non-blocking. The UI reports readiness and the
    # deterministic showcase remains available while models warm.
    Start-Process -FilePath "foundry" -ArgumentList "model", "load", "qwen2.5-0.5b", "--device", "GPU", "--ttl", "3600" -WindowStyle Hidden | Out-Null
    Start-Process -FilePath "foundry" -ArgumentList "model", "load", "deepseek-r1-1.5b", "--device", "GPU", "--ttl", "3600" -WindowStyle Hidden | Out-Null
} elseif (-not $SkipFoundry) {
    Write-Warning "Foundry Local CLI was not found. The showcase and structured outcomes will still work."
}

Write-Host "Starting ONF backend..." -ForegroundColor Green
$backendProcess = Start-Process -FilePath "py" -ArgumentList "-3.12", "-m", "uvicorn", "backend.main:app", "--host", "127.0.0.1", "--port", "8000" -WorkingDirectory $root -PassThru -NoNewWindow

Write-Host "Starting ONF interface..." -ForegroundColor Cyan
$frontendProcess = Start-Process -FilePath "npm.cmd" -ArgumentList "run", "dev" -WorkingDirectory (Join-Path $root "frontend") -PassThru -NoNewWindow

try {
    $ready = $false
    for ($attempt = 0; $attempt -lt 60; $attempt++) {
        try {
            $response = Invoke-RestMethod -Uri "http://127.0.0.1:8000/" -TimeoutSec 1
            if ($response.status -eq "ready") {
                $ready = $true
                break
            }
        } catch {
            [System.Threading.Thread]::Sleep(500)
        }
    }

    if (-not $ready) {
        throw "The ONF backend did not become ready within 30 seconds."
    }

    Write-Host ""
    Write-Host "ONF is ready: http://127.0.0.1:5173" -ForegroundColor Green
    Write-Host "Press Ctrl+C to stop the application." -ForegroundColor DarkGray
    if (-not $NoBrowser) {
        Start-Process "http://127.0.0.1:5173"
    }

    while (-not $backendProcess.HasExited -and -not $frontendProcess.HasExited) {
        [System.Threading.Thread]::Sleep(500)
    }
}
finally {
    foreach ($process in @($backendProcess, $frontendProcess)) {
        if ($process -and -not $process.HasExited) {
            & taskkill.exe /PID $process.Id /T /F 2>$null | Out-Null
        }
    }
    Write-Host "ONF stopped." -ForegroundColor DarkGray
}
