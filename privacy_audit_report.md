# Privacy and Offline Boundary Audit

**Audit date:** 11 July 2026
**Scope:** active v2 web application code and runtime defaults

## Verified controls

- FastAPI and Vite bind to `127.0.0.1` in the supported launcher.
- Frontend API and WebSocket traffic target loopback services.
- Foundry inference targets `127.0.0.1:4500` by default.
- No telemetry, advertising or remote error-reporting SDK is present.
- Session state is stored in local JSON files.
- Reports are written to the local `FacilitatorReports` directory.
- Knowledge is stored in a local ChromaDB collection.
- Knowledge embeddings use `onf-local-hash-v1`, which performs no network access.
- faster-whisper is configured with `local_files_only=True` by default.
- Runtime MeloTTS sets Hugging Face and Transformers offline modes before loading English language assets.
- Uploads are limited to 20 MB and knowledge file types are allowlisted.
- CORS is restricted to local frontend origins by default.
- Skill filenames are sanitized before persistence.

## Explicit provisioning exception

The setup workflow can download Foundry and audio models. This is an intentional provisioning action, not meeting-time data transfer. Once cached, the supported runtime performs inference locally.

## Known limitations

1. Session, vault and report content is not encrypted by ONF. Filesystem encryption such as BitLocker is required for strong data-at-rest protection.
2. Uploaded text is still untrusted input and can influence local model output. The app limits file type and size but does not provide a complete prompt-injection defense.
3. The optional speech stack has its own dependency chain and should be reviewed before regulated deployment.
4. Foundry Local can use the network for initial models, execution providers, and optional catalog refreshes; offline operation begins after provisioning.
5. This is a code/configuration audit, not a packet capture or formal penetration test.

## Runtime verification checklist

- [ ] Disable Wi-Fi/Ethernet after provisioning and complete the presenter scenario.
- [ ] Confirm only loopback listeners exist for ports 4500, 5173 and 8000.
- [ ] Capture process network activity during a real session.
- [ ] Confirm exports and ChromaDB remain inside approved encrypted storage.
- [ ] Review retention and deletion requirements with the deployment owner.

**Result:** The default architecture is local-first and contains no application telemetry. Formal “air-gapped” or regulated-use claims require the runtime verification checklist and host controls above.