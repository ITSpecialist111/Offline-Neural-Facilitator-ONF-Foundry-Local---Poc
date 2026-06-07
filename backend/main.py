"""FastAPI backend for the Offline Neural Facilitator (ONF).

Reliability notes:
- A single lifespan handler initializes the VoiceService exactly once (the old
  build registered two ``startup`` handlers and initialized everything twice).
- Initialization is wrapped so the server *always* comes up; missing optional
  capabilities are reported via ``/health`` rather than crashing the process.
- Endpoints that need an unavailable capability return a clear ``503`` instead
  of a 500 stack trace, so the UI can degrade gracefully.
"""

from __future__ import annotations

import asyncio
import os
import shutil
import time
from contextlib import asynccontextmanager

import numpy as np
import uvicorn
from fastapi import (
    Body,
    FastAPI,
    Form,
    HTTPException,
    UploadFile,
    File,
    WebSocket,
)
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from backend.config import get_settings
from backend.services.voice_service import VoiceService

settings = get_settings()

# Global state ---------------------------------------------------------------
voice_service: VoiceService | None = None
active_websockets: list[WebSocket] = []
audio_queue: "asyncio.Queue[bytes | None]" = asyncio.Queue()


@asynccontextmanager
async def lifespan(app: FastAPI):
    global voice_service
    try:
        voice_service = VoiceService()
        voice_service.set_broadcast_callback(broadcast_message)
        asyncio.create_task(voice_service.start_background_loop())
        asyncio.create_task(audio_processing_worker())
        print("VoiceService and background workers initialized.")
    except Exception as exc:  # pragma: no cover - defensive, should not happen now
        print(f"FATAL: VoiceService failed to initialize: {exc}")
        voice_service = None
    yield
    # Shutdown
    if voice_service:
        voice_service.bg_loop_active = False
    await audio_queue.put(None)


app = FastAPI(title="Offline Neural Facilitator", lifespan=lifespan)

os.makedirs(settings.output_dir, exist_ok=True)
app.mount("/audio", StaticFiles(directory=settings.output_dir), name="audio")

# CORS. "*" cannot be combined with credentials, so disable credentials then.
allow_all = settings.cors_origins == ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=not allow_all,
    allow_methods=["*"],
    allow_headers=["*"],
)


def require_service() -> VoiceService:
    if voice_service is None:
        raise HTTPException(status_code=503, detail="VoiceService not initialized")
    return voice_service


# ---------------------------------------------------------------------------
# Health / status
# ---------------------------------------------------------------------------
@app.get("/")
def read_root():
    return {"status": "Facilitator AI Backend Running"}


@app.get("/health")
def health():
    """Detailed capability snapshot for the UI and operators."""
    if voice_service is None:
        return {"status": "degraded", "voice_service": False, "config": settings.summary()}
    return {
        "status": "ok",
        "voice_service": True,
        "config": settings.summary(),
        "components": voice_service.status(),
    }


