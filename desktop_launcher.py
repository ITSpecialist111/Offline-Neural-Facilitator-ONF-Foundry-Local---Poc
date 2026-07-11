"""Portable Windows host for Offline Neural Facilitator.

The frozen application runs one internal FastAPI/React process, opens the
system browser for reliable microphone support, and exposes reopen/exit actions
through a notification-area icon. Foundry Local remains an optional external
runtime and is started invisibly when its supported CLI is available.
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import shutil
import socket
import subprocess
import sys
import threading
import time
import urllib.request
import webbrowser
from pathlib import Path

APP_NAME = "Offline Neural Facilitator"
DEFAULT_PORT = 8765
FOUNDRY_MODELS = ("qwen2.5-0.5b", "deepseek-r1-1.5b")


def frozen() -> bool:
    return bool(getattr(sys, "frozen", False))


def application_root() -> Path:
    return Path(sys.executable if frozen() else __file__).resolve().parent


def message_box(message: str, title: str = APP_NAME, error: bool = False) -> None:
    try:
        import ctypes

        ctypes.windll.user32.MessageBoxW(None, message, title, 0x10 if error else 0x40)
    except Exception:
        print(f"{title}: {message}", file=sys.stderr)


def writable_data_directory(configured: str | None) -> Path:
    candidates = []
    if configured:
        candidates.append(Path(configured).expanduser())
    candidates.append(application_root() / "data")
    local_app_data = os.getenv("LOCALAPPDATA")
    if local_app_data:
        candidates.append(Path(local_app_data) / "OfflineNeuralFacilitator")

    for candidate in candidates:
        try:
            candidate.mkdir(parents=True, exist_ok=True)
            probe = candidate / ".write-test"
            probe.write_text("portable", encoding="utf-8")
            probe.unlink()
            return candidate.resolve()
        except OSError:
            continue
    raise RuntimeError("No writable ONF data directory is available.")


def configure_logging(data_dir: Path) -> Path:
    log_dir = data_dir / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    log_path = log_dir / "onf-desktop.log"
    logging.basicConfig(
        filename=log_path,
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
        encoding="utf-8",
        force=True,
    )
    return log_path


def hidden_process_options() -> dict:
    if os.name != "nt":
        return {}
    startup = subprocess.STARTUPINFO()
    startup.dwFlags |= subprocess.STARTF_USESHOWWINDOW
    return {
        "creationflags": subprocess.CREATE_NO_WINDOW,
        "startupinfo": startup,
    }


def start_foundry_local() -> None:
    foundry = shutil.which("foundry")
    if not foundry:
        logging.warning("Foundry Local CLI is not installed; deterministic ONF remains available.")
        return

    options = hidden_process_options()
    try:
        result = subprocess.run(
            [foundry, "service", "start"],
            capture_output=True,
            text=True,
            timeout=45,
            check=False,
            **options,
        )
        if result.returncode:
            logging.warning("Foundry service start returned %s: %s", result.returncode, result.stderr.strip())
        else:
            logging.info("Foundry Local service is available.")
    except Exception:
        logging.exception("Unable to start Foundry Local service")
        return

    for model in FOUNDRY_MODELS:
        try:
            subprocess.Popen(
                [foundry, "model", "load", model, "--device", "GPU", "--ttl", "3600"],
                stdin=subprocess.DEVNULL,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                **options,
            )
        except Exception:
            logging.exception("Unable to request Foundry model load: %s", model)


def status_payload(url: str, timeout: float = 1.0) -> dict | None:
    try:
        with urllib.request.urlopen(f"{url}/api/status", timeout=timeout) as response:
            return json.loads(response.read().decode("utf-8"))
    except Exception:
        return None


def port_is_open(port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client:
        client.settimeout(0.25)
        return client.connect_ex(("127.0.0.1", port)) == 0


def wait_until_ready(url: str, server_thread: threading.Thread, timeout: float = 90.0) -> None:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        payload = status_payload(url)
        if payload and payload.get("status") == "ready":
            return
        if not server_thread.is_alive():
            raise RuntimeError("The local ONF service stopped during startup. See the portable log for details.")
        time.sleep(0.25)
    raise RuntimeError("ONF did not become ready within 90 seconds. See the portable log for details.")


def tray_image():
    from PIL import Image, ImageDraw, ImageFont

    image = Image.new("RGBA", (64, 64), "#0f172a")
    draw = ImageDraw.Draw(image)
    draw.rounded_rectangle((3, 3, 61, 61), radius=14, fill="#2563eb", outline="#93c5fd", width=2)
    font = ImageFont.load_default(size=18)
    draw.text((32, 32), "ONF", fill="white", font=font, anchor="mm")
    return image


def run_desktop(args: argparse.Namespace) -> int:
    data_dir = writable_data_directory(args.data_dir)
    os.environ["ONF_DATA_DIR"] = str(data_dir)
    os.environ["ONF_SERVE_FRONTEND"] = "1"
    os.environ.setdefault("ONF_ALLOW_MODEL_DOWNLOADS", "0")
    # The compact portable bundle intentionally omits multi-hundred-megabyte
    # NVIDIA CUDA runtime DLLs. Users can override this when those DLLs are
    # available globally; TranscriptionService still falls back safely.
    os.environ.setdefault("ONF_WHISPER_DEVICE", "cpu")
    os.environ.setdefault("ONF_ALLOWED_ORIGINS", f"http://127.0.0.1:{args.port},http://localhost:{args.port}")
    log_path = configure_logging(data_dir)
    logging.info("Starting ONF Desktop %s with data at %s", args.port, data_dir)

    url = f"http://127.0.0.1:{args.port}"
    if port_is_open(args.port):
        payload = status_payload(url)
        if payload and payload.get("service") == APP_NAME:
            webbrowser.open(url)
            return 0
        raise RuntimeError(f"Port {args.port} is already in use by another application.")

    if not args.no_foundry:
        threading.Thread(target=start_foundry_local, name="onf-foundry-start", daemon=True).start()

    import uvicorn
    from backend.main import app

    server = uvicorn.Server(
        uvicorn.Config(
            app,
            host="127.0.0.1",
            port=args.port,
            log_config=None,
            access_log=False,
        )
    )
    server_thread = threading.Thread(target=server.run, name="onf-local-server", daemon=True)
    server_thread.start()
    wait_until_ready(url, server_thread)

    def open_onf(_icon=None, _item=None) -> None:
        webbrowser.open(url)

    def open_data(_icon=None, _item=None) -> None:
        os.startfile(data_dir)  # type: ignore[attr-defined]

    def open_log(_icon=None, _item=None) -> None:
        os.startfile(log_path)  # type: ignore[attr-defined]

    def exit_onf(icon, _item=None) -> None:
        server.should_exit = True
        icon.stop()

    import pystray

    menu = pystray.Menu(
        pystray.MenuItem("Open ONF", open_onf, default=True),
        pystray.MenuItem("Open portable data", open_data),
        pystray.MenuItem("View log", open_log),
        pystray.Menu.SEPARATOR,
        pystray.MenuItem("Exit ONF", exit_onf),
    )
    icon = pystray.Icon("onf-desktop", tray_image(), APP_NAME, menu)

    if not args.no_browser:
        threading.Timer(0.3, open_onf).start()
    icon.run()

    server.should_exit = True
    server_thread.join(timeout=10)
    logging.info("ONF Desktop stopped")
    return 0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Offline Neural Facilitator portable desktop host")
    parser.add_argument("--port", type=int, default=int(os.getenv("ONF_DESKTOP_PORT", str(DEFAULT_PORT))))
    parser.add_argument("--data-dir", default=os.getenv("ONF_DATA_DIR"))
    parser.add_argument("--no-browser", action="store_true")
    parser.add_argument("--no-foundry", action="store_true")
    return parser.parse_args()


def main() -> int:
    try:
        return run_desktop(parse_args())
    except Exception as exc:
        logging.exception("ONF Desktop failed")
        message_box(f"ONF could not start.\n\n{exc}", error=True)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())