import os
import time
import torch
import pygame
from openvoice import se_extractor
from openvoice.api import ToneColorConverter
from melo.api import TTS

class TtsService:
    def __init__(self, device="cuda" if torch.cuda.is_available() else "cpu", output_dir="outputs_v2"):
        self.device = device
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)
        
        self.ckpt_converter = 'modules/OpenVoice/checkpoints_v2/converter'
        self.tone_color_converter = ToneColorConverter(f'{self.ckpt_converter}/config.json', device=self.device)
        self.tone_color_converter.load_ckpt(f'{self.ckpt_converter}/checkpoint.pth')
        
        self.melo_model = None
        self.melo_speaker_ids = {}
        self._initialize_melo()

    def _initialize_melo(self):
        print(f"Initializing MeloTTS on {self.device}...")
        try:
             self.melo_model = TTS(language="EN", device=self.device, 
                                 ckpt_path="modules/MeloTTS/MeloTTS-English/checkpoint.pth", 
                                 config_path="modules/MeloTTS/MeloTTS-English/config.json")
             self.melo_speaker_ids = self.melo_model.hps.data.spk2id
        except Exception as e:
            print(f"Warning: MeloTTS Initialization failed: {e}")

    def generate_speech(self, text, speed=1.0, speaker_key='EN-BR'):
        """
        Unified method to generate speech using MeloTTS + OpenVoice.
        """
        if not self.melo_model or not text.strip():
            print("Error: MeloTTS not initialized or empty text.")
            return None

        # Standard output path for compatibility with existing tests/frontend
        save_path = os.path.join(self.output_dir, "output.mp3") 
        # Temp path for intermediate MeloTTS output
        src_path = os.path.join(self.output_dir, "tmp.wav")
        
        try:
            speaker_id = self.melo_speaker_ids.get(speaker_key, self.melo_speaker_ids.get('EN-Default', 0))
            self.melo_model.tts_to_file(text, speaker_id, src_path, speed=speed)
            
            # 2. Apply OpenVoice Tone Conversion
            reference_speaker = 'modules/OpenVoice/resources/example_reference.mp3'
            target_se, _ = se_extractor.get_se(reference_speaker, self.tone_color_converter, vad=True)
            source_se = torch.load(f'modules/OpenVoice/checkpoints_v2/base_speakers/ses/en-default.pth', map_location=self.device)
            
            self.tone_color_converter.convert(
                audio_src_path=src_path,
                src_se=source_se,
                tgt_se=target_se,
                output_path=save_path,
                message="@MyShell")
            
            # Cleanup temp file
            if os.path.exists(src_path):
                os.remove(src_path)
                
            return save_path
        except Exception as e:
            print(f"Error generating speech: {e}")
            return None

    def play_audio(self, audio_path):
        if not audio_path or not os.path.exists(audio_path):
            return
            
        pygame.mixer.init()
        pygame.mixer.music.load(audio_path)
        pygame.mixer.music.play()

        while pygame.mixer.music.get_busy():
            pygame.time.Clock().tick(10)

        pygame.mixer.music.stop()
        pygame.mixer.quit()

    async def generate_and_play_speech(self, text):
        """Helper for background tasks or sync CLI."""
        path = self.generate_speech(text)
        if path:
            self.play_audio(path)
        return path
