param(
    [switch]$FullValidation
)

$ErrorActionPreference = "Stop"
$androidRoot = Split-Path -Parent $PSScriptRoot
$repositoryRoot = Split-Path -Parent $androidRoot
$sdk = if ($env:ANDROID_SDK_ROOT) { $env:ANDROID_SDK_ROOT } else { Join-Path $env:LOCALAPPDATA "Android\Sdk" }
$javaHome = if ($env:JAVA_HOME) { $env:JAVA_HOME } else { "C:\Program Files\Android\Android Studio\jbr" }

if (-not (Test-Path (Join-Path $sdk "platform-tools\adb.exe"))) {
    throw "Android SDK not found at '$sdk'. Install Android Studio and the Android SDK first."
}
if (-not (Test-Path (Join-Path $javaHome "bin\java.exe"))) {
    throw "Java runtime not found at '$javaHome'."
}

$env:ANDROID_HOME = $sdk
$env:ANDROID_SDK_ROOT = $sdk
$env:JAVA_HOME = $javaHome

Push-Location $androidRoot
try {
    if ($FullValidation) {
        & .\gradlew.bat :app:testDebugUnitTest :app:lintDebug
        if ($LASTEXITCODE -ne 0) { throw "Android validation failed." }
    }

    & .\gradlew.bat :app:assembleDebug
    if ($LASTEXITCODE -ne 0) { throw "Android APK build failed." }
} finally {
    Pop-Location
}

$source = Join-Path $androidRoot "app\build\outputs\apk\debug\app-debug.apk"
$artifactDirectory = Join-Path $androidRoot "artifacts"
$artifact = Join-Path $artifactDirectory "ONF-Android-v0.1.0-alpha01-debug.apk"
New-Item -ItemType Directory -Path $artifactDirectory -Force | Out-Null
Copy-Item $source $artifact -Force

Write-Host ""
Write-Host "Sideload APK: $artifact" -ForegroundColor Green
