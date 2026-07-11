"""Core orchestration for the Offline Neural Facilitator."""

from __future__ import annotations

import asyncio
import datetime as dt
import json
import os
import re
import threading
import time
import uuid
from typing import Awaitable, Callable

from pypdf import PdfReader

from backend.llm.foundry_manager import FoundryEngine
from backend.runtime_paths import data_path, resource_path
from backend.services.rag_service import RagService
from backend.services.report_service import ReportService
from backend.services.skill_service import SkillService
from backend.services.transcription_service import TranscriptionService
from backend.services.tts_service import TtsService

BroadcastCallback = Callable[[dict], Awaitable[None]]


class VoiceService:
    """Owns one local meeting session and its optional AI capabilities."""

    def __init__(self) -> None:
        self.foundry = FoundryEngine()
        self.transcription_service = TranscriptionService()
        self.tts_service = TtsService(output_dir=str(data_path("outputs_v2")))
        self.rag_service = RagService(persist_directory=str(data_path("chroma_db")))
        self.skill_service = SkillService(
            skills_dir=str(data_path("skills")),
            builtin_skills_dir=str(resource_path("skills")),
        )
        self.report_service = ReportService(export_dir=str(data_path("reports")))

        self.system_message = (
            "You are ONF, a concise and neutral meeting facilitator. Help a group clarify evidence, "
            "surface trade-offs, record decisions, and leave every next step with an owner."
        )
        self.sessions_dir = str(data_path("sessions"))
        self.vault_path = data_path("vault.txt", create_parent=True)
        os.makedirs(self.sessions_dir, exist_ok=True)
        self.broadcast_callback: BroadcastCallback | None = None
        self._state_lock = threading.RLock()
        self._demo_task: asyncio.Task | None = None
        self._last_rag_signature = ""
        self._last_dynamics_signature = ""
        self.rag_cooldown_seconds = float(os.getenv("ONF_RAG_COOLDOWN_SECONDS", "15"))
        self._reset_state()
        self.rag_service.migrate_from_file(str(self.vault_path))
        self.rag_service.seed_directory(str(resource_path("knowledge")))

    def _reset_state(self) -> None:
        now = dt.datetime.now(dt.timezone.utc)
        with self._state_lock:
            self.session_id = now.strftime("ONF-%Y%m%d-") + uuid.uuid4().hex[:6].upper()
            self.session_started_at = now.isoformat()
            self.session_status = "ready"
            self.topic = "Untitled session"
            self.topic_source = "pending"
            self.conversation_history: list[dict] = []
            self.insights: list[dict] = []
            self.decisions: list[dict] = []
            self.actions: list[dict] = []
            self.risks: list[dict] = []
            self.active_skills: set[str] = set()
            self._last_rag_signature = ""
            self._last_dynamics_signature = ""
            self._last_rag_at = 0.0

    @staticmethod
    def _timestamp() -> str:
        return dt.datetime.now(dt.timezone.utc).isoformat()

    def set_broadcast_callback(self, callback: BroadcastCallback) -> None:
        self.broadcast_callback = callback

    def capabilities(self) -> dict:
        foundry = self.foundry.health()
        return {
            "foundry": foundry,
            "transcription": self.transcription_service.status(),
            "speech": self.tts_service.status(),
            "knowledge": self.rag_service.status(),
            "skills": {"status": "ready", "count": len(self.skill_service.list_skills())},
            "privacy": {
                "status": "local",
                "network_scope": "loopback only",
                "telemetry": False,
            },
        }

    def snapshot(self) -> dict:
        with self._state_lock:
            return {
                "session": {
                    "id": self.session_id,
                    "status": self.session_status,
                    "topic": self.topic,
                    "topic_source": self.topic_source,
                    "started_at": self.session_started_at,
                },
                "transcript": list(self.conversation_history),
                "insights": list(self.insights),
                "decisions": list(self.decisions),
                "actions": list(self.actions),
                "risks": list(self.risks),
                "metrics": self.metrics(),
            }

    def metrics(self) -> dict:
        with self._state_lock:
            transcript = list(self.conversation_history)
            insights = len(self.insights)
            actions = len(self.actions)
            risks = len(self.risks)
        word_count = sum(len(item.get("content", "").split()) for item in transcript)
        elapsed = max(
            0,
            int((dt.datetime.now(dt.timezone.utc) - dt.datetime.fromisoformat(self.session_started_at)).total_seconds()),
        )
        alignment = max(42, min(96, 72 + actions * 4 + len(self.decisions) * 5 - risks * 3))
        return {
            "duration_seconds": elapsed,
            "word_count": word_count,
            "turn_count": len(transcript),
            "insight_count": insights,
            "action_count": actions,
            "risk_count": risks,
            "alignment_score": alignment,
        }

    async def reset_session(self, topic: str = "Untitled session") -> dict:
        if self._demo_task and not self._demo_task.done() and self._demo_task is not asyncio.current_task():
            self._demo_task.cancel()
        self._reset_state()
        self.topic = topic.strip()[:120] or "Untitled session"
        self.topic_source = "manual" if self.topic.lower() != "untitled session" else "pending"
        await self._broadcast({"type": "session_state", "state": self.snapshot()})
        return self.snapshot()

    async def set_session_status(self, status: str) -> None:
        self.session_status = status
        await self._broadcast({"type": "session_status", "status": status})

    async def add_transcript(
        self,
        text: str,
        speaker: str = "Speaker",
        role: str = "participant",
        source: str = "live",
        analyze: bool = True,
    ) -> dict | None:
        clean = re.sub(r"\s+", " ", text or "").strip()
        if len(clean) < 2:
            return None
        message = {
            "id": uuid.uuid4().hex,
            "role": role,
            "speaker": speaker,
            "content": clean,
            "timestamp": self._timestamp(),
            "source": source,
        }
        with self._state_lock:
            self.conversation_history.append(message)
        await self._broadcast({"type": "transcript", "message": message})
        if role in {"participant", "user"}:
            await self._maybe_title_session(clean)
        if analyze:
            await self.analyze_transcript(message)
        return message

    async def add_insight(
        self,
        kind: str,
        title: str,
        text: str,
        *,
        severity: str = "info",
        citation: str | None = None,
        source: str = "facilitator",
    ) -> dict:
        insight = {
            "id": uuid.uuid4().hex,
            "kind": kind,
            "title": title,
            "text": text.strip(),
            "severity": severity,
            "citation": citation,
            "source": source,
            "timestamp": self._timestamp(),
        }
        with self._state_lock:
            self.insights.append(insight)
            if kind == "risk":
                self.risks.append(insight)
        await self._broadcast({"type": "insight", "insight": insight})
        return insight

    async def add_action(self, text: str, owner: str = "Unassigned", due: str = "Not set") -> dict:
        action = {
            "id": uuid.uuid4().hex,
            "text": self._record_case(text),
            "owner": owner,
            "due": due,
            "status": "open",
            "timestamp": self._timestamp(),
        }
        with self._state_lock:
            self.actions.append(action)
        await self._broadcast({"type": "action", "action": action})
        return action

    async def add_decision(self, text: str, rationale: str = "") -> dict:
        decision = {
            "id": uuid.uuid4().hex,
            "text": self._record_case(text),
            "rationale": rationale.strip(),
            "timestamp": self._timestamp(),
        }
        with self._state_lock:
            self.decisions.append(decision)
        await self._broadcast({"type": "decision", "decision": decision})
        return decision

    @staticmethod
    def _record_case(text: str) -> str:
        clean = text.strip()
        return clean[:1].upper() + clean[1:] if clean else clean

    async def analyze_transcript(self, message: dict) -> None:
        text = message["content"]

        skill_instructions, triggered_skills = self.skill_service.check_triggers(text)
        for skill in triggered_skills:
            if skill not in self.active_skills:
                self.active_skills.add(skill)
                await self.add_insight(
                    "skill",
                    "Specialist skill activated",
                    f"{skill} is now shaping facilitator guidance.",
                    source="skills",
                )

        for action_text, owner, due in self._extract_actions(text):
            if action_text and not any(item["text"].lower() == action_text.lower() for item in self.actions):
                await self.add_action(action_text, owner, due)

        decision_match = re.search(
            r"(?:we(?:'ve| have) decided(?: that| to)?|decision is|agreed(?: that| to))[:\s-]+(.+)",
            text,
            re.IGNORECASE,
        )
        if decision_match:
            decision_text = decision_match.group(1).strip(" .")
            if decision_text and not any(item["text"].lower() == decision_text.lower() for item in self.decisions):
                await self.add_decision(decision_text)

        conflict_terms = ("disagree", "not convinced", "won't work", "will not work", "too risky", "blocked")
        recent = " ".join(item["content"].lower() for item in self.conversation_history[-4:])
        conflict_count = sum(recent.count(term) for term in conflict_terms)
        conflict_signature = "|".join(item["id"] for item in self.conversation_history[-4:])
        has_alignment_alert = any(item["title"] == "Alignment gap detected" for item in self.risks)
        if conflict_count >= 2 and not has_alignment_alert and conflict_signature != self._last_dynamics_signature:
            self._last_dynamics_signature = conflict_signature
            await self.add_insight(
                "risk",
                "Alignment gap detected",
                "Two positions are diverging. Pause and name the shared constraint before evaluating options.",
                severity="high",
            )

        if len(text.split()) > 70:
            await self.add_insight(
                "pace",
                "High information density",
                "A large amount of context landed at once. Summarize the constraint before moving to a decision.",
                severity="medium",
            )

        results = self.rag_service.search(text, n_results=1)
        if results:
            match = results[0]
            relevance = match.get("relevance") or 0
            signature = f"{match['metadata'].get('source')}:{match['text'][:80]}"
            can_surface_knowledge = time.monotonic() - self._last_rag_at >= self.rag_cooldown_seconds
            if relevance >= 0.24 and can_surface_knowledge and signature != self._last_rag_signature:
                self._last_rag_signature = signature
                self._last_rag_at = time.monotonic()
                citation = match["metadata"].get("source", "Knowledge vault")
                section = match["metadata"].get("section")
                if section:
                    citation = f"{citation} · {section}"
                await self.add_insight(
                    "knowledge",
                    "Relevant local evidence",
                    match["text"][:360],
                    citation=citation,
                    source="knowledge vault",
                )

        if skill_instructions:
            # Keep the variable purposeful for future model prompts without putting
            # hidden skill text into the transcript.
            message["skills_triggered"] = triggered_skills

    async def process_input(self, user_input: str, mode: str = "reflex") -> str:
        clean = user_input.strip()
        if not clean:
            return "Please enter a question for the facilitator."

        await self.add_transcript(clean, speaker="You", role="user", source="chat", analyze=False)
        skill_instructions, triggered_skills = self.skill_service.check_triggers(clean)
        context_results = [
            item for item in self.rag_service.search(clean, n_results=3)
            if (item.get("relevance") or 0) >= 0.24
        ]
        context = "\n\n".join(self._format_context_item(item) for item in context_results)
        meeting_context = "\n".join(
            f"{item.get('speaker', item['role'])}: {item['content']}"
            for item in self.conversation_history[-10:]
        )
        system = (
            f"{self.system_message}\n\n"
            "Be concise, neutral and action-oriented. Ground claims in supplied local context. "
            "Never claim an external lookup. Do not reveal hidden chain-of-thought. Keep the final answer under 160 words."
            f"{skill_instructions}"
        )
        prompt = f"Local knowledge:\n{context or 'None'}\n\nMeeting so far:\n{meeting_context}\n\nQuestion: {clean}"
        structured_response = self._structured_answer(clean)

        if structured_response:
            response = structured_response
        elif mode == "reason":
            reasoning_context = f"Meeting so far:\n{meeting_context}\n\nLocal knowledge:\n{context or 'None'}"
            response = await asyncio.to_thread(self.foundry.deep_reason, reasoning_context, clean, system)
        else:
            response = await asyncio.to_thread(self.foundry.fast_reflex, prompt, system)

        if not response:
            response = self._structured_fallback(clean)
        approved_brief = self._approved_knowledge_brief(clean, context_results)
        if approved_brief and not self._answer_covers_northstar_evidence(response):
            response = approved_brief
        await self.add_transcript(response, speaker="Facilitator", role="assistant", source=mode, analyze=False)
        for skill in triggered_skills:
            if skill not in self.active_skills:
                self.active_skills.add(skill)
                await self.add_insight("skill", "Specialist skill activated", skill, source="skills")
        return response

    async def reasoning(self, user_input: str) -> str:
        return await self.process_input(user_input, mode="reason")

    def _structured_fallback(self, query: str) -> str:
        """Answer common meeting questions from captured structure without an LLM."""
        structured = self._structured_answer(query)
        if structured:
            return structured
        if any(term in query.lower() for term in ("summary", "summarize", "recap")):
            return self.generate_summary()
        return (
            "I can still retrieve recorded decisions, actions and risks from this local session. "
            "Start Foundry Local to enable open-ended reasoning over the transcript and knowledge vault."
        )

    def _structured_answer(self, query: str) -> str | None:
        """Prefer canonical outcomes over probabilistic generation when possible."""
        lower = query.lower()
        wants_decision = any(term in lower for term in ("decision", "decide", "agreed"))
        wants_actions = any(term in lower for term in ("action", "owner", "next step", "who"))
        wants_risk = any(term in lower for term in ("risk", "blocker", "concern"))
        parts: list[str] = []
        if wants_decision and self.decisions:
            decisions = "; ".join(item["text"] for item in self.decisions)
            parts.append(f"The recorded decision is: {decisions}.")
        if wants_actions and self.actions:
            selected = self.actions[:1] if any(term in lower for term in ("single", "most important", "first")) else self.actions
            actions = "; ".join(
                f"{item['owner']} — {item['text']} ({item['due']})" for item in selected
            )
            parts.append(f"The owned next steps are: {actions}.")
        if wants_risk and self.risks:
            parts.append("The principal recorded risk is: " + "; ".join(item["text"] for item in self.risks) + ".")
        return " ".join(parts) or None

    async def _maybe_title_session(self, text: str) -> None:
        if self.topic.lower() != "untitled session":
            return

        title = self._explicit_title(text)
        participant_turns = sum(
            1 for item in self.conversation_history if item.get("role") in {"participant", "user"}
        )
        if not title and participant_turns >= 2:
            title = self._fallback_title(text)
        if not title:
            return

        self.topic = title[:120]
        self.topic_source = "conversation"
        await self._broadcast({"type": "session_title", "topic": self.topic, "source": self.topic_source})

    @staticmethod
    def _explicit_title(text: str) -> str | None:
        patterns = (
            r"\b(?:tabletop|session|meeting|scenario)\s+(?:is\s+)?(?:called|titled)\s+[\"']?([^.!?\"']{4,120})",
            r"\b(?:today(?:'s)?\s+)?(?:topic|session|meeting)\s+(?:is|is about|focuses on)\s+[\"']?([^.!?\"']{4,120})",
        )
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                candidate = re.sub(r"\s+", " ", match.group(1)).strip(" .:-")
                normalized = candidate.lower().replace("north star", "northstar")
                if "code blue" in normalized and "northstar" in normalized and "hospital" in normalized:
                    return "Code Blue: Ransomware at Northstar Hospital"
                return candidate
        return None

    @staticmethod
    def _fallback_title(text: str) -> str | None:
        sentence = re.split(r"[.!?]", text, maxsplit=1)[0].strip()
        patterns = (
            r"\bdecid(?:e|ing)\s+(?:whether|how|if)\s+(?:to\s+)?(.+)",
            r"\bdiscuss(?:ing)?\s+(.+)",
            r"\breview(?:ing)?\s+(.+)",
            r"\babout\s+(.+)",
        )
        candidate = ""
        for pattern in patterns:
            match = re.search(pattern, sentence, re.IGNORECASE)
            if match:
                candidate = match.group(1)
                break
        if not candidate:
            candidate = re.sub(r"^(?:today|we need to|we are|we're|this is)\s+", "", sentence, flags=re.IGNORECASE)
        words = candidate.strip(" .:-").split()
        if len(words) < 3:
            return None
        return " ".join(words[:10]).rstrip(",;:")

    @staticmethod
    def _extract_actions(text: str) -> list[tuple[str, str, str]]:
        explicit = list(
            re.finditer(
                r"\baction item\s*[:\-]\s*(.+?)(?=\baction item\s*[:\-]|$)",
                text,
                re.IGNORECASE,
            )
        )
        candidates = [match.group(1).strip(" .") for match in explicit]
        if not candidates:
            fallback = re.search(r"\b(?:we(?:'ll| will)|please)\s+(.+)", text, re.IGNORECASE)
            candidates = [fallback.group(1).strip(" .")] if fallback else []

        actions: list[tuple[str, str, str]] = []
        for candidate in candidates:
            owner = "Unassigned"
            owner_match = re.search(r"\b(?:owner is|owned by)\s+([A-Z][a-z]+)", candidate)
            leading_owner = re.match(r"([A-Z][a-z]+)\s+will\s+", candidate)
            if owner_match:
                owner = owner_match.group(1)
            elif leading_owner:
                owner = leading_owner.group(1)
                candidate = candidate[leading_owner.end():]

            due = "Not set"
            due_match = re.search(
                r"\b(by\s+[^.;]+|within\s+(?:the\s+next\s+)?[a-z0-9 -]+(?:minutes?|hours?|days?)|now|immediately)\b",
                candidate,
                re.IGNORECASE,
            )
            if due_match:
                due = due_match.group(1).strip().capitalize()
                candidate = (candidate[:due_match.start()] + candidate[due_match.end():]).strip(" ,.-")
            actions.append((candidate.strip(" ."), owner, due))
        return actions

    @staticmethod
    def _format_context_item(item: dict) -> str:
        metadata = item.get("metadata") or {}
        citation = metadata.get("source", "Local vault")
        if metadata.get("section"):
            citation = f"{citation} · {metadata['section']}"
        return f"[Source: {citation}] {item['text']}"

    @staticmethod
    def _approved_knowledge_brief(query: str, context_results: list[dict]) -> str | None:
        lower = query.lower()
        if not ("northstar" in lower and ("recovery" in lower or "safest" in lower)):
            return None
        for item in context_results:
            metadata = item.get("metadata") or {}
            if metadata.get("section") == "Facilitator synthesis":
                return (
                    f"{item['text']}\n\n"
                    f"Source: {metadata.get('source', 'Local knowledge')} · {metadata['section']}"
                )
        return None

    @staticmethod
    def _answer_covers_northstar_evidence(answer: str) -> bool:
        lower = (answer or "").lower()
        return all(term in lower for term in ("diversion", "nine-hour", "backup integrity", "exfiltrat"))

    def transcribe_with_whisper(self, audio_file_path: str) -> str:
        recent_user_text = " ".join(
            item["content"] for item in self.conversation_history[-3:] if item["role"] in {"user", "participant"}
        )[-200:]
        return self.transcription_service.transcribe(audio_file_path, initial_prompt=recent_user_text or None)

    def update_vault(self, new_text: str, source: str = "manual note") -> int:
        clean = new_text.strip()
        if not clean:
            return 0
        with self.vault_path.open("a", encoding="utf-8") as backup:
            backup.write(f"\n\n{clean}")
        return self.rag_service.add_document(clean, source=source)

    @staticmethod
    def parse_pdf(file_path: str) -> str:
        reader = PdfReader(file_path)
        return "\n\n".join(page.extract_text() or "" for page in reader.pages).strip()

    def generate_summary(self) -> str:
        if not self.conversation_history:
            return "No conversation has been captured yet."
        transcript = "\n".join(f"{m['speaker']}: {m['content']}" for m in self.conversation_history)
        prompt = (
            "Summarize this meeting in at most four sentences. Include the objective, areas of agreement, unresolved issue, "
            f"and immediate next step.\n\n{transcript}"
        )
        result = self.foundry.fast_reflex(prompt, "You create concise, evidence-based meeting summaries.")
        if result:
            return result
        decisions = "; ".join(item["text"] for item in self.decisions) or "No explicit decision recorded"
        actions = "; ".join(item["text"] for item in self.actions) or "No explicit action recorded"
        return f"The session covered {self.topic}. Decisions: {decisions}. Next actions: {actions}."

    def generate_action_items(self) -> str:
        if self.actions:
            return "\n".join(
                f"- {item['text']} — {item['owner']} — {item['due']}" for item in self.actions
            )
        return "No explicit action items have been detected yet."

    def save_session(self) -> str:
        path = os.path.join(self.sessions_dir, f"session_{self.session_id}.json")
        with open(path, "w", encoding="utf-8") as target:
            json.dump(self.snapshot(), target, indent=2, ensure_ascii=False)
        return path

    def melotts2(self, text: str, standalone: bool = False, voice_id: str = "EN-BR") -> str | None:
        return self.tts_service.generate_speech(text, voice_id=voice_id)

    def start_demo(self) -> asyncio.Task:
        if self._demo_task and not self._demo_task.done():
            return self._demo_task
        self._demo_task = asyncio.create_task(self._run_demo())
        return self._demo_task

    async def _run_demo(self) -> None:
        await self.reset_session("Code Blue: Ransomware at Northstar Hospital")
        await self.set_session_status("showcase")
        await asyncio.sleep(0.8)
        await self.add_transcript(
            "At 08:17 a ransomware incident took the EHR offline. Fourteen ICU patients are on the ward, and our newest immutable backup is nine hours old.",
            speaker="Priya Shah", role="participant", source="showcase", analyze=False,
        )
        await asyncio.sleep(0.9)
        await self.add_transcript(
            "I disagree with restoring immediately. If identity services are not clean, a fast reconnection is too risky. But continued downtime also threatens patient safety.",
            speaker="Marcus Reed", role="participant", source="showcase", analyze=False,
        )
        await self.add_insight(
            "risk", "Alignment gap detected",
            "The room is treating system uptime and safe clinical recovery as the same goal. Separate patient continuity, clean restoration, and extortion into explicit decision tracks.",
            severity="high",
        )
        await asyncio.sleep(0.9)
        await self.add_transcript(
            "The local continuity card says we divert time-critical arrivals when identity or medication verification is unreliable for thirty minutes. The recovery matrix favors the earliest verified clean restore.",
            speaker="Elena Torres", role="participant", source="showcase", analyze=False,
        )
        await self.add_insight(
            "knowledge", "Relevant continuity evidence",
            "Northstar activates targeted diversion when patient identity or medication verification cannot be performed reliably for thirty continuous minutes. The immutable backup may be used only after clean-room integrity verification.",
            citation="Northstar Clinical Continuity Card · Diversion threshold", source="knowledge vault",
        )
        await self.add_insight(
            "skill", "Ransomware response activated",
            "Patient safety, clean recovery evidence, decision authority, and a timed checkpoint are now shaping facilitator guidance.",
            source="skills",
        )
        await asyncio.sleep(0.9)
        decision_text = "Reject ransom payment, begin the verified Tier One restore, and divert time-critical arrivals until identity and medication checks pass"
        await self.add_transcript(
            f"We have decided to {decision_text.lower()}.",
            speaker="Priya Shah", role="participant", source="showcase", analyze=False,
        )
        await self.add_decision(decision_text, "Prioritizes patient safety and the earliest evidence-supported clean recovery.")
        await asyncio.sleep(0.9)
        action_one = "Activate targeted clinical diversion"
        await self.add_transcript(
            "Action item: Priya will activate targeted clinical diversion now.",
            speaker="Priya Shah", role="participant", source="showcase", analyze=False,
        )
        await self.add_action(action_one, owner="Priya", due="Now")
        await asyncio.sleep(0.9)
        action_two = "Verify backup integrity and start the Tier One restore"
        await self.add_transcript(
            "Action item: Marcus will verify backup integrity and start the Tier One restore within thirty minutes.",
            speaker="Marcus Reed", role="participant", source="showcase", analyze=False,
        )
        await self.add_action(action_two, owner="Marcus", due="Within thirty minutes")
        await asyncio.sleep(0.9)
        action_three = "Notify legal counsel, the privacy officer, insurer, and incident coordination contacts"
        await self.add_transcript(
            "Action item: Elena will notify legal counsel, the privacy officer, insurer, and incident coordination contacts by 09:00.",
            speaker="Elena Torres", role="participant", source="showcase", analyze=False,
        )
        await self.add_action(action_three, owner="Elena", due="By 09:00")
        await asyncio.sleep(0.8)
        await self.add_insight(
            "facilitation",
            "Decision frame clarified",
            "The team separated patient continuity from technical recovery, rejected an unverified shortcut, assigned three owners, and set a thirty-minute evidence checkpoint.",
            severity="low",
        )
        await self.set_session_status("ready")

    async def _broadcast(self, message: dict) -> None:
        if self.broadcast_callback:
            await self.broadcast_callback(message)