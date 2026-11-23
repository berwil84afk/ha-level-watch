"""Render the README screenshots with a headless Chrome or Edge.

Usage (from the repository root, with the preview server running):

    python -m http.server 8766 --bind 127.0.0.1
    python dev/make_screenshots.py

Writes docs/screenshots/<lang>/<shot>.png, trimmed to the content.
Needs Pillow for trimming.
"""

from __future__ import annotations

import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from PIL import Image, ImageChops

BASE_URL = "http://127.0.0.1:8766/dev/screenshots.html"
OUT = Path(__file__).resolve().parent.parent / "docs" / "screenshots"
SCALE = 2
SHOTS = {
    # name: (query, window width, window height)
    "card-styles": ("shot=styles&theme=dark", 1000, 720),
    "tank-shapes": ("shot=tanks&theme=dark", 1140, 360),
    "threshold-editor": ("shot=editor&theme=light", 640, 860),
}
BROWSERS = [
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
    "google-chrome",
    "chromium",
]


def browser() -> str:
    for candidate in BROWSERS:
        if Path(candidate).exists() or shutil.which(candidate):
            return candidate
    sys.exit("No Chrome, Chromium or Edge found")


def trim(path: Path, margin: int = 16 * SCALE) -> None:
    """Cut the uniform page background down to a small margin."""
    img = Image.open(path).convert("RGB")
    bg = Image.new("RGB", img.size, img.getpixel((2, 2)))
    box = ImageChops.difference(img, bg).getbbox()
    if box:
        left, top, right, bottom = box
        img = img.crop(
            (
                max(0, left - margin),
                max(0, top - margin),
                min(img.width, right + margin),
                min(img.height, bottom + margin),
            )
        )
    img.save(path, optimize=True)


def main() -> None:
    exe = browser()
    for lang in ("en", "de"):
        target = OUT / lang
        target.mkdir(parents=True, exist_ok=True)
        for name, (query, width, height) in SHOTS.items():
            out = target / f"{name}.png"
            with tempfile.TemporaryDirectory() as profile:
                subprocess.run(
                    [
                        exe,
                        "--headless=new",
                        "--disable-gpu",
                        "--hide-scrollbars",
                        f"--user-data-dir={profile}",
                        f"--force-device-scale-factor={SCALE}",
                        f"--window-size={width},{height}",
                        "--virtual-time-budget=6000",
                        f"--lang={lang}",
                        f"--screenshot={out}",
                        f"{BASE_URL}?lang={lang}&{query}",
                    ],
                    check=True,
                    capture_output=True,
                    timeout=120,
                )
            trim(out)
            print(out.relative_to(OUT.parent.parent), Image.open(out).size)


if __name__ == "__main__":
    main()
