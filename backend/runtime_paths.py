"""Runtime paths shared by source and packaged ONF builds.

Development keeps the existing repository-relative layout. A frozen portable
build reads bundled assets from PyInstaller's resource directory and writes all
mutable state beside ``ONF.exe`` unless ``ONF_DATA_DIR`` overrides it.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path


def is_frozen() -> bool:
    return bool(getattr(sys, "frozen", False))


def resource_root() -> Path:
    if is_frozen() and hasattr(sys, "_MEIPASS"):
        return Path(sys._MEIPASS).resolve()
    return Path(__file__).resolve().parent.parent


def executable_root() -> Path:
    if is_frozen():
        return Path(sys.executable).resolve().parent
    return resource_root()


def resource_path(*parts: str) -> Path:
    return resource_root().joinpath(*parts)


def data_root() -> Path:
    configured = os.getenv("ONF_DATA_DIR")
    if configured:
        root = Path(configured).expanduser()
    elif is_frozen():
        root = executable_root() / "data"
    else:
        root = resource_root()
    root.mkdir(parents=True, exist_ok=True)
    return root.resolve()


def data_path(*parts: str, create_parent: bool = False) -> Path:
    path = data_root().joinpath(*parts)
    if create_parent:
        path.parent.mkdir(parents=True, exist_ok=True)
    return path