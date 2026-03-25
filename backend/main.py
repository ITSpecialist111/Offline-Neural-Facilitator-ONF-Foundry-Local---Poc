import os
import sys
import shutil
import asyncio

# Add nested modules to path
current_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.dirname(current_dir)
sys.path.append(os.path.join(root_dir, "modules", "OpenVoice"))
sys.path.append(os.path.join(root_dir, "modules", "MeloTTS"))

from fastapi import FastAPI, UploadFile, File, WebSocket, HTTPException, Form, Body, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import uvicorn
import numpy as np
import struct
import time

# Add parent directory to path to import VoiceService
from backend.services.voice_service import VoiceService

app = FastAPI(title="Offline Neural Facilitator")

# Mount audio output directory for playback
if not os.path.exists('outputs_v2'):
    os.makedirs('outputs_v2')
app.mount("/audio", StaticFiles(directory="outputs_v2"), name="audio")

# CORS for Frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify the frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global VoiceService instance
voice_service = None

@app.on_event("startup")
async def startup_event():
    global voice_service
    # Initialize VoiceService but don't start the loop
    voice_service = VoiceService()
    print("VoiceService Initialized")

@app.get("/")
def read_root():
    return {"status": "Facilitator AI Backend Running"}

@app.post("/transcribe")
async def transcribe_audio(file: UploadFile = File(...), mode: str = Form("reflex")):
    """
    Endpoint to receive audio blob from frontend, save it, transcribe it,
    and return the text + LLM response.
    """
    if not voice_service:
        print("Error: VoiceService not initialized")
        raise HTTPException(status_code=503, detail="VoiceService not initialized")
    
    print(f"Transcribe endpoint called. Mode: {mode}")
    temp_filename = "temp_upload_recording.wav"
    
    try:
        with open(temp_filename, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
            
        # 1. Transcribe
        print(f"Received audio file. Size: {os.path.getsize(temp_filename)} bytes")
        user_input = voice_service.transcribe_with_whisper(temp_filename)
        print(f"Transcribed text: {user_input}")
        
        # 2. Process (LLM) - Reflex or Reasoning
        if mode == "reason":
            response_text = await voice_service.reasoning(user_input)
        else:
            response_text = await voice_service.process_input(user_input)
            
        print(f"AI Response: {response_text}")
        
        # 3. Text to Speech
        if response_text and mode != "reason":
             await voice_service.tts_service.generate_and_play_speech(response_text)
             
        # 4. Generate Insight/Topic
        insight = voice_service.generate_insight()
        print(f"Insight: {insight}")

        return {
            "transcription": user_input,
            "response": response_text,
            "insight": insight,
            "mode": mode
        }

        
    except Exception as e:
        print(f"Error processing audio: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if os.path.exists(temp_filename):
            os.remove(temp_filename)

@app.post("/action-items")
async def get_action_items():
    if not voice_service:
        raise HTTPException(status_code=503, detail="VoiceService not initialized")
    
    items = voice_service.generate_action_items()
    return {"action_items": items}

@app.post("/summary")
async def get_summary():
    if not voice_service:
        raise HTTPException(status_code=503, detail="VoiceService not initialized")
    
    summary = voice_service.generate_summary()
    return {"summary": summary}

class KnowledgeUpload(BaseModel):
    text: str

@app.post("/upload-knowledge")
async def upload_knowledge(upload: KnowledgeUpload):
    """
    Endpoint to receive new knowledge text and append it to the vault.
    """
    if not voice_service:
        raise HTTPException(status_code=503, detail="VoiceService not initialized")
    
    if not upload.text.strip():
        raise HTTPException(status_code=400, detail="Text content cannot be empty")
        
    try:
        voice_service.update_vault(upload.text)
        return {"status": "success", "message": "Knowledge vault updated"}
    except Exception as e:
        print(f"Error updating vault: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/upload-file")
async def upload_file(file: UploadFile = File(...)):
    """
    Endpoint to process uploaded files (PDF/Text) and add to vault.
    """
    if not voice_service:
        raise HTTPException(status_code=503, detail="VoiceService not initialized")
        
    temp_filename = f"temp_{file.filename}"
    try:
        with open(temp_filename, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
            
        text_content = ""
        if file.filename.lower().endswith('.pdf'):
            print(f"Processing PDF: {file.filename}")
            text_content = voice_service.parse_pdf(temp_filename)
        elif file.filename.lower().endswith('.txt'):
            print(f"Processing Text file: {file.filename}")
            with open(temp_filename, "r", encoding='utf-8') as f:
                text_content = f.read()
                
        if text_content:
            voice_service.update_vault(text_content)
            return {"status": "success", "message": f"Processed {file.filename}"}
        else:
            raise HTTPException(status_code=400, detail="Could not extract text from file")
            
    except Exception as e:
        print(f"Error processing file upload: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if os.path.exists(temp_filename):
            try:
                os.remove(temp_filename)
            except:
                pass


@app.post("/summary")
async def generate_summary():
    if not voice_service:
        raise HTTPException(status_code=503, detail="VoiceService not initialized")
    
    summary = voice_service.generate_summary()
    return {"summary": summary}

@app.post("/agenda/check")
async def check_agenda():
    if not voice_service:
        raise HTTPException(status_code=503, detail="VoiceService not initialized")
    
    topic = voice_service.check_agenda()
    return {"current_topic": topic}

@app.get("/skills")
async def list_skills():
    if not voice_service:
        raise HTTPException(status_code=503, detail="VoiceService not initialized")
        
    skills = voice_service.skill_service.list_skills()
    return {"skills": skills}

@app.get("/action-items")
async def generate_action_items_get(): # Support GET for simple testing
    return await generate_action_items()

@app.post("/action-items")
async def generate_action_items():
    if not voice_service:
         raise HTTPException(status_code=503, detail="VoiceService not initialized")
    
    actions = voice_service.generate_action_items()
    return {"action_items": actions}


@app.post("/report/generate")
async def generate_report(data: dict = Body(...)):
    """
    Generates a meeting report.
    Expected JSON: { "transcript": [], "insights": [], "summary": "...", "topic": "..." }
    """
    if not voice_service:
         raise HTTPException(status_code=503, detail="VoiceService not initialized")
    
    transcript = data.get("transcript", [])
    insights = data.get("insights", [])
    summary = data.get("summary", "")
    topic = data.get("topic", "General")
    
    filepath = voice_service.report_service.generate_report(transcript, insights, summary, topic)
    
    if filepath:
        return {"status": "success", "filepath": filepath}
    else:
        raise HTTPException(status_code=500, detail="Failed to generate report")

@app.post("/report/export/pdf")
async def export_pdf(data: dict = Body(...)):
    """
    Generates a PDF report.
    """
    if not voice_service:
         raise HTTPException(status_code=503, detail="VoiceService not initialized")
    
    transcript = data.get("transcript", [])
    insights = data.get("insights", [])
    summary = data.get("summary", "")
    topic = data.get("topic", "General")
    
    filepath = voice_service.report_service.export_pdf(transcript, insights, summary, topic)
    
    if filepath:
        return {"status": "success", "filepath": filepath}
    else:
        raise HTTPException(status_code=500, detail="Failed to generate PDF report")


@app.post("/session/save")
async def save_session():
    if not voice_service:
        raise HTTPException(status_code=503, detail="VoiceService not initialized")
    
    filepath = voice_service.save_session()
    if filepath:
        return {"status": "success", "filepath": filepath}
    else:
        raise HTTPException(status_code=500, detail="Failed to save session")

@app.post("/export/{format}")
async def export_data(format: str):
    if not voice_service:
        raise HTTPException(status_code=503, detail="VoiceService not initialized")
        
    data = {"history": voice_service.conversation_history}
    
    if format == "json":
        filepath = voice_service.report_service.export_json(data)
    elif format == "csv":
        filepath = voice_service.report_service.export_csv(data)
    else:
        raise HTTPException(status_code=400, detail="Invalid format. Use 'json' or 'csv'")
        
    if filepath:
        return {"status": "success", "filepath": filepath}
    else:
        raise HTTPException(status_code=500, detail="Failed to export data")



@app.post("/vision/capture")
async def capture_screen():
    if not voice_service:
         raise HTTPException(status_code=503, detail="VoiceService not initialized")
    
    filepath = voice_service.vision_service.capture_screen()
    if filepath:
        return {"status": "success", "filepath": filepath}
    else:
        raise HTTPException(status_code=500, detail="Failed to capture screen")

@app.get("/skills")
async def get_skills():
    if not voice_service:
        return {"skills": []}
    return {"skills": voice_service.skill_service.list_skills()}

@app.post("/skills/upload")
async def upload_skill(file: UploadFile = File(...)):
    if not voice_service:
        raise HTTPException(status_code=503, detail="VoiceService not initialized")
    
    try:
        # Create a directory for the skill based on filename (sanitize it)
        skill_name = file.filename.replace(".md", "").replace("SKILL", "").strip("._- ")
        if not skill_name:
            skill_name = f"skill_{int(time.time())}"
            
        skill_dir = os.path.join(voice_service.skill_service.skills_dir, skill_name)
        os.makedirs(skill_dir, exist_ok=True)
        
        file_path = os.path.join(skill_dir, "SKILL.md")
        
        with open(file_path, "wb") as f:
            content = await file.read()
            f.write(content)
            
        # Reload skills
        voice_service.skill_service.load_skills()
        # Update system prompt
        voice_service.system_message += voice_service.skill_service.get_system_prompt_addition()
        
        return {"status": "success", "skill": skill_name}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# WebSocket Manager
active_websockets = []
audio_queue = asyncio.Queue()

async def broadcast_message(message: dict):
    for websocket in list(active_websockets): # Use list() to avoid mutation issues
        try:
            await websocket.send_json(message)
        except Exception:
            if websocket in active_websockets:
                active_websockets.remove(websocket)

async def audio_processing_worker():
    """
    Background worker that drains the audio queue and processes it via VoiceService.
    """
    print("Audio processing worker started.")
    # WebM Header Cache
    webm_header = b""
    buffer = bytearray()
    
    while True:
        try:
            # 1. Get at least one chunk (blocking)
            chunk = await audio_queue.get()
            if chunk is None: # Shutdown signal
                audio_queue.task_done()
                break
            
            # Cache the first chunk as header (simplified strategy)
            if not webm_header:
                webm_header = chunk

            buffer.extend(chunk)
            audio_queue.task_done()

            # 2. Drain any accumulation that happened while we were processing
            while True:
                try:
                    chunk = audio_queue.get_nowait()
                    if chunk is None: 
                        audio_queue.task_done()
                        return # Should probably break outer loop
                    
                    buffer.extend(chunk)
                    audio_queue.task_done()
                except asyncio.QueueEmpty:
                    break
            
            # Process if we have enough data (approx 2s of compressed audio is much smaller, use time or size)
            # WebM 1s is approx 4KB-10KB depending on complexity. 12000 bytes is roughly 1.5-2.5s.
            if len(buffer) > 12000:
                # Use a specific temp path to avoid collisions
                temp_filename = f"temp_stream_{int(time.time() * 1000)}.webm"
                
                try:
                    # Capture current buffer to write (thread safe snapshot)
                    data_to_write = buffer[:]
                    
                    # Offload I/O and CPU-heavy Whisper to thread pool
                    def process_audio():
                        with open(temp_filename, "wb") as f:
                            # If this buffer doesn't start with the header (subsequent chunks), prepend it
                            if webm_header and not data_to_write.startswith(webm_header[:10]):
                                f.write(webm_header + data_to_write)
                            else:
                                f.write(data_to_write)
                        
                        # 1. Transcribe (Whisper handles WebM via ffmpeg)
                        transcription = voice_service.transcribe_with_whisper(temp_filename)
                        
                        # 2. Diarize (Mock/Real)
                        segments = voice_service.diarize_audio(temp_filename)
                        
                        # Cleanup
                        if os.path.exists(temp_filename):
                            os.remove(temp_filename)
                            
                        return transcription, segments

                    # Run sync tasks in separate thread to keep event loop free
                    loop = asyncio.get_event_loop()
                    transcription, segments = await loop.run_in_executor(None, process_audio)
                    
                    # 3. Broadcast and Update State
                    if transcription and transcription.strip():
                        clean_text = transcription.strip()
                        # Filter Hallucinations (Common Whisper artifacts during silence)
                        HALLUCINATIONS = {"ok", "you", "thanks", "thank you", "ok.", "you.", "thanks.", "thank you.", "subtitles by", "______."}
                        if clean_text.lower().strip(".!?") in HALLUCINATIONS or "______" in clean_text or len(clean_text) < 2:
                            print(f"DEBUG: Dropping hallucination: '{clean_text}'")
                        else:
                            print(f"DEBUG: Transcript: '{transcription[:50]}...'")
                            # Update conversation history safely
                            voice_service.conversation_history.append({"role": "user", "content": clean_text})
                            
                            event = {
                                "type": "transcript",
                                "text": clean_text,
                                "segments": segments
                            }
                            await broadcast_message(event)
                            
                            # Trigger Event-Driven Intelligence (New Hook) - Fire and Forget
                            if hasattr(voice_service, 'emit_transcript'):
                                 asyncio.create_task(voice_service.emit_transcript(clean_text))
                    else:
                        print("DEBUG: Silence/No text.")

                except Exception as e:
                    print(f"Error in audio worker processing: {e}")
                
                # Clear buffer (Don't slide! It breaks WebM stream)
                buffer.clear()
                
        except Exception as e:
            print(f"Audio worker error: {e}")

class ChatRequest(BaseModel):
    query: str

class TTSRequest(BaseModel):
    text: str

@app.post("/chat")
async def chat_agent(request: ChatRequest):
    if not voice_service:
        raise HTTPException(status_code=503, detail="VoiceService not initialized")
    
    # Use process_input reasoning logic (RAG + LLM)
    response = await voice_service.process_input(request.query)
    return {"response": response}

@app.post("/tts/speak")
async def tts_speak(request: TTSRequest):
    if not voice_service:
        raise HTTPException(status_code=503, detail="VoiceService not initialized")
        
    # Generate audio (standalone=False returns path)
    audio_path = voice_service.melotts2(request.text, standalone=False)
    
    if audio_path and os.path.exists(audio_path):
        filename = os.path.basename(audio_path)
        # Return URL accessible via static mount
        return {"audio_url": f"http://localhost:8000/audio/{filename}"}
    else:
        raise HTTPException(status_code=500, detail="Failed to generate audio")

@app.post("/debug/simulate")
async def simulate_conversation(events: list = Body(...)):
    if not voice_service:
        raise HTTPException(status_code=503, detail="VoiceService not initialized")
        
    print(f"Starting simulation with {len(events)} events")
    for event in events:
        # 1. Broadcast to UI
        await broadcast_message(event)
        
        # 2. Hydrate backend state (Conversation History)
        if event.get('type') == 'transcript':
             # We assume simulation sends final segments
             text = event.get('text', '')
             # Use 'role' from event if present, otherwise try to guess or default
             # (Frontend expects 'transcript' type usually for partials, but let's assume we send 'final' blocks)
             # Actually frontend accumulates 'transcript' events as USER messages if they come from WS?
             # Let's check App.jsx:
             # if (data.type === 'transcript') { setTranscript(...) {role: 'user', ...} }
             # It hardcodes 'user'.
             # To simulate ASSISTANT, we might need a different event type or update App.jsx?
             # App.jsx:
             # } else if (data.type === 'timeline_event') { ... role: 'system' ... }
             # It seems App.jsx only handles 'transcript' (User) and 'timeline_event' (System/Insight).
             # It doesn't seem to handle "Assistant" chat responses via WebSocket?
             # Backend process_input returns response, but main.py prints it. 
             # main.py does NOT broadcast assistant response via WS in `transcribe_audio`.
             # It returns it in the HTTP response.
             
             # Wait, `test_websocket_stream` only checked for 'transcript'.
             # Real usage: `transcribe_audio` (HTTP) returns `response`.
             # The WebSocket `websocket_endpoint` is for "streaming" audio chunks -> transcript.
             # It does NOT handle the LLM response.
             
             # So currently, the WebSocket is ONLY for User Transcription?
             # Let's check `backend/main.py` lines 311-323.
             # Yes, it sends `type: transcript`.
             
             # So if I want to simulate an Assistant response in the Transcript UI,
             # I need to see how App.jsx renders Assistant messages.
             # App.jsx: `transcript` state contains `{role: 'assistant', content: ...}`.
             # But it only sets that from `process_input` return?
             # Wait, App.jsx `startRecording` receives WS messages.
             # `setTranscript(prev => [...prev, { role: 'user', text: data.text ... }])`
             # It seems App.jsx supports ONLY User via WS.
             # Assistant responses come via `transcribe_audio` (POST /transcribe) or other API calls?
             # But `startRecording` only sends Audio chunks.
             # The current Frontend implementation seems to be "Live Transcription" focused.
             # "Facilitator AI" usually implies listening and intervening.
             # If I want to simulate "Assistant" speaking, I might need to hack the WS handler in App.jsx
             # OR... use `timeline_event` which renders as System?
             # App.jsx: `data.type === 'timeline_event'` -> `role: 'system'`.
             
             # Basic Simulation:
             # Just User talking + System Insights.
             # That's enough for "Live", "Items", "Risks".
             # "Items" comes from `/action-items` (HTTP).
             # So hydrating history is CRITICAL.
             
             voice_service.conversation_history.append({"role": "user", "content": text})
             if hasattr(voice_service, 'emit_transcript'):
                  await voice_service.emit_transcript(text)

        elif event.get('type') == 'timeline_event':
             # System/Insight
             pass
             
        await asyncio.sleep(2) 
    return {"status": "simulation_complete"}

@app.on_event("startup")
async def startup_event():
    global voice_service
    voice_service = VoiceService()
    if voice_service:
        voice_service.set_broadcast_callback(broadcast_message)
        asyncio.create_task(voice_service.start_background_loop())
        # Start the decoupled background worker
        asyncio.create_task(audio_processing_worker())
    print("VoiceService and Background Workers Initialized")

@app.websocket("/ws/stream")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    active_websockets.append(websocket)
    print(f"WebSocket connected. Total: {len(active_websockets)}")
    
    try:
        while True:
            # Receive audio chunk and push to queue immediately
            # This is extremely fast, keeping the WS loop responsive
            data = await websocket.receive_bytes()
            # Heartbeat Log
            # print(f".", end="", flush=True) 
            
            # 1. Calculate Real-time Energy (VAD) for visual feedback
            # Assuming 16-bit PCM mono
            if len(data) >= 2:
                try:
                    # Ensure even length for 16-bit processing
                    valid_len = len(data) - (len(data) % 2)
                    if valid_len > 0:
                        # Safer numpy conversion
                        samples = np.frombuffer(data[:valid_len], dtype=np.int16).astype(np.float32)
                        rms = np.sqrt(np.mean(samples**2))
                        # Scale to 0-100 (heuristic for speech energy)
                        energy = min(100, int(rms / 300 * 100))
                        
                        if energy > 2: # Noise gate
                            await broadcast_message({
                                "type": "voice_activity",
                                "energy": energy
                            })
                except Exception as e:
                    # Log once to avoid spam, or just print specific error
                    # print(f"Energy calc error: {e}") 
                    pass

            await audio_queue.put(data)
    except Exception as e:
        print(f"WebSocket read error: {e}")
    finally:
        if websocket in active_websockets:
            active_websockets.remove(websocket)
        print("WebSocket disconnected")

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)
