"""VoiceService - the orchestration "brain" of ONF.

Reliability-first redesign:
- Importing this module pulls in **no** heavy ML libraries; everything optional
  is imported lazily inside the services it owns.
- Every sub-service is constructed defensively. If one fails (missing model,
  missing dependency, no GPU, ...) it is disabled and the rest keep working,
  instead of taking the whole backend down. This is what stops the components
  from "breaking each other".
- A :meth:`status` snapshot powers the ``/health`` endpoint so the UI/operator
  can see exactly which capabilities are live.
"""

from __future__ import annotations

import datetime
import asyncio
import json
import os

from backend.config import get_settings
from backend.llm.foundry_manager import FoundryEngine

# Console colors (kept for backward-compatible imports / logging)
PINK = "\033[95m"
CYAN = "\033[96m"
YELLOW = "\033[93m"
NEON_GREEN = "\033[92m"
RESET_COLOR = "\033[0m"


class VoiceService:
    def __init__(self):
        self.settings = get_settings()
        self._output_dir = self.settings.output_dir
        os.makedirs(self._output_dir, exist_ok=True)

        self.conversation_history = []
        self.broadcast_callback = None
        self.bg_loop_active = False

        self.session_start_time = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        self.sessions_dir = self.settings.sessions_dir
        os.makedirs(self.sessions_dir, exist_ok=True)

        # System persona prompt (best-effort; never fatal)
        self.system_message = self._read_persona()

        # --- Core engine (always constructed; degrades internally) --------
        self.foundry = self._safe("FoundryEngine", lambda: FoundryEngine())

        # --- Optional / heavy services (each isolated) --------------------
        self.transcription_service = self._safe(
            "TranscriptionService",
            self._build_transcription,
        )
        self.tts_service = self._safe("TtsService", self._build_tts)
        self.skill_service = self._safe("SkillService", self._build_skills)
        self.agenda_service = self._safe("AgendaService", self._build_agenda)
        self.report_service = self._safe("ReportService", self._build_report)
        self.vision_service = self._safe("VisionService", self._build_vision)
        self.rag_service = self._safe("RagService", self._build_rag)
        self.diarization_service = self._safe("DiarizationService", self._build_diarization)

        if self.rag_service:
            try:
                self.rag_service.migrate_from_file("vault.txt")
            except Exception as exc:
                print(f"[VoiceService] vault migration skipped: {exc}")

        if self.skill_service:
            try:
                skills = self.skill_service.list_skills()
                if skills:
                    print(f"{CYAN}Loaded Skills: {skills}{RESET_COLOR}")
            except Exception:
                pass

        print(f"{NEON_GREEN}VoiceService ready: {json.dumps(self.status())}{RESET_COLOR}")

    # ------------------------------------------------------------------
    # Construction helpers
    # ------------------------------------------------------------------
    def _safe(self, name, factory):
        """Run a constructor, logging and swallowing any failure."""
        try:
            return factory()
        except Exception as exc:
            print(f"{YELLOW}[VoiceService] {name} unavailable: {exc}{RESET_COLOR}")
            return None

    def _build_transcription(self):
        from backend.services.transcription_service import TranscriptionService

        return TranscriptionService(
            model_size=self.settings.whisper_model_size,
            enabled=self.settings.enable_whisper,
        )

    def _build_tts(self):
        from backend.services.tts_service import TtsService

        return TtsService(output_dir=self._output_dir, enabled=self.settings.enable_tts)

    def _build_skills(self):
        from backend.services.skill_service import SkillService

        return SkillService()

    def _build_agenda(self):
        from backend.services.agenda_service import AgendaService

        return AgendaService(self.foundry)

    def _build_report(self):
        from backend.services.report_service import ReportService

        return ReportService()

    def _build_vision(self):
        from backend.services.vision_service import VisionService

        return VisionService(enabled=self.settings.enable_vision)

    def _build_rag(self):
        from backend.services.rag_service import RagService

        return RagService(persist_directory=self.settings.chroma_dir)

    def _build_diarization(self):
        from backend.services.diarization_service import DiarizationService

        return DiarizationService(enabled=self.settings.enable_diarization)

    def _read_persona(self):
        for candidate in ("chatbot1.txt",):
            try:
                if os.path.exists(candidate):
                    with open(candidate, "r", encoding="utf-8") as fh:
                        return fh.read()
            except Exception:
                pass
        return "You are the Offline Neural Facilitator, a concise, helpful meeting assistant."

    # ------------------------------------------------------------------
    # Status / health
    # ------------------------------------------------------------------
    def status(self) -> dict:
        engine = self.foundry.status() if self.foundry else {"offline_available": False}
        return {
            "engine": engine,
            "transcription": bool(self.transcription_service and self.transcription_service.available),
            "tts": bool(self.tts_service and self.tts_service.available),
            "rag": bool(self.rag_service),
            "rag_backend": getattr(self.rag_service, "backend", None) if self.rag_service else None,
            "skills": self.skill_service.list_skills() if self.skill_service else [],
            "vision": bool(self.vision_service),
            "diarization": bool(self.diarization_service),
        }

    def set_broadcast_callback(self, callback):
        self.broadcast_callback = callback

    # ------------------------------------------------------------------
    # Proactive intelligence loop
    # ------------------------------------------------------------------
    async def start_background_loop(self):
        if not self.settings.enable_proactive_loop:
            print(f"{CYAN}Proactive loop disabled by configuration.{RESET_COLOR}")
            return
        print(f"{CYAN}Starting Proactive Intelligence Loop...{RESET_COLOR}")
        self.bg_loop_active = True
        while self.bg_loop_active:
            await asyncio.sleep(15)
            if self.conversation_history:
                await self.proactive_dynamics_check()

    async def emit_transcript(self, text: str):
        if not text or not text.strip():
            return
        print(f"{CYAN}[Reactive] New segment: {text[:50]}...{RESET_COLOR}")
        await self.proactive_rag_check()

    async def proactive_rag_check(self):
        try:
            if not self.rag_service or not self.conversation_history:
                return
            recent_text = " ".join(
                m.get("content", "") or m.get("text", "")
                for m in self.conversation_history[-2:]
            )
            results = self.rag_service.search(recent_text, n_results=1)
            if results and self.broadcast_callback:
                top = results[0]
                text = top["text"]
                source = (top.get("metadata") or {}).get("source", "Unknown")
                await self.broadcast_callback(
                    {
                        "type": "insight",
                        "subtype": "knowledge",
                        "text": f"Context Found: {text[:100]}...",
                        "citation": source,
                    }
                )
                await self.broadcast_callback(
                    {
                        "type": "timeline_event",
                        "subtype": "knowledge",
                        "text": f"Recalled info from {source}",
                        "citation": source,
                        "excerpt": text[:300],
                    }
                )
        except Exception as exc:
            print(f"Background Loop Error (RAG): {exc}")

    async def proactive_dynamics_check(self):
        try:
            if len(self.conversation_history) < 3:
                return
            recent_segments = self.conversation_history[-5:]
            total_words = sum(
                len((m.get("content") or m.get("text", "")).split()) for m in recent_segments
            )
            if total_words > 100 and self.broadcast_callback:
                await self.broadcast_callback(
                    {
                        "type": "insight",
                        "subtype": "cognitive_load",
                        "text": "High information density detected. Consider pausing for clarification.",
                        "severity": "medium",
                    }
                )

            conflict_keywords = ["disagree", "but", "wait", "no", "stop", "wrong", "incorrect"]
            recent_text = " ".join(
                m.get("content", "") or m.get("text", "") for m in recent_segments
            ).lower()
            keyword_count = sum(recent_text.count(kw) for kw in conflict_keywords)

            if keyword_count >= 3 and self.foundry:
                analysis_prompt = (
                    "Analyze the following meeting transcript for tension or interpersonal "
                    "conflict. Respond with ONLY 'TRUE' or 'FALSE'.\n\nTranscript: " + recent_text
                )
                is_conflict = self.foundry.fast_reflex(
                    analysis_prompt, system_prompt="You are a conflict mediator."
                )
                if is_conflict and "TRUE" in is_conflict.upper():
                    intervention_stream = self.foundry.deep_reason(
                        recent_text,
                        "A conflict has been detected. Propose a neutral intervention strategy "
                        "to get the meeting back on track.",
                    )
                    full_intervention = self._consume_stream(intervention_stream)
                    if self.broadcast_callback:
                        await self.broadcast_callback(
                            {
                                "type": "insight",
                                "subtype": "conflict",
                                "text": "Meeting tension detected. Deep Reasoning active.",
                                "intervention": full_intervention,
                            }
                        )
        except Exception as exc:
            print(f"Background Loop Error (Dynamics): {exc}")

    # ------------------------------------------------------------------
    # Conversation
    # ------------------------------------------------------------------
    @staticmethod
    def _consume_stream(stream) -> str:
        out = ""
        if not stream:
            return out
        try:
            for chunk in stream:
                delta = chunk.choices[0].delta.content
                if delta:
                    out += delta
        except Exception as exc:
            print(f"[VoiceService] stream consume error: {exc}")
        return out

    def check_agenda(self):
        if not self.conversation_history:
            return "No conversation yet."
        if not self.agenda_service:
            return "Unknown"
        recent_text = str(self.conversation_history[-6:])
        return self.agenda_service.detect_topic(recent_text)

    def get_relevant_context(self, user_input, top_k=3):
        if not self.rag_service:
            return []
        results = self.rag_service.search(user_input, n_results=top_k)
        output = []
        for r in results:
            source = (r.get("metadata") or {}).get("source", "Unknown")
            output.append(f"[Source: {source}] {r['text']}")
        return output

    async def process_input(self, user_input):
        self.conversation_history.append(
            {
                "role": "user",
                "content": user_input,
                "timestamp": datetime.datetime.now().isoformat(),
            }
        )

        skill_instructions, triggered_skills = ("", [])
        if self.skill_service:
            skill_instructions, triggered_skills = self.skill_service.check_triggers(user_input)
            if triggered_skills and self.broadcast_callback:
                for skill in triggered_skills:
                    await self.broadcast_callback(
                        {
                            "type": "timeline_event",
                            "subtype": "skill_activated",
                            "text": f"Activated Skill: {skill}",
                            "skill": skill,
                        }
                    )

        context_block = "\n".join(self.get_relevant_context(user_input))
        prompt = (
            f"Context:\n{context_block}\n\nUser: {user_input}\n\n"
            "Respond as the facilitator assistant."
        )
        current_system_prompt = self.system_message + skill_instructions

        response = None
        if self.foundry:
            response = self.foundry.fast_reflex(prompt, system_prompt=current_system_prompt)
        if not response:
            response = (
                "The local model is not reachable right now. Start Foundry Local "
                "(e.g. `foundry model run qwen2.5-0.5b`) or enable a hybrid online model."
            )

        self.conversation_history.append(
            {
                "role": "assistant",
                "content": response,
                "timestamp": datetime.datetime.now().isoformat(),
            }
        )
        self._prompt1 = response
        return response

    async def reasoning(self, user_input):
        self.conversation_history.append(
            {
                "role": "user",
                "content": user_input,
                "timestamp": datetime.datetime.now().isoformat(),
            }
        )
        skill_instructions = ""
        if self.skill_service:
            skill_instructions, _ = self.skill_service.check_triggers(user_input)
        context_block = "\n".join(self.get_relevant_context(user_input))
        augmented_input = f"{skill_instructions}\n\n{user_input}"

        full_response = ""
        if self.foundry:
            stream = self.foundry.deep_reason(context_block, augmented_input)
            full_response = self._consume_stream(stream)
        if not full_response:
            full_response = (
                "Deep reasoning is unavailable. Ensure the reasoning model is loaded in "
                "Foundry Local or enable hybrid online for Deep Think."
            )

        self.conversation_history.append(
            {
                "role": "assistant",
                "content": full_response,
                "timestamp": datetime.datetime.now().isoformat(),
            }
        )
        return full_response

    def generate_insight(self):
        if not self.conversation_history or not self.foundry:
            return None
        prompt = (
            "Identify the main topic or a key insight from these recent messages: "
            f"{str(self.conversation_history[-4:])}. Max 5 words."
        )
        return self.foundry.fast_reflex(prompt, system_prompt="You are an analyzer.")

    def generate_action_items(self):
        if not self.conversation_history or not self.foundry:
            return None
        prompt = (
            "Extract a bulleted list of action items from this conversation: "
            f"{str(self.conversation_history)}"
        )
        return self.foundry.fast_reflex(prompt, system_prompt="You are a helpful assistant.")

    def generate_summary(self):
        if not self.conversation_history or not self.foundry:
            return None
        prompt = (
            "Provide a concise paragraph summarizing this conversation: "
            f"{str(self.conversation_history)}"
        )
        return self.foundry.fast_reflex(prompt, system_prompt="You are a summarizer.")

    # ------------------------------------------------------------------
    # Knowledge / files / media
    # ------------------------------------------------------------------
    def update_vault(self, new_text):
        try:
            with open("vault.txt", "a", encoding="utf-8") as f:
                f.write("\n" + new_text.strip())
        except Exception as exc:
            print(f"[VoiceService] could not append vault.txt: {exc}")
        if self.rag_service:
            self.rag_service.add_document(new_text.strip(), source="manual_upload")

    def parse_pdf(self, file_path):
        try:
            from pypdf import PdfReader

            reader = PdfReader(file_path)
            return "\n".join((page.extract_text() or "") for page in reader.pages)
        except Exception as exc:
            print(f"[VoiceService] Error parsing PDF: {exc}")
            return None

    def transcribe_with_whisper(self, audio_file_path):
        if not self.transcription_service:
            return ""
        context_prompt = None
        try:
            if self.conversation_history:
                recent = self.conversation_history[-3:]
                context_prompt = " ".join(
                    m.get("content", "") for m in recent if m.get("role") == "user"
                )
                if context_prompt:
                    context_prompt = context_prompt[-200:].replace("\x00", "").strip()
        except Exception:
            context_prompt = None
        try:
            return self.transcription_service.transcribe(
                audio_file_path, initial_prompt=context_prompt
            )
        except Exception as exc:
            print(f"[VoiceService] transcription failed ({exc}); retrying without prompt.")
            try:
                return self.transcription_service.transcribe(audio_file_path, initial_prompt=None)
            except Exception:
                return ""

    def diarize_audio(self, audio_path):
        if not self.diarization_service:
            return []
        return self.diarization_service.diarize(audio_path)

    def melotts2(self, text, standalone=False, voice_id="EN-Default"):
        """Render speech via the optional backend TTS service. Returns a path or None.

        Returning None is a normal, supported outcome - the frontend then uses the
        browser's offline Web Speech API instead.
        """
        if not self.tts_service or not self.tts_service.available:
            return None
        if not text or not text.strip():
            text = getattr(self, "_prompt1", "Hello, I am your offline facilitator.")
        return self.tts_service.generate_speech(text, speaker_key=voice_id)

    # ------------------------------------------------------------------
    # Session
    # ------------------------------------------------------------------
    def save_session(self):
        filename = f"session_{self.session_start_time}.json"
        filepath = os.path.join(self.sessions_dir, filename)
        session_data = {
            "start_time": self.session_start_time,
            "end_time": datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S"),
            "history": self.conversation_history,
        }
        try:
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(session_data, f, indent=2, ensure_ascii=False)
            return filepath
        except Exception as exc:
            print(f"{YELLOW}Error saving session: {exc}{RESET_COLOR}")
            return None
