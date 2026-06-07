"""Text-to-speech service (optional / lazily loaded).

The original implementation imported MeloTTS + OpenVoice at module import time
and depended on a `modules/OpenVoice` + `modules/MeloTTS` checkpoint tree that is
not shipped with the repo. A single missing import there took the *entire*
backend down at startup.

This version:
- Imports nothing heavy at module load, so importing it is always safe.
- Treats backend TTS as **optional**. It only activates when explicitly enabled
  (``ONF_ENABLE_TTS=true``) *and* the dependencies + checkpoints are present.
- When unavailable, callers get ``None`` and the frontend falls back to the
  browser's offline Web Speech API. The showcase keeps working either way.
"""

from __future__ import annotations

import os
import time
from typing import Optional


class TtsService:
    def __init__(self, device: Optional[str] = None, output_dir: str = "outputs_v2", enabled: bool = False):
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)

        self.enabled = enabled
        self.available = False
        self.device = device or "cpu"
        self.tone_color_converter = None
        self.melo_model = None
        self.melo_speaker_ids = {}

        if self.enabled:
            self._lazy_init()
        else:
            print("[TtsService] Backend TTS disabled (frontend Web Speech fallback in use).")

    def _lazy_init(self) -> None:
        """Best-effort init of MeloTTS + OpenVoice. Never raises."""
        try:
            import torch  # noqa: F401
            from openvoice.api import ToneColorConverter
            from melo.api import TTS

            converter_dir = os.environ.get(
                "ONF_OPENVOICE_CONVERTER", "modules/OpenVoice/checkpoints_v2/converter"
            )
            config_path = f"{converter_dir}/config.json"
            ckpt_path = f"{converter_dir}/checkpoint.pth"
            if not (os.path.exists(config_path) and os.path.exists(ckpt_path)):
                print(
                    "[TtsService] OpenVoice checkpoints not found; backend TTS stays disabled."
                )
                return

            self.tone_color_converter = ToneColorConverter(config_path, device=self.device)
            self.tone_color_converter.load_ckpt(ckpt_path)

            self.melo_model = TTS(language="EN", device=self.device)
            self.melo_speaker_ids = self.melo_model.hps.data.spk2id
            self.available = True
            print("[TtsService] MeloTTS + OpenVoice initialized.")
        except Exception as exc:
            print(f"[TtsService] Backend TTS unavailable ({exc}). Using frontend fallback.")
            self.available = False

    def generate_speech(self, text: str, speed: float = 1.0, speaker_key: str = "EN-Default") -> Optional[str]:
        if not self.available or not self.melo_model or not (text and text.strip()):
            return None
        save_path = os.path.join(self.output_dir, f"tts_{int(time.time())}.wav")
        try:
            speaker_id = self.melo_speaker_ids.get(
                speaker_key, next(iter(self.melo_speaker_ids.values()), 0)
            )
            self.melo_model.tts_to_file(text, speaker_id, save_path, speed=speed)
            return save_path
        except Exception as exc:
            print(f"[TtsService] Error generating speech: {exc}")
            return None

    async def generate_and_play_speech(self, text: str) -> Optional[str]:
        # Playback is a frontend concern; backend only renders the file when able.
        return self.generate_speech(text)
