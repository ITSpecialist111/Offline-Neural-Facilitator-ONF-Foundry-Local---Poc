"""Lazy, English-only local speech synthesis with MeloTTS."""

from __future__ import annotations

import os
import sys
import threading
import time
import types
from pathlib import Path

from backend.runtime_paths import data_path, resource_path


class TtsService:
    def __init__(self, output_dir: str | None = None) -> None:
        self.output_dir = str(output_dir or data_path("outputs_v2"))
        os.makedirs(self.output_dir, exist_ok=True)
        self._model = None
        self._speaker_ids: dict = {}
        self._lock = threading.Lock()
        self.loading = False
        self.last_error: str | None = None

    @property
    def loaded(self) -> bool:
        return self._model is not None

    def status(self) -> dict:
        model_dir = self._model_dir()
        checkpoints_present = all(
            os.path.exists(path)
            for path in (
                model_dir / "checkpoint.pth",
                model_dir / "config.json",
            )
        )
        return {
            "status": "ready" if self.loaded else ("loading" if self.loading else "standby"),
            "checkpoints_present": checkpoints_present,
            "detail": self.last_error,
        }

    def _load(self):
        if self._model is not None:
            return self._model

        with self._lock:
            if self._model is not None:
                return self._model
            self.loading = True
            try:
                import torch

                if os.getenv("ONF_ALLOW_MODEL_DOWNLOADS", "0") != "1":
                    os.environ["HF_HUB_OFFLINE"] = "1"
                    os.environ["TRANSFORMERS_OFFLINE"] = "1"

                # Melo imports every supported language eagerly even though ONF
                # uses English only. Stub unused languages and resolve the
                # English Transformer assets to cached absolute paths so no
                # runtime metadata request can reach Hugging Face.
                import importlib
                from huggingface_hub import snapshot_download
                from transformers import AutoModelForMaskedLM, AutoTokenizer

                def local_asset(model_id: str) -> str:
                    if os.path.exists(model_id):
                        return model_id
                    return snapshot_download(model_id, local_files_only=True)

                original_tokenizer_loader = AutoTokenizer.from_pretrained
                original_model_loader = AutoModelForMaskedLM.from_pretrained

                def local_tokenizer_loader(model_id, *args, **kwargs):
                    kwargs["local_files_only"] = True
                    return original_tokenizer_loader(local_asset(model_id), *args, **kwargs)

                def local_model_loader(model_id, *args, **kwargs):
                    kwargs["local_files_only"] = True
                    return original_model_loader(local_asset(model_id), *args, **kwargs)

                AutoTokenizer.from_pretrained = staticmethod(local_tokenizer_loader)
                AutoModelForMaskedLM.from_pretrained = staticmethod(local_model_loader)

                text_package = importlib.import_module("melo.text")

                def unsupported_language(*_args, **_kwargs):
                    raise RuntimeError("This ONF speech build supports English only.")

                def distribute_phone(phone_count, word_count):
                    distribution = [0] * word_count
                    for _ in range(phone_count):
                        index = distribution.index(min(distribution))
                        distribution[index] += 1
                    return distribution

                for leaf in (
                    "chinese", "japanese", "chinese_mix", "korean", "french", "spanish",
                    "chinese_bert", "japanese_bert", "spanish_bert", "french_bert",
                ):
                    module_name = f"melo.text.{leaf}"
                    stub = types.ModuleType(module_name)
                    stub.text_normalize = unsupported_language
                    stub.g2p = unsupported_language
                    stub.get_bert_feature = unsupported_language
                    if leaf == "japanese":
                        stub.distribute_phone = distribute_phone
                    sys.modules[module_name] = stub
                    setattr(text_package, leaf, stub)

                from melo.api import TTS

                device = "cuda:0" if torch.cuda.is_available() else "cpu"
                self._model = TTS(
                    language="EN",
                    device=device,
                    ckpt_path=str(self._model_dir() / "checkpoint.pth"),
                    config_path=str(self._model_dir() / "config.json"),
                )
                speaker_ids = self._model.hps.data.spk2id
                self._speaker_ids = dict(speaker_ids.items()) if hasattr(speaker_ids, "items") else dict(speaker_ids)
                self.last_error = None
            except Exception as exc:
                self.last_error = str(exc)
                raise RuntimeError(f"Unable to load local speech model: {exc}") from exc
            finally:
                self.loading = False
        return self._model

    @staticmethod
    def _model_dir() -> Path:
        configured = os.getenv("ONF_MELO_MODEL_DIR")
        return Path(configured) if configured else resource_path("audio_models", "MeloTTS-English")

    def generate_speech(self, text: str, voice_id: str = "EN-BR") -> str | None:
        if not text or not text.strip():
            return None

        model = self._load()
        filename = f"facilitator_{int(time.time() * 1000)}.wav"
        output_path = os.path.join(self.output_dir, filename)
        speaker_id = self._speaker_ids.get(voice_id, self._speaker_ids.get("EN-Default", 0))
        model.tts_to_file(text.strip(), speaker_id, output_path, speed=1.0)
        return output_path

    async def generate_and_play_speech(self, text: str) -> str | None:
        # Browser playback is deliberate; the server must never seize host audio.
        return self.generate_speech(text)