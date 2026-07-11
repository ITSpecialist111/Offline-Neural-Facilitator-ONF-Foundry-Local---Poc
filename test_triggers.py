"""Focused deterministic outcome and dynamics checks."""

from __future__ import annotations

import asyncio

from backend.services.voice_service import VoiceService


async def main() -> None:
    facilitator = await asyncio.to_thread(VoiceService)
    events: list[dict] = []

    async def capture(event: dict) -> None:
        events.append(event)

    facilitator.set_broadcast_callback(capture)
    await facilitator.reset_session("Trigger validation")
    await facilitator.add_transcript("I disagree. This launch is too risky.", speaker="A")
    await facilitator.add_transcript("I am not convinced; it will not work without evidence.", speaker="B")
    await facilitator.add_transcript("Agreed to delay access until the control is signed.", speaker="A")
    await facilitator.add_transcript("Action item: Maya will collect the evidence by Tuesday.", speaker="A")

    state = facilitator.snapshot()
    assert len(state["risks"]) == 1
    assert len(state["decisions"]) == 1
    assert len(state["actions"]) == 1
    assert state["actions"][0]["owner"] == "Maya"
    assert {event["type"] for event in events}.issuperset({"insight", "decision", "action"})
    print("PASS trigger, decision and owner extraction")

    events.clear()
    await facilitator.reset_session("Untitled session")
    await facilitator.add_transcript(
        "Today we're opening a fictional tabletop called Code Blue: Ransomware at Northstar Hospital.",
        speaker="Host",
        analyze=False,
    )
    await facilitator.add_transcript(
        "Action item: Priya will activate clinical diversion now. "
        "Action item: Marcus will verify the immutable backup within thirty minutes.",
        speaker="Host",
    )
    state = facilitator.snapshot()
    assert state["session"]["topic"] == "Code Blue: Ransomware at Northstar Hospital"
    assert state["session"]["topic_source"] == "conversation"
    assert len(state["actions"]) == 2
    assert {item["owner"] for item in state["actions"]} == {"Priya", "Marcus"}
    assert {item["due"] for item in state["actions"]} == {"Now", "Within thirty minutes"}
    assert any(item["kind"] == "knowledge" for item in state["insights"])
    assert "session_title" in {event["type"] for event in events}
    assert VoiceService._explicit_title(
        "This tabletop is called Code Blue Ransawam at Northstar Hospital."
    ) == "Code Blue: Ransomware at Northstar Hospital"
    print("PASS automatic title and multi-action extraction")


if __name__ == "__main__":
    asyncio.run(main())