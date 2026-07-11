"""HTTP and WebSocket API for the Offline Neural Facilitator."""

from __future__ import annotations

import asyncio
import os
import re
import tempfile
import uuid
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import Body, FastAPI, File, Form, HTTPException, UploadFile, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from backend.runtime_paths import data_path, is_frozen, resource_path
from backend.services.voice_service import VoiceService

OUTPUT_DIR = data_path("outputs_v2")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
FRONTEND_DIR = resource_path("frontend_dist")
if not FRONTEND_DIR.is_dir() and not is_frozen():
    FRONTEND_DIR = resource_path("frontend", "dist")
SERVE_FRONTEND = os.getenv("ONF_SERVE_FRONTEND", "0") == "1" and (FRONTEND_DIR / "index.html").is_file()
ALLOWED_ORIGINS = [
    origin.strip()
    for origin in os.getenv("ONF_ALLOWED_ORIGINS", "http://127.0.0.1:5173,http://localhost:5173").split(",")
    if origin.strip()
]
MAX_UPLOAD_BYTES = 20 * 1024 * 1024

voice_service: VoiceService | None = None
active_websockets: set[WebSocket] = set()


async def broadcast_message(message: dict) -> None:
    disconnected: list[WebSocket] = []
    for websocket in tuple(active_websockets):
        try:
            await websocket.send_json(message)
        except Exception:
            disconnected.append(websocket)
    for websocket in disconnected:
        active_websockets.discard(websocket)


@asynccontextmanager
async def lifespan(_app: FastAPI):
    global voice_service
    voice_service = await asyncio.to_thread(VoiceService)
    voice_service.set_broadcast_callback(broadcast_message)
    yield
    active_websockets.clear()


app = FastAPI(
    title="Offline Neural Facilitator API",
    version="2.0.0",
    description="Local-first meeting capture, facilitation and accountable outcomes.",
    lifespan=lifespan,
)
app.mount("/audio", StaticFiles(directory=str(OUTPUT_DIR)), name="audio")
if SERVE_FRONTEND and (FRONTEND_DIR / "assets").is_dir():
    app.mount("/assets", StaticFiles(directory=str(FRONTEND_DIR / "assets")), name="frontend-assets")
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)


def service() -> VoiceService:
    if voice_service is None:
        raise HTTPException(status_code=503, detail="Facilitator is still initializing")
    return voice_service


async def read_upload(file: UploadFile) -> bytes:
    data = await file.read(MAX_UPLOAD_BYTES + 1)
    if len(data) > MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=413, detail="File exceeds the 20 MB local upload limit")
    return data


class ChatRequest(BaseModel):
    query: str = Field(min_length=1, max_length=8000)
    mode: str = Field(default="reflex", pattern="^(reflex|reason)$")


class KnowledgeUpload(BaseModel):
    text: str = Field(min_length=1, max_length=250_000)
    title: str = Field(default="Manual note", max_length=160)


class TTSRequest(BaseModel):
    text: str = Field(min_length=1, max_length=4000)
    voice: str = Field(default="EN-BR", max_length=40)


class SessionCreate(BaseModel):
    topic: str = Field(default="Untitled session", max_length=120)


def status_payload() -> dict:
    return {
        "status": "ready" if voice_service else "starting",
        "service": "Offline Neural Facilitator",
        "version": app.version,
        "privacy": "local-first",
    }


@app.get("/", response_model=None)
async def root():
    if SERVE_FRONTEND:
        return FileResponse(FRONTEND_DIR / "index.html")
    return status_payload()


@app.get("/api/status")
async def api_status() -> dict:
    return status_payload()


@app.get("/health")
async def health() -> dict:
    facilitator = service()
    return {"status": "ready", "capabilities": await asyncio.to_thread(facilitator.capabilities)}


@app.get("/state")
async def state() -> dict:
    facilitator = service()
    return {"state": facilitator.snapshot(), "capabilities": await asyncio.to_thread(facilitator.capabilities)}


@app.post("/session/new")
async def new_session(request: SessionCreate) -> dict:
    return {"state": await service().reset_session(request.topic)}


