"""
Bake independent 3s looping preview MP4s with example text/graphics.

Self-contained: does NOT import reels_audio_maker export styles/renderer.
Run once after install:  python scripts/bake_previews.py
"""

from __future__ import annotations

import math
import subprocess
import sys
from pathlib import Path

import cv2
import imageio_ffmpeg
import numpy as np

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "assets" / "previews"
GRADIENT_DIR = ROOT / "assets" / "gradients"

W, H = 360, 640
FPS = 30
DURATION = 3.0
EXAMPLE_TITLE = "Sample Loop"
EXAMPLE_ARTIST = "Demo Artist"
EXAMPLE_META = "128 BPM  ·  C minor"


def load_gradient_asset(palette_id: str) -> np.ndarray | None:
    """Load pre-rendered gradient background from assets/gradients/."""
    asset_path = GRADIENT_DIR / f"{palette_id}.png"
    if not asset_path.is_file():
        return None
    # Load with IMREAD_UNCHANGED to preserve 16-bit depth
    img = cv2.imread(str(asset_path), cv2.IMREAD_UNCHANGED)
    if img is None:
        return None

    # Convert to float32 [0, 255] regardless of source bit depth
    if img.dtype == np.uint16:
        # 16-bit PNG: [0, 65535] → [0, 255]
        img = img.astype(np.float32) / 257.0
    else:
        # 8-bit PNG
        img = img.astype(np.float32)

    # Resize to preview resolution
    return cv2.resize(img, (W, H), interpolation=cv2.INTER_LANCZOS4)


# style_id -> list of (palette_id, colors dict)
# Using the 5 universal palette IDs across all styles
PREVIEWS = {
    "neon_prism": [
        ("cyber_magenta", ((40, 0, 40), (10, 0, 20), (255, 0, 220), (0, 255, 240))),
        ("electric_cyan", ((30, 20, 0), (10, 5, 0), (255, 230, 0), (80, 255, 255))),
        ("acid_lime", ((5, 25, 5), (0, 8, 0), (40, 255, 80), (200, 255, 0))),
        ("hot_amber", ((0, 15, 40), (0, 5, 15), (0, 160, 255), (40, 220, 255))),
        ("ultra_violet", ((50, 0, 30), (15, 0, 10), (255, 60, 180), (255, 180, 255))),
    ],
    "crt_retro": [
        ("cyber_magenta", ((60, 20, 80), (20, 5, 10), (0, 120, 255), (180, 0, 255))),
        ("electric_cyan", ((40, 10, 5), (10, 0, 0), (255, 180, 40), (255, 80, 120))),
        ("acid_lime", ((70, 20, 50), (25, 5, 15), (255, 100, 255), (255, 220, 80))),
        ("hot_amber", ((8, 20, 5), (2, 5, 0), (40, 255, 60), (180, 255, 180))),
        ("ultra_violet", ((50, 15, 40), (15, 5, 20), (255, 120, 220), (200, 180, 255))),
    ],
    "orbital_pulse": [
        ("cyber_magenta", ((40, 15, 5), (10, 5, 0), (255, 180, 40), (255, 220, 120))),
        ("electric_cyan", ((30, 20, 10), (10, 8, 5), (180, 255, 120), (255, 160, 200))),
        ("acid_lime", ((15, 20, 35), (5, 8, 12), (40, 190, 255), (120, 230, 255))),
        ("hot_amber", ((35, 15, 30), (12, 5, 10), (200, 140, 255), (255, 160, 200))),
        ("ultra_violet", ((18, 18, 18), (5, 5, 5), (200, 200, 200), (255, 180, 80))),
    ],
    "glitch_tunnel": [
        ("cyber_magenta", ((10, 0, 0), (0, 0, 10), (0, 0, 255), (255, 0, 255))),
        ("electric_cyan", ((5, 20, 5), (0, 5, 0), (0, 255, 80), (0, 200, 255))),
        ("acid_lime", ((40, 20, 5), (15, 5, 0), (255, 220, 120), (200, 255, 255))),
        ("hot_amber", ((5, 0, 20), (0, 0, 5), (40, 40, 255), (80, 120, 255))),
        ("ultra_violet", ((20, 20, 20), (0, 0, 0), (220, 220, 220), (255, 255, 255))),
    ],
    "lofi_drift": [
        ("cyber_magenta", ((45, 55, 70), (25, 30, 40), (120, 170, 220), (160, 200, 240))),
        ("electric_cyan", ((50, 40, 35), (25, 20, 18), (180, 160, 140), (200, 190, 180))),
        ("acid_lime", ((40, 55, 70), (20, 30, 40), (80, 140, 200), (120, 180, 220))),
        ("hot_amber", ((70, 50, 60), (35, 25, 35), (200, 160, 220), (220, 190, 230))),
        ("ultra_violet", ((35, 25, 20), (12, 8, 6), (140, 120, 100), (180, 160, 140))),
    ],
}


