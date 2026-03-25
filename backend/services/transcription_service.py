import os
import torch
from faster_whisper import WhisperModel

class TranscriptionService:
    def __init__(self, model_size="medium", device="cuda", compute_type="float16"):
        self.model_size = model_size
        self.device = device if torch.cuda.is_available() and device == "cuda" else "cpu"
        self.compute_type = compute_type if self.device == "cuda" else "int8"
        
        print(f"Initializing Whisper ({self.model_size}) on {self.device}...")
        try:
            self.model = WhisperModel(self.model_size, device=self.device, compute_type=self.compute_type)
        except Exception as e:
            print(f"Warning: Whisper initialization failed on {self.device} ({e}). Falling back to CPU/int8.")
            self.model = WhisperModel(self.model_size, device="cpu", compute_type="int8")

    def transcribe(self, audio_file_path, beam_size=1, vad_filter=True, initial_prompt=None):
        """
        Transcribes audio file to text.
        Optimized for latency: beam_size=1 (greedy) is much faster.
        initial_prompt helps maintain context/proper nouns.
        """
        if not os.path.exists(audio_file_path):
            return ""
            
        segments, info = self.model.transcribe(
            audio_file_path, 
            beam_size=beam_size, 
            vad_filter=vad_filter,
            initial_prompt=initial_prompt,
            condition_on_previous_text=False
        )
        
        full_text = ""
        for segment in segments:
            full_text += segment.text + " "
            
        return full_text.strip()