@app.post("/session/save")
async def save_session() -> dict:
    filepath = await asyncio.to_thread(service().save_session)
    return {"status": "success", "filepath": filepath}


@app.post("/chat")
async def chat(request: ChatRequest) -> dict:
    response = await service().process_input(request.query, request.mode)
    return {"response": response, "mode": request.mode}


@app.post("/transcribe")
async def transcribe(file: UploadFile = File(...), mode: str = Form("reflex")) -> dict:
    if mode not in {"reflex", "reason"}:
        raise HTTPException(status_code=400, detail="Mode must be reflex or reason")
    data = await read_upload(file)
    suffix = Path(file.filename or "audio.webm").suffix or ".webm"
    temp_path = Path(tempfile.gettempdir()) / f"onf_{uuid.uuid4().hex}{suffix}"
    try:
        temp_path.write_bytes(data)
        text = await asyncio.to_thread(service().transcribe_with_whisper, str(temp_path))
        if not text:
            return {"transcription": "", "response": "", "mode": mode, "status": "silence"}
        await service().add_transcript(text, speaker="Live speaker", role="participant", source="audio")
        return {"transcription": text, "response": "", "mode": mode, "status": "captured"}
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    finally:
        temp_path.unlink(missing_ok=True)


@app.post("/summary")
async def summary() -> dict:
    value = await asyncio.to_thread(service().generate_summary)
    return {"summary": value}


@app.get("/action-items")
@app.post("/action-items")
async def action_items() -> dict:
    return {"action_items": service().generate_action_items(), "items": service().snapshot()["actions"]}


@app.get("/skills")
async def skills() -> dict:
    return {"skills": service().skill_service.list_skills()}


@app.post("/skills/upload")
async def upload_skill(file: UploadFile = File(...)) -> dict:
    if not (file.filename or "").lower().endswith(".md"):
        raise HTTPException(status_code=400, detail="Skills must be Markdown files")
    data = await read_upload(file)
    safe_name = re.sub(r"[^a-zA-Z0-9_-]+", "-", Path(file.filename or "skill").stem).strip("-") or "skill"
    skill_dir = Path(service().skill_service.skills_dir) / safe_name
    skill_dir.mkdir(parents=True, exist_ok=True)
    (skill_dir / "SKILL.md").write_bytes(data)
    service().skill_service.load_skills()
    return {"status": "success", "skill": safe_name, "skills": service().skill_service.list_skills()}


@app.post("/upload-knowledge")
async def upload_knowledge(upload: KnowledgeUpload) -> dict:
    chunks = await asyncio.to_thread(service().update_vault, upload.text, upload.title)
    return {"status": "success", "message": f"Indexed {chunks} local knowledge chunk(s)", "chunks": chunks}


@app.post("/upload-file")
async def upload_file(file: UploadFile = File(...)) -> dict:
    filename = Path(file.filename or "upload")
    suffix = filename.suffix.lower()
    if suffix not in {".pdf", ".txt", ".md"}:
        raise HTTPException(status_code=400, detail="Supported knowledge files: PDF, TXT and Markdown")
    data = await read_upload(file)
    temp_path = Path(tempfile.gettempdir()) / f"onf_upload_{uuid.uuid4().hex}{suffix}"
    try:
        temp_path.write_bytes(data)
        if suffix == ".pdf":
            text = await asyncio.to_thread(service().parse_pdf, str(temp_path))
        else:
            text = data.decode("utf-8", errors="replace")
        if not text.strip():
            raise HTTPException(status_code=400, detail="No readable text was found in the file")
        chunks = await asyncio.to_thread(service().update_vault, text, filename.name)
        return {"status": "success", "message": f"Indexed {filename.name}", "chunks": chunks}
    finally:
        temp_path.unlink(missing_ok=True)


@app.post("/tts/speak")
async def speak(request: TTSRequest) -> dict:
    try:
        path = await asyncio.to_thread(service().melotts2, request.text, False, request.voice)
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    if not path:
        raise HTTPException(status_code=500, detail="Local speech generation failed")
    return {"audio_url": f"/audio/{Path(path).name}"}


