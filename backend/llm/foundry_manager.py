"""Resilient inference engine for ONF.

Wraps **Microsoft Foundry Local** (offline, on-device) and an optional
**hybrid-online** OpenAI-compatible provider behind one small interface used by
the rest of the app:

    engine.fast_reflex(prompt, system_prompt)   -> str | None      (low latency)
    engine.deep_reason(context, query)          -> stream | None   (chat.completions stream)

Key reliability properties:
- Construction never raises. If Foundry Local (or its SDK) is unavailable the
  engine stays usable in a degraded state and reports `available = False`.
- The Foundry endpoint is resolved dynamically through the SDK when possible
  (the fixed `localhost:4500` of older builds is no longer assumed) and falls
  back to a configurable endpoint.
- Hybrid online is strictly opt-in via configuration; when off, nothing leaves
  the device.
"""

from __future__ import annotations

from typing import Optional

from backend.config import get_settings


class FoundryEngine:
    def __init__(self, reflex_model: Optional[str] = None, reason_model: Optional[str] = None):
        self.settings = get_settings()
        self.reflex_model_name = reflex_model or self.settings.reflex_model
        self.reason_model_name = reason_model or self.settings.reason_model

        # Offline (Foundry Local) state
        self.manager = None
        self.client = None
        self.base_url: Optional[str] = None
        self.available = False
        # Resolved model ids (Foundry may expand an alias to a hardware variant)
        self._reflex_id = self.reflex_model_name
        self._reason_id = self.reason_model_name

        # Online (hybrid) state
        self.online_client = None
        self.online_available = False

        self._init_foundry()
        self._init_online()

    # ------------------------------------------------------------------
    # Initialization
    # ------------------------------------------------------------------
    def _init_foundry(self) -> None:
        try:
            import openai  # local import keeps module import-safe
        except Exception as exc:  # pragma: no cover - openai is a core dep
            print(f"[FoundryEngine] openai SDK unavailable: {exc}")
            return

        base_url = self.settings.foundry_endpoint
        api_key = self.settings.foundry_api_key

        # Preferred path: let the Foundry Local SDK resolve a dynamic endpoint
        # and (optionally) bootstrap the service + model download.
        try:
            from foundry_local import FoundryLocalManager  # type: ignore

            if self.settings.foundry_bootstrap:
                # Passing an alias asks the SDK to start the service and ensure
                # the model is available. Wrapped so a failure is non-fatal.
                self.manager = FoundryLocalManager(self.reflex_model_name)
            else:
                self.manager = FoundryLocalManager()

            endpoint = getattr(self.manager, "endpoint", None) or getattr(
                self.manager, "service_uri", None
            )
            if endpoint:
                base_url = (
                    endpoint
                    if endpoint.rstrip("/").endswith("/v1")
                    else f"{endpoint.rstrip('/')}/v1"
                )
            key = getattr(self.manager, "api_key", None)
            if key:
                api_key = key

            # Resolve alias -> concrete model id when the SDK exposes it.
            self._reflex_id = self._resolve_model_id(self.reflex_model_name)
            self._reason_id = self._resolve_model_id(self.reason_model_name)
        except Exception as exc:
            print(
                f"[FoundryEngine] Foundry Local SDK not used ({exc}). "
                "Falling back to direct endpoint."
            )

        # Fall back to a sensible default endpoint when nothing else resolved.
        if not base_url:
            base_url = "http://localhost:5273/v1"
        self.base_url = base_url

        try:
            self.client = openai.OpenAI(base_url=self.base_url, api_key=api_key or "not-needed")
        except Exception as exc:  # pragma: no cover - defensive
            print(f"[FoundryEngine] Could not create offline client: {exc}")
            return

        # Probe the endpoint, but never block startup for long.
        self.available = self._probe()
        if self.available:
            print(f"[FoundryEngine] Connected to Foundry Local at {self.base_url}")
        else:
            print(
                f"[FoundryEngine] Foundry Local not reachable at {self.base_url}. "
                "Reflex/Reason will report unavailable until the service is up."
            )

    def _resolve_model_id(self, alias: str) -> str:
        try:
            if self.manager and hasattr(self.manager, "get_model_info"):
                info = self.manager.get_model_info(alias)
                return getattr(info, "id", None) or alias
        except Exception:
            pass
        return alias

    def _init_online(self) -> None:
        if not self.settings.online_ready:
            return
        try:
            import openai

            self.online_client = openai.OpenAI(
                base_url=self.settings.online_base_url,
                api_key=self.settings.online_api_key,
            )
            self.online_available = True
            print(
                f"[FoundryEngine] Hybrid online enabled -> {self.settings.online_model} "
                f"(route: {self.settings.online_route})"
            )
        except Exception as exc:
            print(f"[FoundryEngine] Online provider init failed: {exc}")
            self.online_available = False

    def _probe(self) -> bool:
        try:
            self.client.models.list()
            return True
        except Exception:
            return False

    # ------------------------------------------------------------------
    # Routing helpers
    # ------------------------------------------------------------------
    def _use_online_for(self, task: str) -> bool:
        """Decide whether `task` ('reflex' | 'reason') should go online."""
        if not self.online_available:
            return False
        route = self.settings.online_route
        if route == "all":
            return True
        if route == "reason" and task == "reason":
            return True
        return False

    def status(self) -> dict:
        return {
            "offline_available": self.available,
            "endpoint": self.base_url,
            "reflex_model": self._reflex_id,
            "reason_model": self._reason_id,
            "online_available": self.online_available,
            "online_model": self.settings.online_model if self.online_available else None,
            "online_route": self.settings.online_route if self.online_available else None,
        }

    def ensure_available(self) -> bool:
        """Re-probe lazily so a service started after the backend still works."""
        if self.available:
            return True
        if self.client is None:
            return False
        self.available = self._probe()
        return self.available

    # ------------------------------------------------------------------
    # Inference
    # ------------------------------------------------------------------
    def fast_reflex(self, prompt: str, system_prompt: str = "You are a helpful assistant.") -> Optional[str]:
        """Low-latency completion. Uses the small Foundry model (or online if routed)."""
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt},
        ]

        if self._use_online_for("reflex"):
            try:
                resp = self.online_client.chat.completions.create(
                    model=self.settings.online_model,
                    messages=messages,
                    temperature=0.1,
                    max_tokens=500,
                )
                return resp.choices[0].message.content
            except Exception as exc:
                print(f"[FoundryEngine] Online reflex failed ({exc}); trying offline.")

        if not self.ensure_available():
            return None
        try:
            response = self.client.chat.completions.create(
                model=self._reflex_id,
                messages=messages,
                temperature=0.1,
                max_tokens=500,
            )
            return response.choices[0].message.content
        except Exception as exc:
            print(f"[FoundryEngine] Reflex error: {exc}")
            return None

    def deep_reason(self, context: str, query: str):
        """Streaming completion for complex reasoning. Returns a stream or None.

        Routes to the online model when configured, otherwise the larger Foundry
        model. The caller iterates the returned stream of chat completion chunks.
        """
        messages = [
            {
                "role": "system",
                "content": "You are a deep thinking compliance auditor and facilitator. Analyze the context carefully.",
            },
            {"role": "user", "content": f"Context:\n{context}\n\nQuery: {query}"},
        ]

        if self._use_online_for("reason"):
            try:
                return self.online_client.chat.completions.create(
                    model=self.settings.online_model,
                    messages=messages,
                    stream=True,
                )
            except Exception as exc:
                print(f"[FoundryEngine] Online reason failed ({exc}); trying offline.")

        if not self.ensure_available():
            return None
        try:
            return self.client.chat.completions.create(
                model=self._reason_id,
                messages=messages,
                stream=True,
            )
        except Exception as exc:
            print(f"[FoundryEngine] Reasoning error: {exc}")
            return None
