"""Shared palette model, HUD drawing, and geometry helpers for export styles."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Tuple

import cv2
import numpy as np

Color = Tuple[int, int, int]  # BGR for OpenCV

# Cache for loaded gradient backgrounds
_GRADIENT_CACHE: dict[str, np.ndarray] = {}


@dataclass(frozen=True)
class Palette:
    id: str
    name: str
    bg_top: Color
    bg_bottom: Color
    primary: Color
    secondary: Color
    accent: Color
    text: Color
    glow: Color = (255, 255, 255)


@dataclass(frozen=True)
class FrameContext:
    width: int
    height: int
    t: float
    duration: float
    bpm: float
    key: str
    loop_name: str
    artist: str
    spectrum: np.ndarray  # shape (n_bands,) normalized 0..1
    waveform: np.ndarray  # shape (n_samples,) -1..1 for current window
    beat_pulse: float  # 0..1
    palette: Palette


def _load_gradient_asset(style_id: str, palette_id: str) -> np.ndarray | None:
    """Load pre-rendered gradient background from assets/gradients/.
    Returns float32 array (0..255) or None if not found.

    Handles both 8-bit and 16-bit PNGs automatically.
    """
    cache_key = f"{style_id}_{palette_id}"
    if cache_key in _GRADIENT_CACHE:
        return _GRADIENT_CACHE[cache_key]

    # Project root = parent of package
    root = Path(__file__).resolve().parent.parent.parent
    asset_path = root / "assets" / "gradients" / f"{style_id}_{palette_id}.png"

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
        # 8-bit PNG: [0, 255] → [0, 255] as float32
        img = img.astype(np.float32)

    _GRADIENT_CACHE[cache_key] = img
    return img


def vertical_gradient(h: int, w: int, top: Color, bottom: Color,
                      invert: bool = False, style_id: str | None = None,
                      palette_id: str | None = None) -> np.ndarray:
    """Vertical linear gradient from top to bottom color.

    If style_id and palette_id are provided, loads pre-rendered high-quality
    gradient from assets/gradients/ (with subtle vignette). Falls back to
    procedural generation if asset not found.

    Returns float32 array (0..255 range) to preserve precision for 10-bit encoding.
    """
    # Try to load pre-rendered gradient asset
    if style_id and palette_id:
        asset = _load_gradient_asset(style_id, palette_id)
        if asset is not None:
            # Resize if needed (should match export resolution)
            if asset.shape[0] != h or asset.shape[1] != w:
                asset = cv2.resize(asset, (w, h), interpolation=cv2.INTER_LANCZOS4)
            return asset

    # Fallback: procedural gradient
    if invert:
        top, bottom = bottom, top
    # t: (h, 1, 1) - vertical gradient weights
    t = np.linspace(0, 1, h, dtype=np.float32).reshape(h, 1, 1)
    top_arr = np.array(top, dtype=np.float32).reshape(1, 1, 3)
    bottom_arr = np.array(bottom, dtype=np.float32).reshape(1, 1, 3)
    # gradient: (h, 1, 3) -> tile to (h, w, 3)
    gradient = top_arr * (1 - t) + bottom_arr * t
    gradient = np.tile(gradient, (1, w, 1))
    return np.clip(gradient, 0.0, 255.0).astype(np.float32)


def finalize_frame(frame: np.ndarray) -> np.ndarray:
    """Returns the frame in its native precision. Keeps float32 for 10-bit encoding."""
    return np.ascontiguousarray(np.clip(frame, 0.0, 255.0))


def lerp_color(a: Color, b: Color, t: float) -> Color:
    t = float(np.clip(t, 0.0, 1.0))
    return tuple(int(a[i] * (1 - t) + b[i] * t) for i in range(3))  # type: ignore[return-value]


def draw_centered_text(
    frame: np.ndarray,
    text: str,
    center: Tuple[int, int],
    scale: float,
    color: Color,
    thickness: int = 2,
    font: int = cv2.FONT_HERSHEY_SIMPLEX,
) -> None:
    if not text:
        return
    (tw, th), _ = cv2.getTextSize(text, font, scale, thickness)
    x = int(center[0] - tw / 2)
    y = int(center[1] + th / 2)

    # Cast to uint8 temporarily for text drawing, as cv2.putText requires it
    # We create a temporary view or cast if necessary, but putText works on np.ndarray
    # If frame is float32, we draw to a copy and merge or cast temporarily.
    # Actually, simpler: cast the frame segment for text.
    frame_u8 = np.clip(frame, 0, 255).astype(np.uint8)

    # soft shadow
    cv2.putText(frame_u8, text, (x + 2, y + 2), font, scale, (0, 0, 0), thickness + 2, cv2.LINE_AA)
    cv2.putText(frame_u8, text, (x, y), font, scale, color, thickness, cv2.LINE_AA)

    # Copy back the modified text area into the float32 frame
    # We identify the bounding box of the text
    y_min = max(0, y - th)
    y_max = min(frame.shape[0], y + th)
    x_min = max(0, x)
    x_max = min(frame.shape[1], x + tw + thickness + 4)
    frame[y_min:y_max, x_min:x_max] = frame_u8[y_min:y_max, x_min:x_max].astype(np.float32)


def draw_hud(frame: np.ndarray, ctx: FrameContext, title_scale: float = 2.2) -> None:
    """Standard loop name / artist / BPM / key overlay."""
    h, w = frame.shape[:2]
    draw_centered_text(frame, ctx.loop_name, (w // 2, int(h * 0.12)), title_scale, ctx.palette.text, 3)
    if ctx.artist:
        draw_centered_text(
            frame,
            ctx.artist,
            (w // 2, int(h * 0.18)),
            title_scale * 0.45,
            ctx.palette.secondary,
            2,
        )
    meta = f"{int(round(ctx.bpm))} BPM  ·  {ctx.key}"
    draw_centered_text(frame, meta, (w // 2, int(h * 0.92)), 1.1, ctx.palette.accent, 2)


def add_vignette(frame: np.ndarray, strength: float = 0.15) -> np.ndarray:
    h, w = frame.shape[:2]
    y, x = np.ogrid[:h, :w]
    cy, cx = h / 2, w / 2
    dist = np.sqrt((x - cx) ** 2 + (y - cy) ** 2)
    max_dist = np.sqrt(cx**2 + cy**2)
    mask = 1.0 - strength * (dist / max_dist) ** 2
    mask = np.clip(mask, 0.15, 1.0).astype(np.float32)
    out = frame.astype(np.float32) * mask[..., None]
    return np.clip(out, 0, 255).astype(np.uint8)


def add_grain(frame: np.ndarray, amount: float = 12.0, seed: int | None = None) -> np.ndarray:
    rng = np.random.default_rng(seed)
    noise = rng.normal(0, amount, frame.shape).astype(np.float32)
    return np.clip(frame.astype(np.float32) + noise, 0, 255).astype(np.uint8)


def draw_waveform_strip(
    frame: np.ndarray,
    samples: np.ndarray,
    y_center: int,
    height: int,
    color: Color,
    mirror: bool = True,
) -> None:
    h, w = frame.shape[:2]
    if samples.size == 0:
        return
    xs = np.linspace(0, w - 1, num=min(len(samples), w)).astype(int)
    idxs = np.linspace(0, len(samples) - 1, num=len(xs)).astype(int)
    vals = samples[idxs]
    amp = height // 2
    pts_top = []
    pts_bot = []
    for x, v in zip(xs, vals):
        dy = int(np.clip(v, -1, 1) * amp)
        pts_top.append([x, y_center - dy])
        pts_bot.append([x, y_center + dy if mirror else y_center])
    if len(pts_top) > 1:
        cv2.polylines(frame, [np.array(pts_top, dtype=np.int32)], False, color, 2, cv2.LINE_AA)
        if mirror:
            cv2.polylines(frame, [np.array(pts_bot, dtype=np.int32)], False, color, 2, cv2.LINE_AA)


def perspective_bar_poly(
    x: int,
    base_y: int,
    bar_w: int,
    bar_h: int,
    depth: int,
) -> np.ndarray:
    """Return polygon for a simple extruded bar."""
    return np.array(
        [
            [x, base_y],
            [x + bar_w, base_y],
            [x + bar_w + depth, base_y - depth],
            [x + depth, base_y - depth],
            [x + depth, base_y - depth - bar_h],
            [x + bar_w + depth, base_y - depth - bar_h],
            [x + bar_w, base_y - bar_h],
            [x, base_y - bar_h],
        ],
        dtype=np.int32,
    )


def resample_spectrum(spectrum: np.ndarray, bands: int) -> np.ndarray:
    if spectrum.size == 0:
        return np.zeros(bands, dtype=np.float32)
    x_old = np.linspace(0, spectrum.size - 1, spectrum.size)
    x_new = np.linspace(0, spectrum.size - 1, bands)
    return np.interp(x_new, x_old, spectrum).astype(np.float32)


def beat_phase(t: float, bpm: float) -> float:
    if bpm <= 0:
        return 0.0
    period = 60.0 / bpm
    return (t % period) / period