@app.post("/report/generate")
async def report(data: dict = Body(default={})) -> dict:
    snapshot = service().snapshot()
    path = await asyncio.to_thread(
        service().report_service.generate_report,
        data.get("transcript", snapshot["transcript"]),
        data.get("insights", snapshot["insights"]),
        data.get("summary", ""),
        data.get("topic", snapshot["session"]["topic"]),
    )
    if not path:
        raise HTTPException(status_code=500, detail="Report generation failed")
    return {"status": "success", "filepath": path}


@app.post("/report/export/pdf")
async def report_pdf(data: dict = Body(default={})) -> dict:
    snapshot = service().snapshot()
    path = await asyncio.to_thread(
        service().report_service.export_pdf,
        data.get("transcript", snapshot["transcript"]),
        data.get("insights", snapshot["insights"]),
        data.get("summary", ""),
        data.get("topic", snapshot["session"]["topic"]),
    )
    if not path:
        raise HTTPException(status_code=500, detail="PDF generation failed")
    return {"status": "success", "filepath": path}


@app.post("/export/{format_name}")
async def export(format_name: str) -> dict:
    snapshot = service().snapshot()
    if format_name == "json":
        path = await asyncio.to_thread(service().report_service.export_json, snapshot)
    elif format_name == "csv":
        path = await asyncio.to_thread(service().report_service.export_csv, {"history": snapshot["transcript"]})
    else:
        raise HTTPException(status_code=400, detail="Supported formats: json, csv")
    return {"status": "success", "filepath": path}


@app.post("/demo/start")
async def demo_start() -> dict:
    service().start_demo()
    return {"status": "started", "message": "Showcase scenario is running"}


@app.post("/debug/simulate")
async def simulate(events: list[dict] = Body(...)) -> dict:
    for event in events:
        if event.get("type") == "transcript":
            await service().add_transcript(
                event.get("text", ""),
                speaker=event.get("speaker", "Speaker"),
                source="simulation",
            )
        elif event.get("type") == "insight" or event.get("type") == "timeline_event":
            await service().add_insight(
                event.get("subtype", "facilitation"),
                event.get("title", "Facilitator note"),
                event.get("text", ""),
                citation=event.get("citation"),
            )
    return {"status": "simulation_complete", "processed": len(events)}


@app.websocket("/ws/stream")
async def websocket_stream(websocket: WebSocket) -> None:
    await websocket.accept()
    active_websockets.add(websocket)
    try:
        if voice_service:
            await websocket.send_json({"type": "session_state", "state": voice_service.snapshot()})
        while True:
            data = await websocket.receive()
            if data.get("type") == "websocket.disconnect":
                break
            if data.get("text"):
                # Browser heartbeat/control frames.
                if data["text"] == "ping":
                    await websocket.send_json({"type": "pong"})
                continue
            audio = data.get("bytes")
            if not audio:
                continue
            if len(audio) > MAX_UPLOAD_BYTES:
                await websocket.send_json({"type": "error", "message": "Audio segment exceeds 20 MB"})
                continue
            temp_path = Path(tempfile.gettempdir()) / f"onf_stream_{uuid.uuid4().hex}.webm"
            try:
                temp_path.write_bytes(audio)
                text = await asyncio.to_thread(service().transcribe_with_whisper, str(temp_path))
                if text:
                    await service().add_transcript(text, speaker="Live speaker", role="participant", source="audio")
            except Exception as exc:
                await websocket.send_json({"type": "error", "message": str(exc)})
            finally:
                temp_path.unlink(missing_ok=True)
    except (WebSocketDisconnect, RuntimeError):
        pass
    finally:
        active_websockets.discard(websocket)


@app.get("/{full_path:path}", include_in_schema=False, response_model=None)
async def frontend_fallback(full_path: str):
    if not SERVE_FRONTEND:
        raise HTTPException(status_code=404, detail="Not found")
    candidate = (FRONTEND_DIR / full_path).resolve()
    if candidate.is_file() and FRONTEND_DIR.resolve() in candidate.parents:
        return FileResponse(candidate)
    return FileResponse(FRONTEND_DIR / "index.html")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8000)