# Offline Neural Facilitator (ONF) v1.2.0

**Privacy-First, Offline AI Meeting Facilitator powered by Microsoft Foundry Local**

The Offline Neural Facilitator (ONF) transforms your PC into an intelligent meeting facilitator that listens, understands, and proactively assists - all running entirely on your local machine with zero cloud dependency.

## Architecture

```
Frontend (React 19 + Vite)     Backend (FastAPI + WebSockets)     AI Engine
 localhost:5173            -->   localhost:8000              -->   Foundry Local (localhost:4500)
   Live Transcript                /transcribe                      Qwen 2.5 0.5B (Reflex)
   Insights Dashboard             /chat                            DeepSeek R1 1.5B (Reason)
   Chat Widget                    /ws/stream                       faster-whisper (ASR)
   Analytics                      /report/generate                 MeloTTS + OpenVoice (TTS)
                                  /skills, /upload-knowledge       ChromaDB (RAG Vector Store)
```

## Key Features

### Dual-Engine Intelligence
- **Reflex Engine (Qwen 2.5 0.5B)**: Fast, low-latency responses for chat, topic detection, action items, and summaries.
- **Deep Reason Engine (DeepSeek R1 1.5B)**: Complex chain-of-thought reasoning activated via "Deep Think" toggle for conflict analysis, compliance, and strategy.

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
- **MeloTTS + OpenVoice**: AI-generated speech with voice cloning/tone conversion.
- **In-app Playback**: "Play" button on insights to hear them spoken aloud.

## Microsoft Foundry Local Integration

This project uses **Microsoft Azure AI Foundry Local** (Public Preview) for all LLM inference. Foundry Local runs models entirely on-device with no cloud dependency.

### Current Compatibility
| Component | Version | Notes |
|---|---|---|
| **Foundry Local CLI** | v0.8.119+ | Install via `winget install Microsoft.FoundryLocal` |
| **Python SDK** | `foundry-local-sdk` | Install via `pip install foundry-local-sdk` |
| **Inference Endpoint** | `localhost:4500` | OpenAI-compatible API |
| **API Key** | `"foundry"` | Static placeholder for local SDK |

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
pip install -r requirements.txt
```

### 3. Install Frontend Dependencies
```bash
cd frontend && npm install
```

### 4. Start the Application
```powershell
./scripts/start.ps1
```
This launches both the backend (FastAPI on port 8000) and frontend (Vite on port 5173).

### 5. Access the UI
Open your browser to `http://localhost:5173`

## Project Structure

```
backend/
  main.py                    # FastAPI server (all REST + WebSocket endpoints)
  llm/
    foundry_manager.py       # FoundryEngine wrapper for Foundry Local SDK
  services/
    voice_service.py         # Core orchestration (the "brain")
    rag_service.py           # ChromaDB vector store operations
    transcription_service.py # faster-whisper ASR
    tts_service.py           # MeloTTS + OpenVoice
    diarization_service.py   # Speaker separation
    agenda_service.py        # Topic detection
    report_service.py        # Markdown/PDF report generation
    skill_service.py         # SKILL.md loader and trigger system
    vision_service.py        # Screenshot capture via pyautogui

frontend/
  src/
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
  start.ps1                 # PowerShell launcher for backend + frontend
```

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/` | Health check |
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

- **Skills**: Add new personas to `skills/*.md` with YAML frontmatter.
- **Knowledge Vault**: Drag & drop PDF/Text files into the UI.
- **Models**: Foundry Local auto-downloads `Qwen 2.5` and `DeepSeek R1` on first run.
- **Deep Think**: Toggle in the UI to switch between Reflex (fast) and Deep Reason (thorough) modes.

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

- **Zero Telemetry**: No data leaves your machine.
- **Localhost Only**: All services bind to `localhost` / `127.0.0.1`.
- **No Cloud SDKs**: All AI inference runs via Foundry Local on-device.
- **Local Storage**: Sessions, ChromaDB, and reports stored in local directories.

## License

MIT License - See [LICENSE](LICENSE) for details.
