"""Speech-to-text via faster-whisper (optional / lazily loaded).

Importing this module never pulls in torch or faster-whisper. The heavy model is
only loaded when transcription is actually enabled and the dependency is present,
so a minimal install still boots cleanly.
"""

from __future__ import annotations

import os
from typing import Optional


class TranscriptionService:
    def __init__(self, model_size: str = "small", device: str = "auto", enabled: bool = True):
        self.model_size = model_size
        self.enabled = enabled
        self.available = False
        self.model = None
        self.device = "cpu"
        self.compute_type = "int8"

        if self.enabled:
            self._lazy_init(device)
        else:
            print("[TranscriptionService] Disabled by configuration.")

    def _lazy_init(self, device: str) -> None:
        try:
            from faster_whisper import WhisperModel

            use_cuda = False
            if device in ("auto", "cuda"):
                try:
                    import torch

                    use_cuda = torch.cuda.is_available()
                except Exception:
                    use_cuda = False

            self.device = "cuda" if use_cuda else "cpu"
            self.compute_type = "float16" if self.device == "cuda" else "int8"
            print(f"[TranscriptionService] Loading Whisper ({self.model_size}) on {self.device}...")
            try:
                self.model = WhisperModel(self.model_size, device=self.device, compute_type=self.compute_type)
            except Exception as exc:
                print(f"[TranscriptionService] {self.device} load failed ({exc}); using CPU/int8.")
                self.device, self.compute_type = "cpu", "int8"
                self.model = WhisperModel(self.model_size, device="cpu", compute_type="int8")
            self.available = True
        except Exception as exc:
            print(f"[TranscriptionService] Unavailable ({exc}). Transcription disabled.")
            self.available = False

    def transcribe(self, audio_file_path: str, beam_size: int = 1, vad_filter: bool = True,
                   initial_prompt: Optional[str] = None) -> str:
        if not self.available or not self.model:
            return ""
        if not os.path.exists(audio_file_path):
            return ""
        segments, _info = self.model.transcribe(
            audio_file_path,
            beam_size=beam_size,
            vad_filter=vad_filter,
            initial_prompt=initial_prompt,
            condition_on_previous_text=False,
        )
        return "".join(segment.text for segment in segments).strip()
