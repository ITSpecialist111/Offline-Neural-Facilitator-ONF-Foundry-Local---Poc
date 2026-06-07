"""Screen-capture (vision) service.

`pyautogui` is imported lazily so a headless/minimal install can still import
and boot the backend. Capture simply reports unavailable when the dependency or
a display is missing.
"""

from __future__ import annotations

import os
from datetime import datetime
from typing import Optional


class VisionService:
    def __init__(self, export_dir: Optional[str] = None, enabled: bool = True):
        self.enabled = enabled
        if not export_dir:
            user_profile = os.environ.get("USERPROFILE") or os.environ.get("HOME")
            if user_profile:
                self.export_dir = os.path.join(user_profile, "Documents", "FacilitatorReports", "Evidence")
            else:
                self.export_dir = "evidence"
        else:
            self.export_dir = export_dir

        try:
            os.makedirs(self.export_dir, exist_ok=True)
        except Exception:
            self.export_dir = "evidence"
            os.makedirs(self.export_dir, exist_ok=True)

    def capture_screen(self) -> Optional[str]:
        if not self.enabled:
            print("[VisionService] Disabled by configuration.")
            return None
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        filepath = os.path.join(self.export_dir, f"screenshot_{timestamp}.png")
        try:
            import pyautogui  # lazy: requires a display + dependency

            pyautogui.screenshot().save(filepath)
            return filepath
        except Exception as exc:
            print(f"[VisionService] Capture unavailable ({exc}).")
            return None
