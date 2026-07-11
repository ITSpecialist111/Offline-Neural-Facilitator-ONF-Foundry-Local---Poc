param(
    [switch]$WithAudio,
    [switch]$SkipModels
)

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
Set-Location $root

Write-Host "Installing ONF core dependencies..." -ForegroundColor Cyan
py -3.12 -m pip install -r requirements.txt

if ($WithAudio) {
    Write-Host "Installing optional transcription and speech dependencies..." -ForegroundColor Cyan
    py -3.12 -m pip install -r requirements-audio.txt

    Write-Host "Caching the configured Whisper and English speech-language models..." -ForegroundColor Cyan
    py -3.12 -c "import os; from faster_whisper.utils import download_model; download_model(os.environ.get('ONF_WHISPER_MODEL', 'medium'))"
    py -3.12 -c "from transformers import AutoModelForMaskedLM, AutoTokenizer; AutoTokenizer.from_pretrained('bert-base-uncased'); AutoModelForMaskedLM.from_pretrained('bert-base-uncased')"
    py -3.12 -c "from huggingface_hub import snapshot_download; snapshot_download('myshell-ai/MeloTTS-English', local_dir='audio_models/MeloTTS-English')"
}

Write-Host "Installing frontend dependencies..." -ForegroundColor Cyan
npm.cmd --prefix frontend install

if (-not $SkipModels) {
    if (-not (Get-Command foundry -ErrorAction SilentlyContinue)) {
        throw "Foundry Local CLI not found. Install it with: winget install Microsoft.FoundryLocal"
    }

    Write-Host "Starting Foundry Local and caching ONF models..." -ForegroundColor Cyan
    foundry service start
    foundry model download qwen2.5-0.5b --device GPU
    foundry model download deepseek-r1-1.5b --device GPU
}

Write-Host ""
Write-Host "Setup complete. Start ONF with .\scripts\start.ps1" -ForegroundColor Green