def text(frame, s, center, scale, color, thick=2):
    font = cv2.FONT_HERSHEY_SIMPLEX
    (tw, th), _ = cv2.getTextSize(s, font, scale, thick)
    x = int(center[0] - tw / 2)
    y = int(center[1] + th / 2)

    # cv2.putText requires 8-bit image - convert temporarily
    frame_u8 = np.clip(frame, 0, 255).astype(np.uint8)
    cv2.putText(frame_u8, s, (x + 1, y + 1), font, scale, (0, 0, 0), thick + 1, cv2.LINE_AA)
    cv2.putText(frame_u8, s, (x, y), font, scale, color, thick, cv2.LINE_AA)

    # Copy back the modified text area
    y_min = max(0, y - th - 2)
    y_max = min(frame.shape[0], y + th + 2)
    x_min = max(0, x - 2)
    x_max = min(frame.shape[1], x + tw + 2)
    frame[y_min:y_max, x_min:x_max] = frame_u8[y_min:y_max, x_min:x_max].astype(np.float32)


def hud(frame, text_color, accent):
    # Title/artist moved DOWN; meta moved UP (out of Instagram bottom overlay)
    text(frame, EXAMPLE_TITLE, (W // 2, int(H * 0.16)), 0.85, text_color, 2)
    text(frame, EXAMPLE_ARTIST, (W // 2, int(H * 0.23)), 0.5, accent, 1)
    text(frame, EXAMPLE_META, (W // 2, int(H * 0.76)), 0.45, accent, 1)


def draw_neon(frame, t, primary, accent):
    pulse = 0.7 + 0.3 * abs(math.sin(t * 4))
    # Spectrum bars moved UP to avoid Instagram bottom overlay
    base_y = int(H * 0.52)
    n = 16
    for i in range(n):
        mag = 0.3 + 0.7 * abs(math.sin(t * 3 + i * 0.4))
        x = int(20 + i * ((W - 40) / n))
        bh = int(mag * 120 * pulse)
        bw = 12
        cv2.rectangle(frame, (x, base_y - bh), (x + bw, base_y), primary, -1)
        cv2.rectangle(frame, (x + bw, base_y - bh - 8), (x + bw + 8, base_y - 8), accent, -1)
    xs = np.linspace(0, W - 1, 80)
    pts = np.array(
        [[int(x), int(H * 0.66 + 20 * math.sin(t * 6 + x * 0.08))] for x in xs], np.int32
    )
    cv2.polylines(frame, [pts], False, accent, 2, cv2.LINE_AA)


def draw_crt(frame, t, primary, accent):
    horizon = int(H * 0.42)
    cv2.circle(frame, (W // 2, horizon - 30), 40, accent, -1)
    for i in range(1, 14):
        y = horizon + int((H - horizon) * (i / 14) ** 1.5)
        cv2.line(frame, (0, y), (W, y), primary, 1)
    for i in range(-8, 9):
        cv2.line(frame, (W // 2, horizon), (W // 2 + i * 40, H), primary, 1)
    frame[::2] = np.clip(frame[::2].astype(np.int16) - 20, 0, 255).astype(np.uint8)


def draw_orbital(frame, t, primary, accent):
    cx, cy = W // 2, int(H * 0.48)
    for k in range(5):
        r = int(40 + 28 * k + 8 * abs(math.sin(t * 3)))
        cv2.circle(frame, (cx, cy), r, primary if k % 2 == 0 else accent, 2)
    for i in range(24):
        ang = 2 * math.pi * i / 24 + t
        mag = 0.4 + 0.6 * abs(math.sin(t * 2 + i))
        r0, r1 = 50, int(50 + mag * 90)
        x0, y0 = int(cx + math.cos(ang) * r0), int(cy + math.sin(ang) * r0)
        x1, y1 = int(cx + math.cos(ang) * r1), int(cy + math.sin(ang) * r1)
        cv2.line(frame, (x0, y0), (x1, y1), accent, 2)
    cv2.circle(frame, (cx, cy), 35, accent, -1)


def draw_glitch(frame, t, primary, accent):
    cx, cy = W // 2, H // 2
    for i in range(18, 0, -1):
        s = i / 18
        rw = int(20 * s + 40 * s * abs(math.sin(t * 2 + i)))
        rh = int(30 * s + 50 * s * abs(math.sin(t * 2 + i * 0.5)))
        cv2.ellipse(frame, (cx, cy), (max(rw, 2), max(rh, 2)), 0, 0, 360, primary, 1)
    if abs(math.sin(t * 8)) > 0.7:
        y = int((t * 100) % (H - 30))
        block = frame[y : y + 20, 20:160].copy()
        frame[y : y + 20, 40:180] = block


def draw_lofi(frame, t, primary, accent):
    for i in range(5):
        cx = int(60 + i * 55 + 15 * math.sin(t * 0.8 + i))
        cy = int(H * 0.4 + 20 * math.sin(t * 0.5 + i))
        r = int(40 + 20 * abs(math.sin(t + i)))
        overlay = frame.copy()
        cv2.circle(overlay, (cx, cy), r, primary, -1)
        frame[:] = cv2.addWeighted(overlay, 0.2, frame, 0.8, 0)
    for i in range(30):
        px = int((i * 47 + t * 20) % W)
        py = int((i * 91 + math.sin(t + i) * 10) % H)
        cv2.circle(frame, (px, py), 1, accent, -1)


DRAWERS = {
    "neon_prism": draw_neon,
    "crt_retro": draw_crt,
    "orbital_pulse": draw_orbital,
    "glitch_tunnel": draw_glitch,
    "lofi_drift": draw_lofi,
}


def bake_one(style_id: str, palette_id: str, colors) -> Path:
    top, bottom, primary, accent = colors
    out_dir = OUT / style_id
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"{palette_id}.mp4"
    drawer = DRAWERS[style_id]
    ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
    total = int(DURATION * FPS)

    cmd = [
        ffmpeg,
        "-y",
        "-f",
        "rawvideo",
        "-vcodec",
        "rawvideo",
        "-s",
        f"{W}x{H}",
        "-pix_fmt",
        "bgr24",
        "-r",
        str(FPS),
        "-i",
        "-",
        "-an",
        "-c:v",
        "libx264",
        "-preset",
        "ultrafast",
        "-crf",
        "28",
        "-pix_fmt",
        "yuv420p",
        str(out_path),
    ]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
    assert proc.stdin is not None

    # Load pre-rendered gradient background once
    gradient_bg = load_gradient_asset(palette_id)
    if gradient_bg is None:
        raise RuntimeError(f"Gradient asset not found: {palette_id}.png")

    for i in range(total):
        t = i / FPS
        frame = gradient_bg.copy()  # Start with the pre-rendered gradient
        drawer(frame, t, primary, accent)
        hud(frame, (245, 245, 250), accent)
        proc.stdin.write(frame.tobytes())
    proc.stdin.close()
    err = proc.stderr.read() if proc.stderr else b""
    code = proc.wait()
    if code != 0:
        raise RuntimeError(f"bake failed {style_id}/{palette_id}: {err.decode(errors='ignore')[-400:]}")
    return out_path


def main() -> int:
    print(f"Baking previews into {OUT}")
    count = 0
    for style_id, palettes in PREVIEWS.items():
        for palette_id, colors in palettes:
            path = bake_one(style_id, palette_id, colors)
            count += 1
            print(f"  [{count}/25] {path.relative_to(ROOT)}")
    print("Done.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
