# Offline Neural Facilitator (ONF) v2.0.0

**Privacy-First, Offline AI Meeting Facilitator powered by Microsoft Foundry Local**

The Offline Neural Facilitator (ONF) transforms your PC into an intelligent meeting facilitator that listens, understands, and proactively assists - running entirely on your local machine by default, with an optional opt-in hybrid-online mode for more powerful models when you want it.

## Architecture

```
Frontend (React 19 + Vite)     Backend (FastAPI + WebSockets)     AI Engine
 localhost:5173            -->   localhost:8000              -->   Foundry Local (auto endpoint)
   Live Transcript                /transcribe                      Qwen 2.5 0.5B (Reflex)
   Insights Dashboard             /chat, /health                   Qwen 2.5 1.5B / DeepSeek R1 (Reason)
   Chat Widget                    /ws/stream                       faster-whisper (ASR, optional)
   Analytics                      /report/generate                 Web Speech API / MeloTTS (TTS)
                                  /skills, /upload-knowledge       ChromaDB (RAG, in-memory fallback)
                                  (optional) Hybrid online model    OpenAI-compatible cloud (opt-in)
```

> **Reliability by design:** every heavy component (Whisper, TTS, ChromaDB,
> diarization, vision) is optional and lazily initialized. The backend always
> boots; missing or failing components degrade gracefully and are reported via
> `GET /health` instead of crashing the app. See
> [Reliability & Graceful Degradation](#reliability--graceful-degradation).

## Key Features

### Dual-Engine Intelligence
- **Reflex Engine (Qwen 2.5 0.5B)**: Fast, low-latency responses for chat, topic detection, action items, and summaries.
- **Deep Reason Engine (Qwen 2.5 1.5B / DeepSeek R1)**: Heavier reasoning activated via "Deep Think" toggle for conflict analysis, compliance, and strategy. Models are configurable by alias (see Configuration).
- **Optional Hybrid Online**: Strictly opt-in routing of "Deep Think" requests to a more powerful OpenAI-compatible cloud model. Disabled by default — nothing leaves the device unless you enable it.

### Continuous Listening & Transcription
- **Real-time ASR**: Uses `faster-whisper` (medium model) with CUDA/CPU fallback and VAD filtering.
- **Speaker Diarization**: Distinguishes between multiple speakers.
- **WebSocket Streaming**: Live audio capture from browser microphone via `MediaRecorder` API.

### Proactive Intelligence
- **Smart Loop**: Automatically scans conversation every 15 seconds for dynamics.
- **RAG Knowledge Surfacing**: Pushes relevant insights from your Knowledge Vault when it detects matching topics.
- **Cognitive Load Detection**: Alerts when conversation density exceeds threshold.
- **Conflict Detection**: Keyword + LLM-based conflict identification with DeepSeek intervention strategy.

### Knowledge & Skills System
- **RAG Vault**: Upload PDF/Text files to a ChromaDB vector database for semantic search.
- **Skills System**: Load specialized personas via `SKILL.md` files (YAML frontmatter + instructions).
- **Built-in Skills**: Facilitator Core, Crisis Manager, Strategy Consultant, Legal Compliance.

### Data Portability
- **Report Generation**: Export meeting summaries to Markdown, JSON, CSV, or PDF.
- **Session Persistence**: Full session save/load to JSON files.
- **Analytics Dashboard**: Meeting Health score, talk balance metrics, action items grid.

### Text-to-Speech
- **Browser Web Speech API (default)**: Reliable, fully offline, zero-dependency speech synthesis in the browser.
- **Optional backend TTS (MeloTTS + OpenVoice)**: AI-generated speech with voice cloning, enabled via `ONF_ENABLE_TTS` when the optional dependencies are installed. The frontend automatically falls back to the browser voice when backend TTS is unavailable.
- **In-app Playback**: "Play" button on insights to hear them spoken aloud.

## Microsoft Foundry Local Integration

This project uses **Microsoft Azure AI Foundry Local** (Public Preview) for all LLM inference. Foundry Local runs models entirely on-device with no cloud dependency.

### Current Compatibility
| Component | Version | Notes |
|---|---|---|
| **Foundry Local CLI** | latest | Install via `winget install Microsoft.FoundryLocal` |
| **Python SDK** | `foundry-local-sdk` | `pip install foundry-local-sdk` |
| **Inference Endpoint** | auto-resolved | OpenAI-compatible; the SDK resolves a dynamic endpoint (no hardcoded port) |
| **API Key** | not required | Local inference needs no key |

The engine uses the Foundry Local SDK to start the service and resolve the
endpoint and model id automatically. If the SDK is unavailable it falls back to
a configurable endpoint (`ONF_FOUNDRY_ENDPOINT`). Models are referenced by
catalog alias (`foundry model ls`), e.g. `qwen2.5-0.5b`, `qwen2.5-1.5b`,
`deepseek-r1-7b`, `phi-4-mini`.

### Supported Hardware Acceleration
| Provider | Hardware | Status |
|---|---|---|
| CUDA | NVIDIA RTX 30xx+ | Built-in, recommended |
| WebGPU (Dawn) | Any GPU | Built-in fallback |
| CPU (MLAS) | Any CPU | Built-in fallback |
| OpenVINO | Intel 11th Gen+ | Plugin, auto-downloaded |
| QNN | Qualcomm Snapdragon X | Plugin, auto-downloaded |
| NvTensorRTRTX | NVIDIA RTX 30xx+ | Plugin, auto-downloaded |

### Recent Foundry Local Updates (as of March 2026)
- **Tool Calling** (v0.8.113+): Function calling support for compatible models.
- **Built-in Whisper**: On-device audio transcription via `whisper-tiny` model.
- **Continuous Decoding**: Multi-turn KV-cache for improved conversation performance.
- **AMD/Intel NPU Support** (v0.7.117+): Pluggable execution providers.
- **Documentation URL Change**: Docs moved from `/azure/ai-foundry/foundry-local/` to `/azure/foundry-local/`.

## Requirements

1. **Windows 10/11** (macOS/Linux partial support via cross-platform SDK)
2. **Python 3.12+**
3. **Node.js 18+** (for frontend)
4. **Microsoft Foundry Local CLI** (`winget install Microsoft.FoundryLocal`)
5. **NVIDIA GPU** (recommended for CUDA acceleration, but CPU works)
6. **Microphone** (for live transcription)
7. **FFmpeg** (for audio processing)

## Quick Start

### 1. Install Foundry Local
```powershell
winget install Microsoft.FoundryLocal
```

### 2. Install Python Dependencies
```bash
# Core dependencies (keeps the backend lean and always-bootable)
pip install -r requirements.txt

# Optional: heavy on-device capabilities (Whisper ASR, diarization, backend TTS, vision)
pip install -r requirements-optional.txt
```

### 3. Configure (optional)
All settings have safe offline-first defaults. To customize, copy the example
environment files and edit them:
```bash
cp .env.example .env                 # backend settings (ONF_* variables)
cp frontend/.env.example frontend/.env   # frontend API base (VITE_API_BASE)
```

### 4. Install Frontend Dependencies
```bash
cd frontend && npm install
```

### 5. Start the Application
```powershell
./scripts/start.ps1      # Windows (PowerShell)
```
```bash
./scripts/start.sh       # macOS / Linux / Git Bash
```
This launches both the backend (FastAPI on port 8000) and frontend (Vite on port 5173).

### 6. Access the UI
Open your browser to `http://localhost:5173`

Check backend status any time at `http://localhost:8000/health` — it reports
which components are active and which have gracefully degraded.

## Project Structure

```
backend/
  config.py                  # Central env-driven settings (all ONF_* toggles)
  main.py                    # FastAPI server (single lifespan startup, /health, all endpoints)
  llm/
    foundry_manager.py       # Resilient FoundryEngine (offline + opt-in hybrid online)
  services/
    voice_service.py         # Core orchestration (the "brain"), fault-isolated init
    rag_service.py           # ChromaDB vector store with in-memory keyword fallback
    transcription_service.py # faster-whisper ASR (lazy, optional)
    tts_service.py           # Optional backend TTS (MeloTTS + OpenVoice)
    diarization_service.py   # Speaker separation (optional)
    agenda_service.py        # Topic detection
    report_service.py        # Markdown/PDF report generation
    skill_service.py         # SKILL.md loader and trigger system
    vision_service.py        # Screenshot capture via pyautogui (optional)

frontend/
  src/
    config.js                # API/WebSocket base URL (VITE_API_BASE)
    speech.js                # TTS helper: backend TTS -> browser Web Speech fallback
    App.jsx                  # Main React app (three-panel layout)
    components/
      ChatWidget.jsx         # Floating "Ask the Facilitator" chat
      AnalyticsDashboard.jsx # Session health and metrics
      VADIndicator.jsx       # Voice activity detection indicator

skills/                      # Modular AI personas (SKILL.md files)
  facilitator_core.md
  crisis_manager.md
  strategy_consultant.md
  legal_compliance/SKILL.md

scripts/
  start.ps1                 # PowerShell launcher (Windows)
  start.sh                  # Bash launcher (macOS/Linux/Git Bash)

.env.example                # Backend configuration template
frontend/.env.example       # Frontend configuration template
requirements.txt            # Core dependencies (always-bootable backend)
requirements-optional.txt   # Optional heavy on-device capabilities
smoke_test.py               # Dependency-light graceful-degradation smoke test
```

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/` | Service banner |
| `GET` | `/health` | Component status (active / degraded) |
| `POST` | `/transcribe` | Upload audio for transcription + LLM response |
| `POST` | `/chat` | Direct text chat with RAG context |
| `POST` | `/tts/speak` | Text-to-speech generation |
| `POST` | `/action-items` | Extract action items from conversation |
| `POST` | `/summary` | Generate conversation summary |
| `POST` | `/upload-knowledge` | Add text to knowledge vault |
| `POST` | `/upload-file` | Upload PDF/TXT to vault |
| `POST` | `/agenda/check` | Detect current meeting topic |
| `GET` | `/skills` | List loaded skills |
| `POST` | `/skills/upload` | Upload new SKILL.md |
| `POST` | `/report/generate` | Generate Markdown report |
| `POST` | `/report/export/pdf` | Generate PDF report |
| `POST` | `/session/save` | Save session to JSON |
| `POST` | `/export/{format}` | Export to JSON/CSV |
| `WS` | `/ws/stream` | WebSocket for live audio streaming |

## Configuration

ONF is configured via environment variables (prefix `ONF_`). Copy `.env.example`
to `.env` to customize. All values default to a fully offline, on-device setup.

Common settings:

| Variable | Default | Description |
|---|---|---|
| `ONF_HOST` / `ONF_PORT` | `127.0.0.1` / `8000` | Backend bind address |
| `ONF_REFLEX_MODEL` | `qwen2.5-0.5b` | Fast reflex model alias |
| `ONF_REASON_MODEL` | `qwen2.5-1.5b` | Deep reason model alias |
| `ONF_FOUNDRY_BOOTSTRAP` | `true` | Let the SDK auto-start Foundry + download models |
| `ONF_ENABLE_WHISPER` | `true` | On-device ASR via faster-whisper |
| `ONF_ENABLE_TTS` | `false` | Optional backend TTS (else browser Web Speech) |
| `ONF_ENABLE_DIARIZATION` | `true` | Speaker separation |
| `ONF_ENABLE_VISION` | `true` | Screen capture |
| `ONF_ONLINE_ENABLED` | `false` | Opt-in hybrid online routing |
| `ONF_ONLINE_BASE_URL` / `ONF_ONLINE_API_KEY` | — | OpenAI-compatible cloud endpoint |
| `ONF_ONLINE_ROUTE` | `reason` | Which requests go online: `reason`, `all`, `off` |

See `.env.example` for the full list. Other configuration:

- **Skills**: Add new personas to `skills/*.md` with YAML frontmatter.
- **Knowledge Vault**: Drag & drop PDF/Text files into the UI.
- **Models**: Foundry Local auto-downloads the configured aliases on first run.
- **Deep Think**: Toggle in the UI to switch between Reflex (fast) and Deep Reason (thorough) modes.

## Reliability & Graceful Degradation

ONF is built so the components never break each other:

- **Always boots**: The backend starts even if Foundry Local isn't running and
  no optional ML dependencies are installed.
- **Lazy, fault-isolated init**: Heavy libraries (Whisper, ChromaDB, TTS,
  diarization, vision) are imported only when used and wrapped so one failure
  can't abort startup.
- **Honest status**: `GET /health` reports each component as active or degraded;
  endpoints for unavailable features return `503` rather than crashing.
- **Sensible fallbacks**: RAG falls back to an in-memory keyword store if
  ChromaDB is absent; TTS falls back to the browser Web Speech API.
- **Smoke test**: `python smoke_test.py` validates graceful degradation with no
  heavy dependencies and no Foundry running.

## Implementation Roadmap

- [x] **Phases 1-9**: Core RAG, File Support, Deep Reasoning, WebSockets, Skills, Reports, Proactive Intelligence
- [x] **Phase 10**: Core Architecture Refactor (Foundry Local SDK)
- [x] **Phase 11**: Advanced Knowledge Engine (ChromaDB)
- [x] **Phase 12**: Dynamic Skills System (Anthropic-style SKILL.md)
- [x] **Phase 13**: Enhanced Visualization & UI (Spotify Gold theme)
- [x] **Phase 14**: Interactive Agent & Text-to-Speech
- [x] **Phase 15**: Session Intelligence, Analytics & Exports
- [ ] **Phase 16**: Multi-Modal Future (video analysis, advanced diarization)

## Privacy & Security

- **Offline by default**: No data leaves your machine unless you explicitly enable the hybrid-online engine (`ONF_ONLINE_ENABLED`).
- **Localhost Only**: All services bind to `localhost` / `127.0.0.1`.
- **On-device inference**: All default AI inference runs via Foundry Local on-device.
- **Opt-in hybrid**: When enabled, only the requests you route online (e.g. "Deep Think") are sent to your chosen OpenAI-compatible endpoint.
- **Local Storage**: Sessions, ChromaDB, and reports stored in local directories.

## License

MIT License - See [LICENSE](LICENSE) for details.
