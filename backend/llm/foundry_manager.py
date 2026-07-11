"""Bounded, lazy access to Microsoft Foundry Local.

The web application must be useful before the models are warm.  This module
therefore never starts services or downloads models during import/startup.
"""

from __future__ import annotations

import os
import re
import threading
import time
from typing import Iterable

import openai
import requests


class FoundryEngine:
    """Small, resilient wrapper around Foundry Local's OpenAI endpoint."""

    def __init__(
        self,
        reflex_model: str | None = None,
        reason_model: str | None = None,
        base_url: str | None = None,
    ) -> None:
        self.reflex_model_name = reflex_model or os.getenv("ONF_REFLEX_MODEL", "qwen-reflex")
        self.reason_model_name = reason_model or os.getenv("ONF_REASON_MODEL", "deepseek-reason")
        endpoint = (base_url or os.getenv("ONF_FOUNDRY_URL", "http://127.0.0.1:4500")).rstrip("/")
        self.base_url = endpoint if endpoint.endswith("/v1") else f"{endpoint}/v1"
        self.timeout = float(os.getenv("ONF_LLM_TIMEOUT_SECONDS", "90"))
        self._client: openai.OpenAI | None = None
        self._lock = threading.Lock()
        self.last_error: str | None = None
        self.last_latency_ms: int | None = None
        self.active_reflex_model: str | None = None
        self.active_reason_model: str | None = None

    @property
    def client(self) -> openai.OpenAI:
        if self._client is None:
            self._client = openai.OpenAI(
                base_url=self.base_url,
                api_key="foundry-local",
                timeout=self.timeout,
                max_retries=0,
            )
        return self._client

    def health(self, timeout: float = 1.0) -> dict:
        """Return capability state without starting or warming any model."""
        started = time.perf_counter()
        try:
            response = requests.get(f"{self.base_url}/models", timeout=timeout)
            response.raise_for_status()
            payload = response.json()
            models = [model.get("id", "") for model in payload.get("data", [])]
            self.last_error = None
            result = {
                "status": "ready" if models else "standby",
                "endpoint": self.base_url,
                "models": models,
                "latency_ms": round((time.perf_counter() - started) * 1000),
            }
            if not models:
                result["detail"] = "Foundry Local is running, but no chat model is loaded yet."
            return result
        except Exception as exc:  # A stopped local service is a normal degraded state.
            self.last_error = str(exc)
            return {
                "status": "offline",
                "endpoint": self.base_url,
                "models": [],
                "latency_ms": None,
                "detail": "Foundry Local is not responding. Start it to enable live model inference.",
            }

    @staticmethod
    def _content_from_stream(chunks: Iterable) -> str:
        parts: list[str] = []
        for chunk in chunks:
            if not chunk.choices:
                continue
            content = getattr(chunk.choices[0].delta, "content", None)
            if content:
                parts.append(content)
        return "".join(parts).strip()

    def _model_candidates(self, preferred: str, family: str) -> list[str]:
        available = self.health(timeout=1.0).get("models", [])
        if family == "reflex":
            matches = [model for model in available if "qwen2.5-0.5b-instruct" in model.lower()]
        else:
            matches = [model for model in available if "deepseek" in model.lower() and "1.5b" in model.lower()]
        candidates = sorted(matches, key=lambda model: ("cuda" not in model.lower(), model.lower()))
        candidates.append(preferred)
        return list(dict.fromkeys(candidates))

    @staticmethod
    def _strip_reasoning_preamble(content: str) -> str:
        clean = re.sub(r"<think>.*?</think>", "", content, flags=re.DOTALL | re.IGNORECASE).strip()
        if "</think>" in clean.lower():
            clean = re.split(r"</think>", clean, flags=re.IGNORECASE)[-1].strip()
        paragraphs = [paragraph.strip() for paragraph in re.split(r"\n\s*\n", clean) if paragraph.strip()]
        scratchpad_starts = ("okay", "let me", "i need", "we need", "the user", "so,")
        if len(paragraphs) > 1 and paragraphs[0].lower().startswith(scratchpad_starts):
            clean = paragraphs[-1]
        clean = re.sub(r"^(?:final answer|answer|recommendation)\s*:\s*", "", clean, flags=re.IGNORECASE)
        return clean

    def _complete(self, *, models: list[str], messages: list[dict], max_tokens: int, stream: bool = False) -> tuple[str, str | None]:
        started = time.perf_counter()
        for model in models:
            try:
                with self._lock:
                    completion = self.client.chat.completions.create(
                        model=model,
                        messages=messages,
                        temperature=0.15,
                        max_tokens=max_tokens,
                        stream=stream,
                    )
                content = self._content_from_stream(completion) if stream else (completion.choices[0].message.content or "").strip()
                if content:
                    self.last_error = None
                    self.last_latency_ms = round((time.perf_counter() - started) * 1000)
                    return content, model
            except Exception as exc:
                self.last_error = str(exc)
        self.last_latency_ms = round((time.perf_counter() - started) * 1000)
        return "", None

    def fast_reflex(self, prompt: str, system_prompt: str = "You are a helpful assistant.") -> str:
        content, model = self._complete(
            models=self._model_candidates(self.reflex_model_name, "reflex"),
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt},
            ],
            max_tokens=600,
        )
        self.active_reflex_model = model
        return content

    def deep_reason(self, context: str, query: str, system_prompt: str | None = None) -> str:
        analysis, model = self._complete(
            models=self._model_candidates(self.reason_model_name, "reason"),
            messages=[
                {
                    "role": "system",
                    "content": (
                        "Analyze the supplied meeting evidence and trade-offs. Treat unknown facts as unknown, do not invent "
                        "policy, and produce compact internal analysis notes for a separate final-answer editor."
                    ),
                },
                {"role": "user", "content": f"Context:\n{context}\n\nRequest:\n{query}"},
            ],
            max_tokens=280,
            stream=False,
        )
        self.active_reason_model = model
        synthesis_prompt = (
            f"Evidence and meeting context:\n{context}\n\n"
            f"Question:\n{query}\n\n"
            f"Draft analysis notes from the reasoning engine:\n{analysis or 'No draft was available.'}\n\n"
            "Return only the final answer. Use only supported evidence, preserve uncertainty, and stay under 160 words."
        )
        final, reflex_model = self._complete(
            models=self._model_candidates(self.reflex_model_name, "reflex"),
            messages=[
                {
                    "role": "system",
                    "content": system_prompt
                    or "You are a concise meeting facilitator who grounds every recommendation in supplied local evidence.",
                },
                {"role": "user", "content": synthesis_prompt},
            ],
            max_tokens=240,
            stream=False,
        )
        self.active_reflex_model = reflex_model
        return final or self._strip_reasoning_preamble(analysis)