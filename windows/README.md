# ONF Windows Portable

The Windows package is a one-folder portable application built with Python 3.12 and PyInstaller. It embeds the production React interface and FastAPI backend in one `ONF.exe` lifecycle, so end users do not need Python, Node.js, npm, Vite, VS Code, or a terminal.

## Run

1. Download and extract the complete portable ZIP.
2. Double-click `ONF.exe` or `Start ONF.cmd`.
3. Use the Windows notification-area icon to reopen ONF, open its data folder, view logs, or exit.

The browser UI is deliberate: Chromium/Edge provides reliable secure-context microphone and `MediaRecorder` behavior while the server remains restricted to `127.0.0.1:8765`.

## Runtime boundaries

- Compiled React files are served by the internal FastAPI process.
- Mutable state is stored beside the executable under `data/`, with a `%LOCALAPPDATA%\OfflineNeuralFacilitator` fallback for read-only locations.
- Microsoft Foundry Local is an external Microsoft dependency. If installed, `ONF.exe` starts its service and requests Qwen 2.5 0.5B plus DeepSeek R1 1.5B. Model weights remain in Foundry's own cache.
- The deterministic showcase, local hash RAG, skills, outcomes, and exports work without Foundry.
- Faster-whisper runtime libraries are bundled, but Whisper weights are not. Runtime downloads are disabled and packaged transcription uses CPU against a compatible model already in the Windows user's Hugging Face cache.
- MeloTTS/PyTorch/checkpoints are excluded from this compact alpha; speech output remains standby.
- Chroma anonymized telemetry is explicitly disabled.

## Build

From the repository root on Windows:

```powershell
.\scripts\build-portable.ps1
```

The script creates an isolated Python 3.12 build environment by default, compiles and lints the frontend, builds the one-folder executable, launches the frozen binary, verifies its embedded UI, runs the canonical deterministic smoke suite, and emits a ZIP plus SHA-256 manifest under the ignored `windows/artifacts/` directory.

## Validated release gates

- launches from an extracted temporary directory with Python and Node removed from `PATH`;
- serves the embedded React HTML, CSS, and JavaScript;
- creates portable Chroma/session/log data;
- passes health/privacy, WebSocket, Code Blue, structured query, JSON, Markdown, PDF, and session persistence tests;
- starts installed Foundry Local and produces a real local Qwen response;
- transcribes a real WAV through the packaged faster-whisper runtime on CPU;
- includes Windows icon and product version metadata.

This is an unsigned experimental alpha. Production distribution should add trusted Windows code signing and, if desired, an installer that creates Start-menu shortcuts without changing the portable runtime design.
