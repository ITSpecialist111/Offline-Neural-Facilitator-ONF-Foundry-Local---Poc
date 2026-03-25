from backend.llm.foundry_manager import FoundryEngine
from backend.services.tts_service import TtsService
from backend.services.transcription_service import TranscriptionService
import torch
import os
import datetime
import asyncio
import pygame
import sys

# UI Colors
PINK = '\033[95m'
CYAN = '\033[96m'
YELLOW = '\033[93m'
NEON_GREEN = '\033[92m'
RESET_COLOR = '\033[0m'

# Define the name of the log file
chat_log_filename = "chatbot_conversation_log.txt"

class VoiceService:

    def __init__(self):
        self._device = "cuda:0" if torch.cuda.is_available() else "cpu"
        self._output_dir = 'outputs_v2'
        os.makedirs(self._output_dir, exist_ok=True)
        
        # Initialize Core Services
        self.foundry = FoundryEngine()
        self.transcription_service = TranscriptionService()
        self.tts_service = TtsService(device=self._device, output_dir=self._output_dir)
        
        self.conversation_history = []
        self.system_message = self.open_file("chatbot1.txt")
        
        # Initialize Sub-Services
        from backend.services.skill_service import SkillService
        from backend.services.agenda_service import AgendaService
        from backend.services.report_service import ReportService
        from backend.services.vision_service import VisionService
        from backend.services.rag_service import RagService

        self.session_start_time = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        self.sessions_dir = "sessions"
        os.makedirs(self.sessions_dir, exist_ok=True)
        
        self.skill_service = SkillService()
        skills_prompt = self.skill_service.get_system_prompt_addition()
        if skills_prompt:
             print(f"{CYAN}Loaded Skills: {self.skill_service.list_skills()}{RESET_COLOR}")
             self.system_message += skills_prompt

        self.agenda_service = AgendaService(self.foundry)
        self.report_service = ReportService()
        self.vision_service = VisionService()
        self.rag_service = RagService()
        self.rag_service.migrate_from_file("vault.txt")

        # Background Loop State
        self.bg_loop_active = False
        self.active_websockets = [] # Track sockets for push notifications

    def set_broadcast_callback(self, callback):
        self.broadcast_callback = callback

    async def start_background_loop(self):
        """
        Starts the proactive intelligence loop.
        """
        print(f"{CYAN}Starting Proactive Intelligence Loop (Polling for Dynamics)...{RESET_COLOR}")
        self.bg_loop_active = True
        while self.bg_loop_active:
            await asyncio.sleep(15) # Check every 15 seconds for dynamics/load
            if self.conversation_history:
                # RAG check is now reactive (via emit_transcript), 
                # but we keep dynamics polling for long-term load analysis.
                await self.proactive_dynamics_check()

    async def emit_transcript(self, text: str):
        """
        Reactive hook called whenever new transcription is available.
        Triggers RAG and other immediate intelligence tasks.
        """
        if not text or not text.strip():
            return
            
        print(f"{CYAN}[Reactive] New segment: {text[:50]}...{RESET_COLOR}")
        
        # 1. Trigger Proactive RAG immediately
        await self.proactive_rag_check()
        
        # 2. Check for Skill Triggers (Already handled in process_input if manual, 
        # but for LIVE we might want to check here too if we want system to react)
        # For now, let's keep it in RAG check.

    async def proactive_rag_check(self):
        """
        Checks recent conversation against vault and pushes insights.
        """
        try:
            # Get last 2 turns
            if len(self.conversation_history) < 1:
                return

            recent_text = " ".join([m.get('content', '') or m.get('text', '') for m in self.conversation_history[-2:]])
            
            # Perform RAG search
            results = self.rag_service.search(recent_text, n_results=1)
            if results:
                top_match = results[0] # {"text": ..., "metadata": ...}
                text = top_match['text']
                source = top_match['metadata'].get('source', 'Unknown')
                
                # If we have a match, broadcast it
                if self.broadcast_callback:
                    # 1. Sidebar Insight
                    await self.broadcast_callback({
                        "type": "insight", # Changed to 'insight' for consistency
                        "subtype": "knowledge",
                        "text": f"Context Found: {text[:100]}...",
                        "citation": source 
                    })
                    # 2. Timeline Marker
                    await self.broadcast_callback({
                        "type": "timeline_event",
                        "subtype": "knowledge",
                        "text": f"Recalled info from {source}",
                        "citation": source,
                        "excerpt": text[:300] # Provide a bit more content for the popup
                    })
                    print(f"{CYAN}[Proactive] Pushed insight from {source}{RESET_COLOR}")
        except Exception as e:
            print(f"Background Loop Error (RAG): {e}")


    async def proactive_dynamics_check(self):
        """
        Analyzes conversation for Cognitive Load and Conflict.
        """
        try:
            if len(self.conversation_history) < 3:
                return

            # 1. Cognitive Load Detection (WPM)
            recent_segments = self.conversation_history[-5:]
            total_words = sum([len((m.get('content') or m.get('text', '')).split()) for m in recent_segments])
            
            # Simple heuristic: if we have 5 segments in 15 seconds (loop freq), that's high load
            # Or if total words in last 5 turns is > 100
            if total_words > 100:
                if self.broadcast_callback:
                    await self.broadcast_callback({
                        "type": "insight",
                        "subtype": "cognitive_load",
                        "text": "High information density detected. Consider pausing for clarification.",
                        "severity": "medium"
                    })
                    print(f"{YELLOW}[Proactive] High Cognitive Load detected ({total_words} words){RESET_COLOR}")

            # 2. Conflict Detection
            conflict_keywords = ["disagree", "but", "wait", "no", "stop", "wrong", "incorrect"]
            recent_text = " ".join([m.get('content', '') or m.get('text', '') for m in recent_segments]).lower()
            
            keyword_count = sum([recent_text.count(kw) for kw in conflict_keywords])
            
            if keyword_count >= 3:
                # Use Reflex to confirm tension
                print(f"{PINK}Verifying potential conflict...{RESET_COLOR}")
                analysis_prompt = f"Analyze the following meeting transcript for tension or interpersonal conflict. Respond with ONLY 'TRUE' or 'FALSE'.\n\nTranscript: {recent_text}"
                is_conflict = self.foundry.fast_reflex(analysis_prompt, system_prompt="You are a conflict mediator.")
                
                if is_conflict and "TRUE" in is_conflict.upper():
                    # Trigger Deep Reason for intervention strategy
                    print(f"{PINK}Conflict confirmed. Generating intervention strategy...{RESET_COLOR}")
                    intervention_stream = self.foundry.deep_reason(recent_text, "A conflict has been detected. Propose a neutral intervention strategy to get the meeting back on track.")
                    
                    full_intervention = ""
                    if intervention_stream:
                        for chunk in intervention_stream:
                            if chunk.choices[0].delta.content:
                                full_intervention += chunk.choices[0].delta.content
                    
                    if self.broadcast_callback:
                        await self.broadcast_callback({
                            "type": "insight",
                            "subtype": "conflict",
                            "text": "Meeting tension detected. Deep Reasoning active.",
                            "intervention": full_intervention
                        })
                        print(f"{YELLOW}[Proactive] Tension detected. Intervention pushed.{RESET_COLOR}")

        except Exception as e:
            print(f"Background Loop Error (Dynamics): {e}")

    def clean_text(self, text):
        return text.strip().lower()

    def check_agenda(self):
        """
        Triggers agenda detection based on recent conversation history.
        """
        if not self.conversation_history:
            return "No conversation yet."
            
        # Get last few turns for context
        recent_text = str(self.conversation_history[-6:])
        topic = self.agenda_service.detect_topic(recent_text)
        print(f"{CYAN}Agenda Update: Current Topic is '{topic}'{RESET_COLOR}")
        return topic

    async def process_input(self, user_input):
        """
        Processes user input and returns a response from the Reflex engine (Qwen).
        """
        print(f"{CYAN}Tú: {user_input}{RESET_COLOR}")
        self.conversation_history.append({
            "role": "user", 
            "content": user_input,
            "timestamp": datetime.datetime.now().isoformat()
        })
        
        # 1. Check for Skill Triggers
        skill_instructions, triggered_skills = self.skill_service.check_triggers(user_input)
        
        # Broadcast Skill Events
        if triggered_skills and self.broadcast_callback:
            for skill in triggered_skills:
                await self.broadcast_callback({
                    "type": "timeline_event",
                    "subtype": "skill_activated",
                    "text": f"Activated Skill: {skill}",
                    "skill": skill
                })

        # 2. Retrieve Context
        relevant_context = self.get_relevant_context(user_input)
        context_block = "\n".join(relevant_context)
        
        # 3. Formulate Prompt
        prompt = f"Context:\n{context_block}\n\nUser: {user_input}\n\nRespond as the facilitator assistant."
        
        # 4. Call Reflex Engine (Fast)
        print(f"{PINK}Generating Reflex response...{RESET_COLOR}")
        
        # Dynamic System Prompt
        current_system_prompt = self.system_message + skill_instructions
        
        response = self.foundry.fast_reflex(prompt, system_prompt=current_system_prompt)
        
        if not response:
            response = "I'm having trouble connecting to my brain."

        print(f"{NEON_GREEN}{response}{RESET_COLOR}")
        
        self.conversation_history.append({
            "role": "assistant", 
            "content": response,
            "timestamp": datetime.datetime.now().isoformat()
        })
        self._prompt1 = response
        return response

    def generate_insight(self):
        """
        Reflex task: Quick topic extraction.
        """
        if not self.conversation_history:
            return None
        
        prompt = f"Identify the main topic or a key insight from these recent messages: {str(self.conversation_history[-4:])}. Max 5 words."
        return self.foundry.fast_reflex(prompt, system_prompt="You are an analyzer.")

    def generate_action_items(self):
        """
        Reflex task: Formatting and extraction.
        """
        if not self.conversation_history:
            return None
        
        prompt = f"Extract a bulleted list of action items from this conversation: {str(self.conversation_history)}"
        return self.foundry.fast_reflex(prompt, system_prompt="You are a helpful assistant.")

    def generate_summary(self):
        """
        Reflex task: Summarization.
        (Could use 'deep_reason' if we wanted a compliance summary, but fast_reflex is good for general)
        """
        if not self.conversation_history:
            return None
            
        prompt = f"Provide a concise paragraph summarizing this conversation: {str(self.conversation_history)}"
        return self.foundry.fast_reflex(prompt, system_prompt="You are a summarizer.")

    async def reasoning(self, user_input):
        """
        Uses the 'DeepSeek' model for complex reasoning tasks.
        """
        print(f"{CYAN}Tú (Deep Think): {user_input}{RESET_COLOR}")
        self.conversation_history.append({
            "role": "user", 
            "content": user_input,
            "timestamp": datetime.datetime.now().isoformat()
        })
        
        # 1. Check for Skill Triggers
        skill_instructions, triggered_skills = self.skill_service.check_triggers(user_input)

        # 2. Retrieve Context
        relevant_context = self.get_relevant_context(user_input)
        context_block = "\n".join(relevant_context)
        
        # 3. Call Reasoning Engine
        print(f"{PINK}Thinking deeply...{RESET_COLOR}")
        
        # For Deep Reasoning, we merge instructions into the prompt typically, 
        # or system prompt if supported. Foundry deep_reason takes user input.
        # We'll prepend to context or prompt.
        augmented_input = f"{skill_instructions}\n\n{user_input}"
        
        stream = self.foundry.deep_reason(context_block, augmented_input)
        
        full_response = ""
        if stream:
            for chunk in stream:
                if chunk.choices[0].delta.content:
                    content = chunk.choices[0].delta.content
                    full_response += content
        else:
            full_response = "I had a deep thought, but forgot it."

        print(f"{NEON_GREEN}{full_response}{RESET_COLOR}")
        
        self.conversation_history.append({
            "role": "assistant",
            "content": full_response,
            "timestamp": datetime.datetime.now().isoformat()
        })
        return full_response

    def open_file(self, filepath):
        with open(filepath, 'r', encoding='utf-8') as infile:
            return infile.read()
            
    def load_vault(self):
        # Legacy method kept for interface if needed, but logic moved to RagService
        pass

    def update_vault(self, new_text):
        """
        Appends new text to vault.txt and updates the embeddings.
        """
        # Append to file for backup
        with open("vault.txt", "a", encoding='utf-8') as f:
            f.write("\n" + new_text.strip())
            
        # Add to ChromaDB
        self.rag_service.add_document(new_text.strip(), source="manual_upload")
        print(f"{NEON_GREEN}Vault updated with new knowledge.{RESET_COLOR}")

    def melotts2(self, text, standalone=True, voice_id='EN-BR'):
        if not text or not text.strip():
            text = getattr(self, '_prompt1', "Hello, I am your offline facilitator.")
            
        # Generate unique filename for this TTS generation
        filename = f"tts_{int(time.time())}_{hash(text) % 1000}.wav"
        src_path = f'{self._output_dir}/{filename}'
        
        if not self.melo_model:
            print(f"{YELLOW}Warning: MeloTTS model not loaded. Skipping TTS.{RESET_COLOR}")
            return None

        try:
             # Speed is adjustable
             speed = 1.0 
             
             # Use provided voice_id (Default: British English EN-BR)
             speaker_id = self.melo_speaker_ids.get(voice_id, self.melo_speaker_ids.get('EN-Default', 0))
             
             self.melo_model.tts_to_file(text, speaker_id, src_path, speed=speed)
             
             return self.play(src_path) if standalone else src_path
        except Exception as e:
            print(f"Error in MeloTTS: {e}")
            return None

    def parse_pdf(self, file_path):
        """
        Extracts text from a PDF file.
        """
        try:
            reader = PdfReader(file_path)
            text = ""
            for page in reader.pages:
                text += page.extract_text() + "\n"
            return text
        except Exception as e:
            print(f"Error parsing PDF: {e}")
            return None

    def diarize_audio(self, audio_path):
        """
        Runs speaker diarization on the audio file.
        """
        from backend.services.diarization_service import DiarizationService
        
        # Lazy load to avoid circular imports or startup overhead if not used
        if not hasattr(self, 'diarization_service'):
            self.diarization_service = DiarizationService()
            
        return self.diarization_service.diarize(audio_path)

    async def openvoice(self, text):
        return await self.tts_service.generate_and_play_speech(text)

    def get_relevant_context(self, user_input, top_k=3):
        """
        Retrieves the top-k most relevant context from the vault based on the user input.
        """
        results = self.rag_service.search(user_input, n_results=top_k)
        # Extract text only for LLM context, but could prepend metadata "Source: ..."
        output = []
        for r in results:
            meta = r.get('metadata') or {}
            source = meta.get('source', 'Unknown')
            output.append(f"[Source: {source}] {r['text']}")
        return output

    def chatgpt_streamed(self, user_input, system_message, conversation_history, bot_name, vault_embeddings,
                         vault_content, model):
        """
        Function to send a query to OpenAI's GPT-3.5-Turbo model, stream the response, and print each full line in yellow color.
        """
        # Get relevant context from the vault
        relevant_context = self.get_relevant_context(user_input, vault_embeddings, vault_content, model)
        # Concatenate the relevant context with the user's input
        user_input_with_context = user_input
        if relevant_context:
            user_input_with_context = "\n".join(relevant_context) + "\n\n" + user_input
        messages = [{"role": "system", "content": system_message}] + conversation_history + [
            {"role": "user", "content": user_input_with_context}]
        
        # Ensure only recent history is sent if it gets too long (optional optimization)
        if len(messages) > 10:
             messages = [messages[0]] + messages[-9:]

        streamed_completion = self.foundry.client.chat.completions.create(
            model=self.foundry.reflex_model_name,
            messages=messages,
            stream=True
        )
        self.full_response = ""
        line_buffer = ""
        for chunk in streamed_completion:
            delta_content = chunk.choices[0].delta.content
            if delta_content is not None:
                line_buffer += delta_content
                if '\n' in line_buffer:
                    lines = line_buffer.split('\n')
                    for line in lines[:-1]:
                        print(NEON_GREEN + line + RESET_COLOR)
                        self.full_response += line + '\n'
                    line_buffer = lines[-1]
        if line_buffer:
            print(NEON_GREEN + line_buffer + RESET_COLOR)
            self.full_response += line_buffer
        return self.full_response

    def transcribe_with_whisper(self, audio_file_path):
        # Extract last few words of conversation to help Whisper context
        context_prompt = None
        try:
            if self.conversation_history:
                # Take last 3 messages and join them
                recent_msg = self.conversation_history[-3:]
                context_prompt = " ".join([m.get("content", "") for m in recent_msg if m.get("role") == "user"])
                # Truncate to avoid too long prompt
                if context_prompt:
                    context_prompt = context_prompt[-200:]
            
            # Debug log
            if context_prompt:
                # Sanitize prompt to ensure it's safe (ascii/utf-8 clean)
                context_prompt = context_prompt.replace("\x00", "").strip()
                print(f"Whisper Context: '{context_prompt}'")
                
            try:
                return self.transcription_service.transcribe(audio_file_path, initial_prompt=context_prompt)
            except Exception as e:
                print(f"WARN: Transcription with prompt failed: {e}. Retrying without prompt.")
                return self.transcription_service.transcribe(audio_file_path, initial_prompt=None)
        except Exception as e:
            print(f"Error in transcribe_with_whisper: {e}")
            return ""

    # Function to record audio from the microphone and save to a file
    def record_audio(self, file_path):
        recognizer = sr.Recognizer()
        with sr.Microphone() as source:
            print(f"{NEON_GREEN}Listening... (Speak now){RESET_COLOR}")
            try:
                # Listen for audio input allowing for ambient noise adjustment
                recognizer.adjust_for_ambient_noise(source, duration=0.5)
                audio_data = recognizer.listen(source, timeout=None)
                print("Recording stopped.")
                with open(file_path, "wb") as f:
                    f.write(audio_data.get_wav_data())
            except Exception as e:
                print(f"Error recording audio: {e}")

    async def user_chatbot_conversation(self):
        # Kept for backward compatibility if needed, but updated to use shared state
        print("Starting CLI Chat...")
        while True:
            audio_file = "temp_recording.wav"
            self.record_audio(audio_file)
            user_input = self.transcribe_with_whisper(audio_file)
            os.remove(audio_file)
            
            if user_input.lower() == "exit":
                break
                
            await self.process_input(user_input)
            
            # Text to Speech
            start_time = time.time()
            await self.tts_service.generate_and_play_speech(getattr(self, '_prompt1', "Hello."))
            end_time = time.time()

        while pygame.mixer.music.get_busy():
            pygame.time.Clock().tick(10)

        pygame.mixer.music.stop()
        pygame.mixer.quit()
        # os.remove(temp_audio_file)

    def save_session(self):
        """
        Saves the current conversation history to a JSON file.
        """
        import json
        
        # Ensure timestamp exists for filename
        if not hasattr(self, 'session_start_time'):
            self.session_start_time = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            
        filename = f"session_{self.session_start_time}.json"
        filepath = os.path.join(self.sessions_dir, filename)
        
        session_data = {
            "start_time": self.session_start_time,
            "end_time": datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S"),
            "history": self.conversation_history
        }
        
        try:
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(session_data, f, indent=2, ensure_ascii=False)
            print(f"{NEON_GREEN}Session saved to {filepath}{RESET_COLOR}")
            return filepath
        except Exception as e:
            print(f"{YELLOW}Error saving session: {e}{RESET_COLOR}")
            return None
