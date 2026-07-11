OFFLINE NEURAL FACILITATOR — WINDOWS PORTABLE
================================================

START
1. Extract the complete ZIP to a normal writable folder.
2. Double-click ONF.exe.
3. ONF opens in your default browser and remains available from the ONF
   notification-area icon. Right-click that icon to reopen ONF, open its data
   folder, view the log, or exit cleanly.

Do not run ONF.exe from inside the ZIP and do not move ONF.exe out of its
portable folder. The adjacent _internal folder is required.

PORTABLE DATA
ONF creates a data folder beside ONF.exe. It contains sessions, the local
knowledge database, uploaded skills, generated audio, and logs. Keep or move
that folder with the application if you want to retain your data. If the
portable folder is not writable, ONF falls back to:
  %LOCALAPPDATA%\OfflineNeuralFacilitator

LOCAL AI
Microsoft Foundry Local remains a separately installed Microsoft runtime. When
its `foundry` CLI is available, ONF starts the local service and requests the
Qwen 2.5 0.5B and DeepSeek R1 1.5B models without showing extra consoles.
Install Foundry Local separately and cache the models before working offline.
The deterministic showcase, local knowledge, skills, structured outcomes, and
exports continue to work if Foundry is unavailable.

TRANSCRIPTION AND SPEECH
The portable bundle includes the faster-whisper runtime but does not include
multi-gigabyte Whisper weights. It can use a compatible model already present
in the current Windows user's Hugging Face cache. Runtime downloads remain
disabled by default. MeloTTS and its PyTorch/checkpoint stack are not bundled in
this first portable build; local speech output reports standby instead of
silently downloading assets.

PRIVACY
The application binds only to 127.0.0.1. It contains no application analytics
or telemetry SDK. Initial dependency/model provisioning is separate from local
meeting-time operation. Foundry Local has its own Microsoft runtime terms.

TROUBLESHOOTING
- Browser did not open: right-click the ONF tray icon and choose Open ONF.
- Port conflict/start failure: open data\logs\onf-desktop.log.
- Microphone access: allow microphone permission for http://127.0.0.1:8765 in
  your browser.
- Exit: right-click the tray icon and choose Exit ONF.

This is an unsigned experimental portable alpha. Windows SmartScreen may warn
about an unrecognized publisher. A code-signed installer/portable release is a
future distribution-hardening milestone.
