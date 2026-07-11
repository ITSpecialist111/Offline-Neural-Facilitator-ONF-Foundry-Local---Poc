param(
    [string]$Serial,
    [string]$ApkPath
)

$ErrorActionPreference = "Stop"
$androidRoot = Split-Path -Parent $PSScriptRoot
$sdk = if ($env:ANDROID_SDK_ROOT) { $env:ANDROID_SDK_ROOT } else { Join-Path $env:LOCALAPPDATA "Android\Sdk" }
$adb = Join-Path $sdk "platform-tools\adb.exe"

if (-not (Test-Path $adb)) {
    throw "ADB not found at '$adb'."
}
if (-not $ApkPath) {
    $ApkPath = Join-Path $androidRoot "artifacts\ONF-Android-v0.1.0-alpha01-debug.apk"
}
if (-not (Test-Path $ApkPath)) {
    throw "APK not found at '$ApkPath'. Run .\scripts\build.ps1 first."
}

$devices = & $adb devices -l | Select-Object -Skip 1 | Where-Object { $_ -match "\sdevice\s" }
if (-not $devices) {
    throw "No authorized Android device found. Connect the Fold7, enable USB debugging, unlock it, and accept the RSA prompt."
}

if (-not $Serial) {
    $physical = $devices | Where-Object { $_ -notmatch "^emulator-" } | Select-Object -First 1
    $candidate = if ($physical) { $physical } else { $devices | Select-Object -First 1 }
    $Serial = ($candidate -split "\s+")[0]
}

Write-Host "Installing ONF on $Serial..." -ForegroundColor Cyan
& $adb -s $Serial install -r -t (Resolve-Path $ApkPath).Path
if ($LASTEXITCODE -ne 0) { throw "APK installation failed on $Serial." }

& $adb -s $Serial shell monkey -p com.offlineneuralfacilitator.onf -c android.intent.category.LAUNCHER 1 | Out-Null
Write-Host "ONF installed and launched on $Serial." -ForegroundColor Green
