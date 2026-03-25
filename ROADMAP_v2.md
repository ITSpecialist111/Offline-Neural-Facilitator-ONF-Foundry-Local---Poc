# Offline Neural Facilitator (ONF) - Roadmap v2.0
**Next Generation Features: Visualization, Context, and Deep Customization**

This roadmap outlines the path from v1.2.0 to v2.0, focusing on advanced RAG, dynamic skills, and rich visual interfaces.

## Phase 10: Core Architecture Refactor (Foundry Local)
**Goal**: Offline-first, low-latency intelligence via `foundry-local-sdk`.
- [x] **Foundry Engine**: Replaced direct ONNX loading with `FoundryEngine` wrapping `foundry-local-sdk`.
- [x] **Dual Model Support**: Standardized Reflex (Qwen) and Deep Reason (DeepSeek) interfaces.
- [x] **Vision Support**: Added `/vision/capture` endpoint and UI integration for screenshot context.
- [x] **FastAPI Migration**: Ported legacy loop to robust ASGI backend.

## Phase 11: Advanced Knowledge Engine (VectorDB)
**Goal**: Move beyond simple text matching to a robust, scalable vector store.
- [x] **Infrastructure**: Replace `SentenceTransformer`+`pkl` with **ChromaDB** or **Qdrant** (Local).
- [x] **Ingestion Pipeline**: Support PDF, Docx, and Markdown ingestion with metadata extraction (page numbers, authors).
- [x] **Hybrid Search**: Combine keyword search (BM25) with semantic search (Embeddings). (Metadata Citations Implemented).
- [x] **Hover Citations**: UI extracts source metadata to show "Page 5" on hover over an insight.

## Phase 12: Dynamic Skills System (Anthropic Standard)
**Goal**: Modular, importable personality and capability packages.
- [x] **Standard Definition**: Adopt `SKILL.md` format (YAML Frontmatter + Instructions).
- [x] **Skill Loader**:
    - Scan `skills/` directories.
    - Load lightweight metadata (`name`, `description`) into System Prompt.
    - "Just-in-Time" loading of full instructions when triggered.
- [x] **Context Awareness**: Auto-switch active skills based on conversation keywords (e.g., "Legal" -> Load Legal Reviewer).
- [x] **Import UI**: "Drag & Drop" a skill folder to install it.

## Phase 13: Enhanced Visualization & UI
**Goal**: Turn the meeting into a visual dashboard.
- [x] **Timeline UI**: Visualize the meeting as a chronological stream (Spotify Lyrics style).
- [x] **Live Marker**: Auto-scroll to current speaker/topic.
- [x] **Keyword Highlighting**: Fade out irrelevant text, highlight action items/risks. (Implicit in the new card design which highlights Proactive insights).
- [x] **Sidebar Redesign**: Move from simple list to "Now Playing" insights dashboard.
- [x] **Premium Theme**: "Spotify Gold" aesthetic." with the excerpt.
- [x] **Sidebar Revamp**: Tabs for "Live", "Action Items", "Risks".

## Phase 14: Interactive Agent & Audio
**Goal**: Two-way conversation and accessibility.
- [x] **Agent Chat Mode**:
    - "Ask the Facilitator" chat box (separate from meeting transcript).
    - Q&A against the current session + Vault.
- [x] **Text-to-Speech (TTS)**:
    - Re-integrate MeloTTS/OpenVoice.
    - "Read Insight": Button to have the AI speak the insight into the user's earpiece.
- [ ] **Voice Personalities**: Selectable voices for the Facilitator. (British Voice configured).

## Phase 15: Session Intelligence & Export
**Goal**: Enterprise-grade records and analytics.
- [x] **Session Logger**: Full JSON dumps of every event (transcript, insight, mouse click).
- [x] **Export Formats**: JSON, CSV, PDF (Report).
- [x] **Action Item Extractor**: Dedicated NLP pass to extract owners and due dates.
- [x] **Analytics Dashboard**: "Meeting Health" score, talk time distribution (Diarization metrics).
- [x] **The Smart Loop**: Implemented proactive Cognitive Load and Conflict detection logic.
- [x] **Specialized Skills**: Added Strategy Consultant and Crisis Manager personas.

## Phase 16: Multi-Modal Future
**Goal**: Integration of video and advanced diarization.
- [ ] **Video Analysis**: Real-time expression and engagement tracking.
- [ ] **Advanced Diarization**: Multi-camera speaker identification and visual cues.