# ---------------------------------------------------------------------------
# Transcription + chat
# ---------------------------------------------------------------------------
@app.post("/transcribe")
async def transcribe_audio(file: UploadFile = File(...), mode: str = Form("reflex")):
    vs = require_service()
    temp_filename = "temp_upload_recording.wav"
    try:
        with open(temp_filename, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        user_input = vs.transcribe_with_whisper(temp_filename)

        if mode == "reason":
            response_text = await vs.reasoning(user_input)
        else:
            response_text = await vs.process_input(user_input)

        if response_text and mode != "reason" and vs.tts_service and vs.tts_service.available:
            await vs.tts_service.generate_and_play_speech(response_text)

        insight = vs.generate_insight()
        return {
            "transcription": user_input,
            "response": response_text,
            "insight": insight,
            "mode": mode,
        }
    except HTTPException:
        raise
    except Exception as exc:
        print(f"Error processing audio: {exc}")
        raise HTTPException(status_code=500, detail=str(exc))
    finally:
        if os.path.exists(temp_filename):
            os.remove(temp_filename)


class ChatRequest(BaseModel):
    query: str


@app.post("/chat")
async def chat_agent(request: ChatRequest):
    vs = require_service()
    response = await vs.process_input(request.query)
    return {"response": response}


# ---------------------------------------------------------------------------
# Insights / summaries / agenda
# ---------------------------------------------------------------------------
@app.post("/action-items")
async def generate_action_items():
    vs = require_service()
    return {"action_items": vs.generate_action_items()}


@app.get("/action-items")
async def generate_action_items_get():
    return await generate_action_items()


@app.post("/summary")
async def generate_summary():
    vs = require_service()
    return {"summary": vs.generate_summary()}


@app.post("/agenda/check")
async def check_agenda():
    vs = require_service()
    return {"current_topic": vs.check_agenda()}


# ---------------------------------------------------------------------------
# Knowledge vault
# ---------------------------------------------------------------------------
class KnowledgeUpload(BaseModel):
    text: str


@app.post("/upload-knowledge")
async def upload_knowledge(upload: KnowledgeUpload):
    vs = require_service()
    if not upload.text.strip():
        raise HTTPException(status_code=400, detail="Text content cannot be empty")
    vs.update_vault(upload.text)
    return {"status": "success", "message": "Knowledge vault updated"}


@app.post("/upload-file")
async def upload_file(file: UploadFile = File(...)):
    vs = require_service()
    temp_filename = f"temp_{file.filename}"
    try:
        with open(temp_filename, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        text_content = ""
        name = (file.filename or "").lower()
        if name.endswith(".pdf"):
            text_content = vs.parse_pdf(temp_filename)
        elif name.endswith(".txt"):
            with open(temp_filename, "r", encoding="utf-8") as f:
                text_content = f.read()

        if text_content:
            vs.update_vault(text_content)
            return {"status": "success", "message": f"Processed {file.filename}"}
        raise HTTPException(status_code=400, detail="Could not extract text from file")
    except HTTPException:
        raise
    except Exception as exc:
        print(f"Error processing file upload: {exc}")
        raise HTTPException(status_code=500, detail=str(exc))
    finally:
        if os.path.exists(temp_filename):
            try:
                os.remove(temp_filename)
            except Exception:
                pass


# ---------------------------------------------------------------------------
# Skills
# ---------------------------------------------------------------------------
@app.get("/skills")
async def list_skills():
    if voice_service is None or voice_service.skill_service is None:
        return {"skills": []}
    return {"skills": voice_service.skill_service.list_skills()}


@app.post("/skills/upload")
async def upload_skill(file: UploadFile = File(...)):
    vs = require_service()
    if vs.skill_service is None:
        raise HTTPException(status_code=503, detail="Skill service unavailable")
    try:
        skill_name = (file.filename or "").replace(".md", "").replace("SKILL", "").strip("._- ")
        if not skill_name:
            skill_name = f"skill_{int(time.time())}"
        skill_dir = os.path.join(vs.skill_service.skills_dir, skill_name)
        os.makedirs(skill_dir, exist_ok=True)
        with open(os.path.join(skill_dir, "SKILL.md"), "wb") as f:
            f.write(await file.read())
        vs.skill_service.load_skills()
        return {"status": "success", "skill": skill_name}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


# ---------------------------------------------------------------------------
# Reports / exports
# ---------------------------------------------------------------------------
@app.post("/report/generate")
async def generate_report(data: dict = Body(...)):
    vs = require_service()
    if vs.report_service is None:
        raise HTTPException(status_code=503, detail="Report service unavailable")
    filepath = vs.report_service.generate_report(
        data.get("transcript", []),
        data.get("insights", []),
        data.get("summary", ""),
        data.get("topic", "General"),
    )
    if filepath:
        return {"status": "success", "filepath": filepath}
    raise HTTPException(status_code=500, detail="Failed to generate report")


@app.post("/report/export/pdf")
async def export_pdf(data: dict = Body(...)):
    vs = require_service()
    if vs.report_service is None:
        raise HTTPException(status_code=503, detail="Report service unavailable")
    filepath = vs.report_service.export_pdf(
        data.get("transcript", []),
        data.get("insights", []),
        data.get("summary", ""),
        data.get("topic", "General"),
    )
    if filepath:
        return {"status": "success", "filepath": filepath}
    raise HTTPException(status_code=503, detail="PDF export unavailable (reportlab missing?)")


@app.post("/session/save")
async def save_session():
    vs = require_service()
    filepath = vs.save_session()
    if filepath:
        return {"status": "success", "filepath": filepath}
    raise HTTPException(status_code=500, detail="Failed to save session")


@app.post("/export/{format}")
async def export_data(format: str):
    vs = require_service()
    if vs.report_service is None:
        raise HTTPException(status_code=503, detail="Report service unavailable")
    data = {"history": vs.conversation_history}
    if format == "json":
        filepath = vs.report_service.export_json(data)
    elif format == "csv":
        filepath = vs.report_service.export_csv(data)
    else:
        raise HTTPException(status_code=400, detail="Invalid format. Use 'json' or 'csv'")
    if filepath:
        return {"status": "success", "filepath": filepath}
    raise HTTPException(status_code=500, detail="Failed to export data")


# ---------------------------------------------------------------------------
# Vision
# ---------------------------------------------------------------------------
@app.post("/vision/capture")
async def capture_screen():
    vs = require_service()
    if vs.vision_service is None:
        raise HTTPException(status_code=503, detail="Vision service unavailable")
    filepath = vs.vision_service.capture_screen()
    if filepath:
        return {"status": "success", "filepath": filepath}
    raise HTTPException(status_code=503, detail="Screen capture unavailable on this host")


# ---------------------------------------------------------------------------
# Text to speech (optional; UI falls back to Web Speech API on 503)
# ---------------------------------------------------------------------------
class TTSRequest(BaseModel):
    text: str


@app.post("/tts/speak")
async def tts_speak(request: TTSRequest):
    vs = require_service()
    audio_path = vs.melotts2(request.text, standalone=False)
    if audio_path and os.path.exists(audio_path):
        filename = os.path.basename(audio_path)
        return {"audio_url": f"{settings.public_base_url}/audio/{filename}"}
    # Not an error: signal the UI to use the browser's offline speech synthesis.
    raise HTTPException(status_code=503, detail="Backend TTS unavailable; use client speech synthesis")


# ---------------------------------------------------------------------------
# Debug simulation
# ---------------------------------------------------------------------------
@app.post("/debug/simulate")
async def simulate_conversation(events: list = Body(...)):
    vs = require_service()
    for event in events:
        await broadcast_message(event)
        if event.get("type") == "transcript":
            text = event.get("text", "")
            vs.conversation_history.append({"role": "user", "content": text})
            await vs.emit_transcript(text)
        await asyncio.sleep(2)
    return {"status": "simulation_complete"}


# ---------------------------------------------------------------------------
# WebSocket streaming
# ---------------------------------------------------------------------------
async def broadcast_message(message: dict):
    for websocket in list(active_websockets):
        try:
            await websocket.send_json(message)
        except Exception:
            if websocket in active_websockets:
                active_websockets.remove(websocket)


async def audio_processing_worker():
    print("Audio processing worker started.")
    webm_header = b""
    buffer = bytearray()

    while True:
        try:
            chunk = await audio_queue.get()
            if chunk is None:
                audio_queue.task_done()
                break
            if not webm_header:
                webm_header = chunk
            buffer.extend(chunk)
            audio_queue.task_done()

            # Drain anything that accumulated.
            while True:
                try:
                    chunk = audio_queue.get_nowait()
                    if chunk is None:
                        audio_queue.task_done()
                        return
                    buffer.extend(chunk)
                    audio_queue.task_done()
                except asyncio.QueueEmpty:
                    break

            if len(buffer) > 12000 and voice_service is not None:
                temp_filename = f"temp_stream_{int(time.time() * 1000)}.webm"
                data_to_write = bytes(buffer)

                def process_audio():
                    with open(temp_filename, "wb") as f:
                        if webm_header and not data_to_write.startswith(webm_header[:10]):
                            f.write(webm_header + data_to_write)
                        else:
                            f.write(data_to_write)
                    transcription = voice_service.transcribe_with_whisper(temp_filename)
                    segments = voice_service.diarize_audio(temp_filename)
                    if os.path.exists(temp_filename):
                        os.remove(temp_filename)
                    return transcription, segments

                try:
                    loop = asyncio.get_event_loop()
                    transcription, segments = await loop.run_in_executor(None, process_audio)

                    if transcription and transcription.strip():
                        clean_text = transcription.strip()
                        HALLUCINATIONS = {
                            "ok", "you", "thanks", "thank you", "ok.", "you.",
                            "thanks.", "thank you.", "subtitles by", "______.",
                        }
                        if (
                            clean_text.lower().strip(".!?") in HALLUCINATIONS
                            or "______" in clean_text
                            or len(clean_text) < 2
                        ):
                            print(f"DEBUG: Dropping hallucination: '{clean_text}'")
                        else:
                            voice_service.conversation_history.append(
                                {"role": "user", "content": clean_text}
                            )
                            await broadcast_message(
                                {"type": "transcript", "text": clean_text, "segments": segments}
                            )
                            asyncio.create_task(voice_service.emit_transcript(clean_text))
                except Exception as exc:
                    print(f"Error in audio worker processing: {exc}")

                buffer.clear()
        except Exception as exc:
            print(f"Audio worker error: {exc}")


@app.websocket("/ws/stream")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    active_websockets.append(websocket)
    print(f"WebSocket connected. Total: {len(active_websockets)}")
    try:
        while True:
            data = await websocket.receive_bytes()
            if len(data) >= 2:
                try:
                    valid_len = len(data) - (len(data) % 2)
                    if valid_len > 0:
                        samples = np.frombuffer(data[:valid_len], dtype=np.int16).astype(np.float32)
                        rms = np.sqrt(np.mean(samples ** 2))
                        energy = min(100, int(rms / 300 * 100))
                        if energy > 2:
                            await broadcast_message({"type": "voice_activity", "energy": energy})
                except Exception:
                    pass
            await audio_queue.put(data)
    except Exception as exc:
        print(f"WebSocket read error: {exc}")
    finally:
        if websocket in active_websockets:
            active_websockets.remove(websocket)
        print("WebSocket disconnected")


if __name__ == "__main__":
    uvicorn.run(app, host=settings.host, port=settings.port)
