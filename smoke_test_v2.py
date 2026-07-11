"""Deterministic end-to-end smoke test for ONF v2.

Start the application first with ``.\\scripts\\start.ps1 -NoBrowser`` or run the
backend directly.  This suite deliberately avoids ASR/TTS so it never downloads
or loads optional voice models.
"""

from __future__ import annotations

import asyncio
import json
import os
import sys
import time
from pathlib import Path

import requests
import websockets

BASE_URL = os.getenv("ONF_TEST_BASE_URL", "http://127.0.0.1:8000").rstrip("/")
WS_URL = BASE_URL.replace("http://", "ws://", 1).replace("https://", "wss://", 1) + "/ws/stream"


def request(method: str, path: str, **kwargs) -> dict:
    response = requests.request(method, f"{BASE_URL}{path}", timeout=120, **kwargs)
    response.raise_for_status()
    return response.json()


def wait_for_backend() -> None:
    for _ in range(40):
        try:
            if request("GET", "/api/status").get("status") == "ready":
                return
        except Exception:
            time.sleep(0.25)
    raise RuntimeError("ONF backend did not become ready")


def assert_health() -> None:
    payload = request("GET", "/health")
    capabilities = payload["capabilities"]
    assert payload["status"] == "ready"
    assert capabilities["knowledge"]["status"] == "ready"
    assert capabilities["knowledge"]["curated_chunks"] >= 8
    assert capabilities["privacy"]["telemetry"] is False
    assert capabilities["privacy"]["network_scope"] == "loopback only"
    print("PASS health and privacy contract")


async def run_showcase_and_observe() -> list[dict]:
    events: list[dict] = []
    async with websockets.connect(WS_URL, open_timeout=5) as websocket:
        initial = json.loads(await asyncio.wait_for(websocket.recv(), timeout=5))
        assert initial["type"] == "session_state"

        request("POST", "/demo/start")
        deadline = asyncio.get_running_loop().time() + 15
        while asyncio.get_running_loop().time() < deadline:
            event = json.loads(await asyncio.wait_for(websocket.recv(), timeout=12))
            events.append(event)
            if event.get("type") == "session_status" and event.get("status") == "ready":
                break

    event_types = {event["type"] for event in events}
    assert {"transcript", "insight", "decision", "action", "session_status"}.issubset(event_types)
    print(f"PASS WebSocket event contract ({len(events)} events)")
    return events


def assert_showcase_state() -> dict:
    state = request("GET", "/state")["state"]
    assert state["session"]["topic"] == "Code Blue: Ransomware at Northstar Hospital"
    assert state["session"]["status"] == "ready"
    assert len(state["transcript"]) == 7
    assert len(state["insights"]) == 4
    assert len(state["decisions"]) == 1
    assert len(state["actions"]) == 3
    assert len(state["risks"]) == 1
    assert {item["owner"] for item in state["actions"]} == {"Priya", "Marcus", "Elena"}
    print("PASS deterministic showcase outcomes")
    return state


def assert_chat() -> None:
    response = request(
        "POST",
        "/chat",
        json={"query": "What decision did the group make and who owns the next steps?", "mode": "reflex"},
    )
    answer = response["response"].lower()
    assert answer
    assert "ransom" in answer and "priya" in answer and "marcus" in answer and "elena" in answer
    print("PASS local facilitator query")


def assert_exports(state: dict) -> None:
    summary = request("POST", "/summary")["summary"]
    payload = {
        "transcript": state["transcript"],
        "insights": state["insights"],
        "summary": summary,
        "topic": state["session"]["topic"],
    }
    results = [
        request("POST", "/session/save"),
        request("POST", "/export/json"),
        request("POST", "/report/generate", json=payload),
        request("POST", "/report/export/pdf", json=payload),
    ]
    for result in results:
        path = Path(result["filepath"])
        assert path.exists(), f"Missing export: {path}"
        assert path.stat().st_size > 0, f"Empty export: {path}"
    print("PASS JSON, Markdown, PDF and session persistence")


async def main() -> int:
    try:
        wait_for_backend()
        assert_health()
        await run_showcase_and_observe()
        state = assert_showcase_state()
        assert_chat()
        assert_exports(state)
    except Exception as exc:
        print(f"FAIL {type(exc).__name__}: {exc}")
        return 1

    print("\nALL ONF V2 SMOKE TESTS PASSED")
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))