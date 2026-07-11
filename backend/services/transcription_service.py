"""Lazy local speech-to-text capability."""

from __future__ import annotations

import os
import threading
import logging


class TranscriptionService:
    def __init__(self, model_size: str | None = None) -> None:
        self.model_size = model_size or os.getenv("ONF_WHISPER_MODEL", "medium")
        self._model = None
        self._lock = threading.Lock()
        self.loading = False
        self.last_error: str | None = None
        self.device: str | None = None

    @property
    def loaded(self) -> bool:
        return self._model is not None

    def status(self) -> dict:
        return {
            "status": "ready" if self.loaded else ("loading" if self.loading else "standby"),
            "model": self.model_size,
            "device": self.device,
            "detail": self.last_error,
        }

    def _load(self, force_cpu: bool = False):
        if self._model is not None:
            return self._model

        with self._lock:
            if self._model is not None:
                return self._model

            self.loading = True
            try:
                import ctranslate2
                from faster_whisper import WhisperModel

                configured_device = os.getenv("ONF_WHISPER_DEVICE", "auto").lower()
                if force_cpu:
                    device = "cpu"
                elif configured_device in {"cpu", "cuda"}:
                    device = configured_device
                else:
                    device = "cuda" if ctranslate2.get_cuda_device_count() > 0 else "cpu"
                compute_type = "float16" if device == "cuda" else "int8"
                allow_downloads = os.getenv("ONF_ALLOW_MODEL_DOWNLOADS", "0") == "1"
                self._model = WhisperModel(
                    self.model_size,
                    device=device,
                    compute_type=compute_type,
                    local_files_only=not allow_downloads,
                )
                self.device = device
                self.last_error = None
            except Exception as exc:
                self.last_error = str(exc)
                raise RuntimeError(f"Unable to load local Whisper model: {exc}") from exc
            finally:
                self.loading = False

        return self._model

    def transcribe(self, audio_file_path: str, initial_prompt: str | None = None) -> str:
        if not os.path.exists(audio_file_path):
            return ""

        def run(model) -> str:
            segments, _ = model.transcribe(
                audio_file_path,
                beam_size=1,
                vad_filter=True,
                initial_prompt=initial_prompt,
                condition_on_previous_text=False,
            )
            return " ".join(segment.text.strip() for segment in segments if segment.text.strip()).strip()

        model = self._load()
        try:
            return run(model)
        except Exception as exc:
            if self.device != "cuda":
                raise
            logging.warning("Whisper CUDA inference failed; retrying on CPU: %s", exc)
            with self._lock:
                self._model = None
                self.device = None
            return run(self._load(force_cpu=True))