"""Glitch Tunnel — bass-driven tunnel with chromatic glitch on beats."""

from __future__ import annotations

import cv2
import numpy as np

from .base import (
    FrameContext,
    Palette,
    add_grain,
    draw_centered_text,
    lerp_color,
    resample_spectrum,
    vertical_gradient,
)
from .palettes import get_style_palettes

PALETTES: list[Palette] = get_style_palettes("glitch_tunnel")


def _tunnel(frame: np.ndarray, p: Palette, t: float, spectrum: np.ndarray, pulse: float) -> None:
    h, w = frame.shape[:2]
    cx, cy = w // 2, h // 2
    bands = resample_spectrum(spectrum, 24)
    depth_scroll = (t * 120) % 40

    for i in range(24, 0, -1):
        scale = i / 24
        mag = bands[i % len(bands)]
        rw = int(w * 0.08 * scale + mag * w * 0.12 * pulse)
        rh = int(h * 0.08 * scale + mag * h * 0.10 * pulse)
        offset = int(depth_scroll * scale)
        color = lerp_color(p.primary, p.accent, 1 - scale)
        cv2.ellipse(
            frame,
            (cx, cy + offset // 8),
            (max(rw, 2), max(rh, 2)),
            0,
            0,
            360,
            color,
            2,
            cv2.LINE_AA,
        )
        # wall ribs
        for a in range(0, 360, 30):
            rad = np.deg2rad(a + t * 40)
            x1 = int(cx + np.cos(rad) * rw * 0.3)
            y1 = int(cy + np.sin(rad) * rh * 0.3)
            x2 = int(cx + np.cos(rad) * rw)
            y2 = int(cy + np.sin(rad) * rh)
            cv2.line(frame, (x1, y1), (x2, y2), p.secondary, 1, cv2.LINE_AA)


def _block_glitch(frame: np.ndarray, intensity: float, seed: int) -> np.ndarray:
    if intensity < 0.35:
        return frame
    out = frame.copy()
    h, w = out.shape[:2]
    rng = np.random.default_rng(seed)
    n = int(4 + 10 * intensity)
    max_bw = max(41, w // 2)
    for _ in range(n):
        bh = int(rng.integers(8, min(60, h)))
        bw = int(rng.integers(40, max_bw))
        y = int(rng.integers(0, max(h - bh, 1)))
        x = int(rng.integers(0, max(w - bw, 1)))
        shift = int(rng.integers(-40, 40))
        src = out[y : y + bh, x : x + bw].copy()
        nx = int(np.clip(x + shift, 0, w - bw))
        out[y : y + bh, nx : nx + bw] = src
    return out


def _chromatic(frame: np.ndarray, amount: int) -> np.ndarray:
    b, g, r = cv2.split(frame)
    M = np.float32([[1, 0, amount], [0, 1, 0]])
    r2 = cv2.warpAffine(r, M, (frame.shape[1], frame.shape[0]), borderMode=cv2.BORDER_REFLECT)
    M2 = np.float32([[1, 0, -amount], [0, 1, 0]])
    b2 = cv2.warpAffine(b, M2, (frame.shape[1], frame.shape[0]), borderMode=cv2.BORDER_REFLECT)
    return cv2.merge([b2, g, r2])


def draw_frame(ctx: FrameContext) -> np.ndarray:
    p = ctx.palette
    frame = vertical_gradient(ctx.height, ctx.width, p.bg_top, p.bg_bottom,
                              style_id="glitch_tunnel", palette_id=p.id)
    _tunnel(frame, p, ctx.t, ctx.spectrum, 0.7 + 0.3 * ctx.beat_pulse)

    # starfield rush
    rng = np.random.default_rng(42)
    for i in range(80):
        z = ((rng.random() + ctx.t * 0.5) % 1.0)
        ang = rng.random() * 2 * np.pi
        rad = z * min(ctx.width, ctx.height) * 0.55
        px = int(ctx.width / 2 + np.cos(ang) * rad)
        py = int(ctx.height / 2 + np.sin(ang) * rad)
        cv2.circle(frame, (px, py), 1 + int(2 * z), p.glow, -1)

    jitter = int(6 * ctx.beat_pulse)
    title_pos = (ctx.width // 2 + int(np.sin(ctx.t * 40) * jitter), int(ctx.height * 0.14))
    draw_centered_text(frame, ctx.loop_name, title_pos, 2.3, p.text, 3)
    if ctx.artist:
        draw_centered_text(
            frame,
            ctx.artist,
            (ctx.width // 2 - jitter, int(ctx.height * 0.20)),
            1.0,
            p.secondary,
            2,
        )
    meta = f"{int(round(ctx.bpm))} BPM  ·  {ctx.key}"
    draw_centered_text(frame, meta, (ctx.width // 2, int(ctx.height * 0.90)), 1.1, p.accent, 2)

    frame = _block_glitch(frame, ctx.beat_pulse, seed=int(ctx.t * 20) % 10_000)
    frame = _chromatic(frame, amount=1 + int(6 * ctx.beat_pulse))
    frame = add_grain(frame, 10 + 20 * ctx.beat_pulse, seed=int(ctx.t * 15) % 10_000)
    return frame
