import pyaudio
import torch
from openvoice import se_extractor
from openvoice.api import ToneColorConverter
from melo.api import TTS
from sentence_transformers import SentenceTransformer, util
import argparse
import wave
from zipfile import ZipFile
import langid
import openai
from openai import OpenAI
import time
import speech_recognition as sr
from faster_whisper import WhisperModel
import os
import pygame

PINK = '\033[95m'
CYAN = '\033[96m'
YELLOW = '\033[93m'
NEON_GREEN = '\033[92m'
RESET_COLOR = '\033[0m'

model_size = "medium"
try:
    print(f"{CYAN}Initializing Whisper on GPU (CUDA)...{RESET_COLOR}")
    whisper_model = WhisperModel(model_size, device="cuda", compute_type="float16")
except Exception as e:
    print(f"{YELLOW}Warning: GPU initialization failed ({e}). Fallback to CPU.{RESET_COLOR}")
    whisper_model = WhisperModel(model_size, device="cpu", compute_type="int8")
# import subprocess
# import re
from backend.llm.foundry_manager import FoundryEngine

# Define the name of the log file
chat_log_filename = "chatbot_conversation_log.txt"
class VoiceService:

    def __init__(self):
        self._ckpt_converter = 'modules/OpenVoice/checkpoints_v2/converter'
        self._device = "cuda:0" if torch.cuda.is_available() else "cpu"
        print(f"{CYAN}Debug: Compute Device Selected: {self._device}{RESET_COLOR}")
        self._output_dir = 'outputs_v2'

        self._tone_color_converter = ToneColorConverter(f'{self._ckpt_converter}/config.json', device=self._device)
        self._tone_color_converter.load_ckpt(f'{self._ckpt_converter}/checkpoint.pth')

        os.makedirs(self._output_dir, exist_ok=True)
        
        # Initialize RAG and Chat components via FoundryEngine
        self.foundry = FoundryEngine()
        
        self.conversation_history = []
        self.system_message = self.open_file("chatbot1.txt")
        self.rag_model = SentenceTransformer("all-MiniLM-L6-v2")
        self.load_vault()

    def process_input(self, user_input):
        """
        Uses the 'Reflex' model for standard chat interaction + RAG context injection.
        """
        print(f"{CYAN}Tú: {user_input}{RESET_COLOR}")
        self.conversation_history.append({"role": "user", "content": user_input})
        
        # 1. Retrieve Context
        relevant_context = self.get_relevant_context(user_input, self.vault_embeddings_tensor, self.vault_content, self.rag_model)
        context_block = "\n".join(relevant_context)
        
        # 2. Formulate Prompt
        prompt = f"Context:\n{context_block}\n\nUser: {user_input}\n\nRespond as the facilitator assistant."
        
        # 3. Call Reflex Engine (Fast)
        print(f"{PINK}Generating Reflex response...{RESET_COLOR}")
        response = self.foundry.fast_reflex(prompt, system_prompt=self.system_message)
        
        if not response:
            response = "I'm having trouble connecting to my brain."

        print(f"{NEON_GREEN}{response}{RESET_COLOR}")
        
        self.conversation_history.append({"role": "assistant", "content": response})
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

    def open_file(self, filepath):
        with open(filepath, 'r', encoding='utf-8') as infile:
            return infile.read()

    def get_relevant_context(self, user_input, vault_embeddings, vault_content, model, top_k=3):
        """
        Retrieves the top-k most relevant context from the vault based on the user input.
        """
        if vault_embeddings.nelement() == 0:  # Check if the tensor has any elements
            return []

        # Encode the user input
        input_embedding = model.encode([user_input])
        # Compute cosine similarity between the input and vault embeddings
        cos_scores = util.cos_sim(input_embedding, vault_embeddings)[0]
        # Adjust top_k if it's greater than the number of available scores
        top_k = min(top_k, len(cos_scores))
        # Sort the scores and get the top-k indices
        top_indices = torch.topk(cos_scores, k=top_k)[1].tolist()
        # Get the corresponding context from the vault
        relevant_context = [vault_content[idx].strip() for idx in top_indices]
        return relevant_context

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
        # Load the model
        segments, info = whisper_model.transcribe(audio_file_path, beam_size=5)
        self.transcription = ""
        for segment in segments:
            self.transcription += segment.text + " "
        # Transcribe the audio
        self.result = self.transcription.strip()
        return self.transcription.strip()

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

    def user_chatbot_conversation(self):
        # Kept for backward compatibility if needed, but updated to use shared state
        print("Starting CLI Chat...")
        while True:
            audio_file = "temp_recording.wav"
            self.record_audio(audio_file)
            user_input = self.transcribe_with_whisper(audio_file)
            os.remove(audio_file)
            
            if user_input.lower() == "exit":
                break
                
            self.process_input(user_input)
            
            # Text to Speech
            start_time = time.time()
            VoiceService.openvoice(self, " ") 
            end_time = time.time()
            print(f"Openvoice Execution Time: {end_time - start_time}")

    def openvoice_v2(self):
        reference_speaker = 'modules/OpenVoice/resources/example_reference.mp3'  # This is the voice you want to clone
        target_se, audio_name = se_extractor.get_se(reference_speaker, self._tone_color_converter, vad=True)

        texts = {
            'EN': f"{self._prompt1}", # Using prompt1 from process_input
        }

        src_path = f'{self._output_dir}/tmp.wav'
        speed = 1.3

        for language, text in texts.items():
            model = TTS(language='EN', device=self._device)
            speaker_ids = model.hps.data.spk2id

            for speaker_key in speaker_ids.keys():
                speaker_id = speaker_ids[speaker_key]
                speaker_key = speaker_key.lower().replace('_', '-')
                # print(speaker_key)
                source_se = torch.load(f'modules/OpenVoice/checkpoints_v2/base_speakers/ses/{speaker_key}.pth', map_location=self._device)
                model.tts_to_file(text, 3, src_path, speed=speed)
                save_path = f'{self._output_dir}/output_v2_{speaker_key}and{language}.wav'

                # Run the tone color converter
                encode_message = "@MyShell"
                self._tone_color_converter.convert(
                    audio_src_path=src_path,
                    src_se=source_se,
                    tgt_se=target_se,
                    output_path=save_path,
                    message=encode_message)
                
                play_audio =  self.play(save_path)
                play_audio

    def openvoice(self, text):

        reference_speaker = 'modules/OpenVoice/resources/example_reference.mp3'  # This is the voice you want to clone
        target_se, audio_name = se_extractor.get_se(reference_speaker, self._tone_color_converter, vad=True)
        source_se = torch.load(f'modules/OpenVoice/checkpoints_v2/base_speakers/ses/en-default.pth',
                               map_location=self._device)

        save_path = f'{self._output_dir}/output.mp3'

        src_path = self.melotts2(text, standalone=False)

        # Run the tone color converter
        encode_message = "@MyShell"
        self._tone_color_converter.convert(
            audio_src_path=src_path,
            src_se=source_se,
            tgt_se=target_se,
            output_path=save_path,
            message=encode_message)
        self.play(save_path)
        
    def melotts2(self,text, standalone=True):

        texts = {
            'EN': f"{self._prompt1}",
        }

        for language, text in texts.items():
            model = TTS(language="EN", device=self._device, ckpt_path="modules/MeloTTS/MeloTTS-English/checkpoint.pth", config_path="modules/MeloTTS/MeloTTS-English/config.json")

        src_path = f'{self._output_dir}/tmp.wav'

        # Speed is adjustable
        speed = 1.3
        model.tts_to_file(text, 3, src_path, speed=speed)

        return self.play(src_path) if standalone else src_path

    def play(self, temp_audio_file):

        pygame.mixer.init()
        pygame.mixer.music.load(temp_audio_file)
        pygame.mixer.music.play()

        while pygame.mixer.music.get_busy():
            pygame.time.Clock().tick(10)

        pygame.mixer.music.stop()
        pygame.mixer.quit()
        # os.remove(temp_audio_file)

# Start the conversation in main