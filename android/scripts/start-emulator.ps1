param(
    [string]$Name = "ONF_Fold_API36"
)

$ErrorActionPreference = "Stop"
$sdk = if ($env:ANDROID_SDK_ROOT) { $env:ANDROID_SDK_ROOT } else { Join-Path $env:LOCALAPPDATA "Android\Sdk" }
$emulator = Join-Path $sdk "emulator\emulator.exe"

if (-not (Test-Path $emulator)) {
    throw "Android Emulator not found at '$emulator'."
}

& $emulator -avd $Name -gpu auto -no-boot-anim -camera-back none -camera-front none
