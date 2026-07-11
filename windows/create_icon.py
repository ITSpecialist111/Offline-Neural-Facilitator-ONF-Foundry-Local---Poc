"""Generate the ONF multi-resolution Windows icon used by PyInstaller."""

from __future__ import annotations

import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


def main() -> int:
    destination = Path(sys.argv[1] if len(sys.argv) > 1 else Path(__file__).with_name("onf.ico"))
    destination.parent.mkdir(parents=True, exist_ok=True)

    canvas = Image.new("RGBA", (256, 256), "#0f172a")
    draw = ImageDraw.Draw(canvas)
    draw.rounded_rectangle((12, 12, 244, 244), radius=58, fill="#2563eb", outline="#bfdbfe", width=9)
    draw.ellipse((39, 39, 217, 217), fill="#0f172a", outline="#60a5fa", width=6)
    draw.ellipse((67, 67, 189, 189), fill="#1d4ed8", outline="#dbeafe", width=4)
    font = ImageFont.truetype("segoeuib.ttf", 56)
    draw.text((128, 128), "ONF", fill="white", font=font, anchor="mm")
    canvas.save(destination, format="ICO", sizes=[(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
