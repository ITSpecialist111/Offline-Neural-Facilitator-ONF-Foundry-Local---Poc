param(
    [string]$Version = "2.0.0-alpha01",
    [string]$PythonExecutable,
    [switch]$SkipDependencyInstall,
    [switch]$SkipSmoke
)

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
$venv = Join-Path $root "build\portable-venv"
$venvPython = if ($PythonExecutable) { (Resolve-Path $PythonExecutable).Path } else { Join-Path $venv "Scripts\python.exe" }
$requirements = Join-Path $root "windows\requirements-portable.txt"
$spec = Join-Path $root "windows\onf-portable.spec"
$distRoot = Join-Path $root "dist"
$bundle = Join-Path $distRoot "ONF-Windows-Portable"
$work = Join-Path $root "build\onf-pyinstaller"
$artifacts = Join-Path $root "windows\artifacts"
$zip = Join-Path $artifacts "ONF-Windows-Portable-v$Version.zip"
$checksumFile = [System.IO.Path]::ChangeExtension($zip, ".sha256.txt")

if (-not (Get-Command py -ErrorAction SilentlyContinue)) {
    throw "The Python launcher is required to build ONF Portable."
}
if (-not (Get-Command npm.cmd -ErrorAction SilentlyContinue)) {
    throw "Node.js/npm is required to compile the ONF interface."
}

if (-not $PythonExecutable -and -not (Test-Path $venvPython)) {
    Write-Host "Creating isolated Python 3.12 portable-build environment..." -ForegroundColor Cyan
    & py -3.12 -m venv $venv
    if ($LASTEXITCODE -ne 0) { throw "Unable to create the Python 3.12 build environment." }
}

if (-not $SkipDependencyInstall) {
    Write-Host "Installing portable runtime and packaging dependencies..." -ForegroundColor Cyan
    & $venvPython -m pip install --upgrade pip
    if ($LASTEXITCODE -ne 0) { throw "Unable to update pip in the portable-build environment." }
    & $venvPython -m pip install -r $requirements
    if ($LASTEXITCODE -ne 0) { throw "Unable to install portable-build dependencies." }
}

Write-Host "Compiling the production React interface..." -ForegroundColor Cyan
& npm.cmd --prefix (Join-Path $root "frontend") ci --no-audit --no-fund
if ($LASTEXITCODE -ne 0) { throw "Frontend dependency installation failed." }
& npm.cmd --prefix (Join-Path $root "frontend") run lint
if ($LASTEXITCODE -ne 0) { throw "Frontend lint failed." }
& npm.cmd --prefix (Join-Path $root "frontend") run build
if ($LASTEXITCODE -ne 0) { throw "Frontend production build failed." }

Write-Host "Building the Windows portable application..." -ForegroundColor Cyan
& $venvPython (Join-Path $root "windows\create_icon.py") (Join-Path $root "windows\onf.ico")
if ($LASTEXITCODE -ne 0) { throw "Unable to generate the ONF Windows icon." }
Remove-Item $bundle -Recurse -Force -ErrorAction SilentlyContinue
Remove-Item $work -Recurse -Force -ErrorAction SilentlyContinue
& $venvPython -m PyInstaller --noconfirm --clean --distpath $distRoot --workpath $work $spec
if ($LASTEXITCODE -ne 0) { throw "PyInstaller failed to build ONF Portable." }

Copy-Item (Join-Path $root "windows\README-PORTABLE.txt") (Join-Path $bundle "README-PORTABLE.txt") -Force
Copy-Item (Join-Path $root "windows\Start ONF.cmd") (Join-Path $bundle "Start ONF.cmd") -Force
Copy-Item (Join-Path $root "LICENSE") (Join-Path $bundle "LICENSE") -Force
@(
    "Offline Neural Facilitator Windows Portable",
    "Version: $Version",
    "Built: $([DateTime]::UtcNow.ToString('u')) UTC",
    "Entry point: ONF.exe",
    "Frontend: embedded production React build",
    "Mutable data: .\data (created on first launch)"
) | Set-Content (Join-Path $bundle "BUILD-INFO.txt") -Encoding utf8

if (-not $SkipSmoke) {
    Write-Host "Running the packaged application smoke suite..." -ForegroundColor Cyan
    $smokeData = Join-Path $root "build\portable-smoke-data"
    Remove-Item $smokeData -Recurse -Force -ErrorAction SilentlyContinue
    $previousDataDir = $env:ONF_DATA_DIR
    $env:ONF_DATA_DIR = $smokeData
    $portable = Start-Process -FilePath (Join-Path $bundle "ONF.exe") -ArgumentList "--no-browser", "--no-foundry" -PassThru
    try {
        $ready = $false
        for ($attempt = 0; $attempt -lt 180; $attempt++) {
            try {
                $status = Invoke-RestMethod -Uri "http://127.0.0.1:8765/api/status" -TimeoutSec 1
                if ($status.status -eq "ready") {
                    $ready = $true
                    break
                }
            } catch {
                [System.Threading.Thread]::Sleep(500)
            }
        }
        if (-not $ready) { throw "The packaged application did not become ready." }

        $rootResponse = Invoke-WebRequest -UseBasicParsing -Uri "http://127.0.0.1:8765/" -TimeoutSec 5
        if ($rootResponse.StatusCode -ne 200 -or $rootResponse.Content -notmatch '<div id="root"></div>') {
            throw "The packaged application did not serve the embedded React interface."
        }

        $env:ONF_TEST_BASE_URL = "http://127.0.0.1:8765"
        & $venvPython (Join-Path $root "smoke_test_v2.py")
        if ($LASTEXITCODE -ne 0) { throw "The packaged ONF smoke suite failed." }
    } finally {
        Remove-Item Env:ONF_TEST_BASE_URL -ErrorAction SilentlyContinue
        if ($null -eq $previousDataDir) {
            Remove-Item Env:ONF_DATA_DIR -ErrorAction SilentlyContinue
        } else {
            $env:ONF_DATA_DIR = $previousDataDir
        }
        if ($portable -and -not $portable.HasExited) {
            Stop-Process -Id $portable.Id -Force -ErrorAction SilentlyContinue
        }
    }
}

Write-Host "Creating portable ZIP..." -ForegroundColor Cyan
New-Item -ItemType Directory -Path $artifacts -Force | Out-Null
Remove-Item $zip -Force -ErrorAction SilentlyContinue
Remove-Item $checksumFile -Force -ErrorAction SilentlyContinue
Compress-Archive -Path (Join-Path $bundle "*") -DestinationPath $zip -CompressionLevel Optimal
$checksum = (Get-FileHash $zip -Algorithm SHA256).Hash
Set-Content -Path $checksumFile -Value "$checksum  $(Split-Path -Leaf $zip)" -Encoding ascii

Write-Host ""
Write-Host "Portable application: $bundle" -ForegroundColor Green
Write-Host "Portable ZIP:         $zip" -ForegroundColor Green
Write-Host "SHA-256:              $checksum" -ForegroundColor Green
