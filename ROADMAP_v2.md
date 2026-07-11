# ONF v2 Roadmap

The product north star is defined in [COMMANDERS_INTENT.md](COMMANDERS_INTENT.md). Roadmap items are valuable only when they improve the loop **capture → understand → intervene → decide → export**.

## v2.0 showcase foundation — complete

- [x] Rebuild the UI as a responsive, accessible private meeting workspace.
- [x] Make backend import and startup independent of heavyweight model loading.
- [x] Publish honest capability readiness instead of failing the whole application.
- [x] Replace malformed partial-WebM buffering with complete audio segments.
- [x] Establish one canonical session state and WebSocket event contract.
- [x] Separate guidance, decisions, actions and risks.
- [x] Add a deterministic presenter scenario with camera-safe content.
- [x] Add local save, JSON, Markdown and PDF workflows.
- [x] Replace download-prone default embeddings with a network-free local index.
- [x] Standardize and load five bundled facilitator and incident-response skills.
- [x] Resolve Foundry model aliases against available device-specific model IDs.

## v2.1 reliability — next

- [ ] Validate live microphone capture across Edge and Chrome for 60-minute sessions.
- [ ] Add a local audio fixture suite covering silence, speech, reconnect and malformed input.
- [ ] Add opt-in, fully local speaker diarization with measured accuracy and explicit consent.
- [ ] Add structured application logs with automatic sensitive-text suppression.
- [ ] Add backend unit and contract tests to CI.
- [ ] Add session history with reopen, rename and delete.
- [ ] Package a signed Windows installer and first-run readiness wizard.

## v2.2 facilitation quality

- [ ] Add intervention cooldowns configurable by meeting type.
- [ ] Measure citation precision and suppress weak knowledge matches.
- [ ] Add agenda objectives and explicit decision gates.
- [ ] Improve owner and due-date extraction with structured local model output.
- [ ] Add user-editable decisions and actions with an audit trail.
- [ ] Add skill activation explanations and per-session skill controls.

## v2.3 deployment hardening

- [ ] Encrypt sensitive local state or integrate with Windows-protected storage.
- [ ] Add configurable retention and secure deletion.
- [ ] Add signed export manifests and evidence hashes.
- [ ] Complete threat modeling for local uploads, prompts and report rendering.
- [ ] Validate offline operation with network interfaces disabled.

## v2.4 mobile and edge research

- [ ] Extract a platform-neutral session and event contract package.
- [ ] Prototype the responsive workspace inside a native mobile WebView/PWA shell.
- [ ] Benchmark quantized reflex, ASR, and retrieval models on representative phone hardware.
- [ ] Evaluate Foundry Local support by target platform and ONNX Runtime Mobile where a native Foundry host is unavailable.
- [ ] Replace desktop file paths and ChromaDB with sandboxed mobile storage and a mobile-safe local index.
- [ ] Measure battery, thermals, memory pressure, and background microphone constraints before claiming native mobile support.

## Future, not currently claimed

- Real speaker identity
- Video or expression analysis
- Multi-camera cues
- Shared cloud workspaces
- Autonomous consequential decisions

These remain out of scope until the core meeting loop is measured, reliable and trustworthy.