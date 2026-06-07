"""
Central configuration for the Offline Neural Facilitator (ONF) backend.

Design goals:
- **Offline-first**: every default keeps the app fully on-device. Nothing reaches
  the network unless the operator explicitly opts in.
- **Hybrid-online (opt-in)**: when a more powerful cloud model is available and the
  operator enables it, the engine can route reasoning to an OpenAI-compatible
  endpoint (OpenAI, Azure OpenAI, OpenRouter, ...).
- **Fault tolerance**: heavy/optional components can be toggled off so a missing
  dependency never takes the whole backend down.

All settings are environment driven and read from the process environment plus an
optional `.env` file in the repository root (parsed with a tiny dependency-free
reader so we don't require `python-dotenv`).
"""

from __future__ import annotations

import os
from functools import lru_cache


def _load_dotenv() -> None:
    """Load KEY=VALUE pairs from a `.env` file without external dependencies.

    Existing environment variables always win, so values exported in the shell
    override the file. Lines that are blank or start with `#` are ignored.
    """
    # Look for a .env next to the repo root (two levels up from this file).
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    env_path = os.path.join(root, ".env")
    if not os.path.exists(env_path):
        return
    try:
        with open(env_path, "r", encoding="utf-8") as fh:
            for raw in fh:
                line = raw.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                key, _, value = line.partition("=")
                key = key.strip()
                value = value.strip().strip('"').strip("'")
                if key and key not in os.environ:
                    os.environ[key] = value
    except Exception as exc:  # pragma: no cover - defensive, never fatal
        print(f"[config] Warning: could not read .env: {exc}")


def _as_bool(value: str | None, default: bool = False) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on", "y"}


class Settings:
    """Resolved runtime settings. Construct once via :func:`get_settings`."""

    def __init__(self) -> None:
        _load_dotenv()
        env = os.environ.get

        # --- Server -------------------------------------------------------
        self.host: str = env("ONF_HOST", "127.0.0.1")
        self.port: int = int(env("ONF_PORT", "8000"))
        # Public base URL used when handing audio file links back to the UI.
        self.public_base_url: str = env(
            "ONF_PUBLIC_BASE_URL", f"http://localhost:{self.port}"
        )
        # CORS origins (comma separated). Default to the Vite dev server only;
        # "*" is accepted for convenience but discouraged for real deployments.
        self.cors_origins: list[str] = [
            o.strip()
            for o in env(
                "ONF_CORS_ORIGINS",
                "http://localhost:5173,http://127.0.0.1:5173",
            ).split(",")
            if o.strip()
        ]

        # --- Foundry Local (offline engine) -------------------------------
        # Model aliases. Defaults track the current Foundry Local catalog.
        self.reflex_model: str = env("ONF_REFLEX_MODEL", "qwen2.5-0.5b")
        self.reason_model: str = env("ONF_REASON_MODEL", "qwen2.5-1.5b")
        # Optional explicit endpoint override. When unset the Foundry Local SDK
        # resolves a dynamic endpoint automatically; this is only a fallback for
        # when the SDK is unavailable or the operator runs a manual server.
        self.foundry_endpoint: str | None = env("ONF_FOUNDRY_ENDPOINT") or None
        self.foundry_api_key: str = env("ONF_FOUNDRY_API_KEY", "not-needed")
        # Allow the SDK to auto-start the Foundry service / download models.
        self.foundry_bootstrap: bool = _as_bool(env("ONF_FOUNDRY_BOOTSTRAP"), True)

        # --- Hybrid online engine (opt-in, privacy sensitive) -------------
        # When disabled (default) nothing ever leaves the device.
        self.online_enabled: bool = _as_bool(env("ONF_ONLINE_ENABLED"), False)
        self.online_base_url: str | None = env("ONF_ONLINE_BASE_URL") or None
        self.online_api_key: str | None = env("ONF_ONLINE_API_KEY") or None
        self.online_model: str = env("ONF_ONLINE_MODEL", "gpt-4o-mini")
        # When should the online model be used? "reason" routes only Deep Think
        # requests online; "all" routes every request online; "off" never does.
        self.online_route: str = env("ONF_ONLINE_ROUTE", "reason").strip().lower()

        # --- Optional heavy components ------------------------------------
        # Toggle individual subsystems off to guarantee a clean boot on minimal
        # installs. Each is also auto-disabled if its dependency is missing.
        self.enable_whisper: bool = _as_bool(env("ONF_ENABLE_WHISPER"), True)
        self.enable_tts: bool = _as_bool(env("ONF_ENABLE_TTS"), False)
        self.enable_diarization: bool = _as_bool(env("ONF_ENABLE_DIARIZATION"), True)
        self.enable_vision: bool = _as_bool(env("ONF_ENABLE_VISION"), True)
        self.enable_proactive_loop: bool = _as_bool(
            env("ONF_ENABLE_PROACTIVE_LOOP"), True
        )

        # --- Model / data sizing -----------------------------------------
        self.whisper_model_size: str = env("ONF_WHISPER_MODEL", "small")
        self.output_dir: str = env("ONF_OUTPUT_DIR", "outputs_v2")
        self.sessions_dir: str = env("ONF_SESSIONS_DIR", "sessions")
        self.chroma_dir: str = env("ONF_CHROMA_DIR", "./chroma_db")

    # Convenience -----------------------------------------------------------
    @property
    def online_ready(self) -> bool:
        """True when hybrid-online is enabled *and* fully configured."""
        return bool(
            self.online_enabled
            and self.online_base_url
            and self.online_api_key
            and self.online_route != "off"
        )

    def summary(self) -> dict:
        """A non-secret view of the configuration for /health and logs."""
        return {
            "reflex_model": self.reflex_model,
            "reason_model": self.reason_model,
            "foundry_endpoint": self.foundry_endpoint or "auto (SDK)",
            "online_enabled": self.online_enabled,
            "online_ready": self.online_ready,
            "online_route": self.online_route,
            "online_model": self.online_model if self.online_enabled else None,
            "enable_whisper": self.enable_whisper,
            "enable_tts": self.enable_tts,
            "enable_diarization": self.enable_diarization,
            "enable_vision": self.enable_vision,
        }


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
