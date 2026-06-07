"""Speaker diarization service.

Heavy dependencies (`torch`, `pyannote.audio`) are imported lazily. Until a real
pyannote pipeline is configured (it needs a Hugging Face token / local model),
this returns a deterministic two-speaker mock so the streaming pipeline keeps
flowing without crashing a minimal install.
"""

from __future__ import annotations

from typing import List, Dict


class DiarizationService:
    def __init__(self, enabled: bool = True):
        self.enabled = enabled
        self.pipeline = None  # real pyannote pipeline would be assigned here
        print("[DiarizationService] Ready (mock segments until pyannote is configured).")

    def diarize(self, audio_path: str) -> List[Dict]:
        if not self.enabled:
            return []
        if not self.pipeline:
            # Placeholder segmentation keeps the UI timeline populated.
            return [
                {"start": 0.0, "end": 2.5, "speaker": "Speaker A"},
                {"start": 2.5, "end": 5.0, "speaker": "Speaker B"},
            ]
        # Real implementation (requires configured pipeline):
        # diarization = self.pipeline(audio_path)
        # return [
        #     {"start": turn.start, "end": turn.end, "speaker": label}
        #     for turn, _, label in diarization.itertracks(yield_label=True)
        # ]
        return []
