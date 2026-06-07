"""Dependency-light smoke test for the ONF backend.

This boots the FastAPI app **in-process** with FastAPI's TestClient and verifies
that the backend comes up and degrades gracefully even when none of the heavy,
optional ML dependencies (torch, faster-whisper, chromadb, MeloTTS/OpenVoice,
pyannote, pyautogui) are installed and Foundry Local is not running.

It is the canonical "does the wiring hold together" check and runs anywhere,
including CI, with only the core web dependencies installed:

    pip install fastapi "uvicorn[standard]" openai pydantic httpx \
        python-multipart pyyaml numpy pypdf
    python smoke_test.py

For a *full* live test against a running server (real models, microphone, etc.)
use ``smoke_test_v2.py`` which exercises the HTTP/WebSocket API end to end.
"""

from __future__ import annotations

import os
import sys

# Force a clean, fully-offline configuration for the smoke test.
os.environ.setdefault("ONF_FOUNDRY_BOOTSTRAP", "false")
os.environ.setdefault("ONF_ENABLE_TTS", "false")
os.environ.setdefault("ONF_ENABLE_WHISPER", "false")
os.environ.setdefault("ONF_ENABLE_VISION", "false")
os.environ.setdefault("ONF_ENABLE_PROACTIVE_LOOP", "false")
os.environ.setdefault("ONF_ONLINE_ENABLED", "false")

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

PASSED = 0
FAILED = 0


def check(name: str, condition: bool, detail: str = "") -> None:
    global PASSED, FAILED
    if condition:
        PASSED += 1
        print(f"  PASS  {name}")
    else:
        FAILED += 1
        print(f"  FAIL  {name} {('- ' + detail) if detail else ''}")


def main() -> int:
    print("=== ONF backend smoke test (graceful-degradation) ===\n")

    # 1. Importing the app must never raise, even with heavy deps absent.
    from fastapi.testclient import TestClient
    from backend.main import app

    with TestClient(app) as client:  # triggers lifespan startup
        # 2. Root + health
        r = client.get("/")
        check("GET / responds", r.status_code == 200, str(r.status_code))

        r = client.get("/health")
        check("GET /health responds", r.status_code == 200, str(r.status_code))
        health = r.json() if r.status_code == 200 else {}
        check("backend booted (voice_service up)", health.get("voice_service") is True)
        check("health reports components", "components" in health)
        comps = health.get("components", {})
        print(f"    components: {comps}")

        # 3. Skills endpoint returns a list (works even with no engine).
        r = client.get("/skills")
        check(
            "GET /skills returns list",
            r.status_code == 200 and isinstance(r.json().get("skills"), list),
        )

        # 4. Knowledge upload + RAG fallback works without chromadb.
        r = client.post("/upload-knowledge", json={"text": "ACME deploys on Fridays only."})
        check("POST /upload-knowledge ok", r.status_code == 200, r.text)

        # 5. Chat degrades gracefully (no engine -> helpful message, not a 500).
        r = client.post("/chat", json={"query": "When do we deploy?"})
        check("POST /chat degrades gracefully", r.status_code == 200, r.text)
        check("chat returns a response string", bool(r.json().get("response")))

        # 6. Report generation (pure-python, should work).
        r = client.post(
            "/report/generate",
            json={
                "transcript": [{"role": "user", "text": "Hello"}],
                "insights": [{"type": "Topic", "text": "Intro"}],
                "summary": "Test summary.",
                "topic": "Smoke Test",
            },
        )
        check("POST /report/generate ok", r.status_code == 200, r.text)

        # 7. Agenda + summary + action items must not 500.
        check("POST /agenda/check ok", client.post("/agenda/check").status_code == 200)
        check("POST /summary ok", client.post("/summary").status_code == 200)
        check("POST /action-items ok", client.post("/action-items").status_code == 200)

        # 8. TTS without backend engine returns 503 (UI uses Web Speech fallback).
        r = client.post("/tts/speak", json={"text": "hello"})
        check("POST /tts/speak signals fallback (503)", r.status_code == 503, str(r.status_code))

        # 9. Session save works.
        check("POST /session/save ok", client.post("/session/save").status_code == 200)

    print(f"\n=== {PASSED} passed, {FAILED} failed ===")
    if FAILED:
        print("SMOKE TEST FAILED")
        return 1
    print("ALL SMOKE TESTS PASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
