"""Orbital Pulse — concentric rings, radial spectrum, beat particles."""

from __future__ import annotations

import cv2
import numpy as np

from .base import (
    FrameContext,
    Palette,
    add_vignette,
    draw_centered_text,
    lerp_color,
    resample_spectrum,
    vertical_gradient,
)
from .palettes import get_style_palettes

PALETTES: list[Palette] = get_style_palettes("orbital_pulse")


def draw_frame(ctx: FrameContext) -> np.ndarray:
    p = ctx.palette
    frame = vertical_gradient(ctx.height, ctx.width, p.bg_top, p.bg_bottom)
    cx, cy = ctx.width // 2, int(ctx.height * 0.48)
    bands = resample_spectrum(ctx.spectrum, 48)
    n = len(bands)

    # outer radial spokes
    max_r = int(min(ctx.width, ctx.height) * 0.38)
    for i, mag in enumerate(bands):
        ang = (2 * np.pi * i / n) - ctx.t * 0.4
        r0 = int(max_r * 0.35)
        r1 = int(r0 + mag * max_r * 0.55 * (0.85 + 0.15 * ctx.beat_pulse))
        x0 = int(cx + np.cos(ang) * r0)
        y0 = int(cy + np.sin(ang) * r0)
        x1 = int(cx + np.cos(ang) * r1)
        y1 = int(cy + np.sin(ang) * r1)
        color = lerp_color(p.primary, p.accent, mag)
        cv2.line(frame, (x0, y0), (x1, y1), color, 3, cv2.LINE_AA)

    # concentric rings
    for k in range(5):
        r = int(max_r * (0.25 + 0.15 * k) + 8 * ctx.beat_pulse * (k + 1))
        color = lerp_color(p.secondary, p.glow, k / 4)
        cv2.circle(frame, (cx, cy), r, color, 2, cv2.LINE_AA)

    # glowing core
    core_r = int(70 + 30 * ctx.beat_pulse)
    overlay = frame.copy()
    cv2.circle(overlay, (cx, cy), core_r, p.glow, -1, cv2.LINE_AA)
    cv2.circle(overlay, (cx, cy), core_r // 2, p.primary, -1, cv2.LINE_AA)
    frame = cv2.addWeighted(overlay, 0.55, frame, 0.45, 0)

    # beat particles
    rng = np.random.default_rng(int(ctx.t * 8) % 10_000)
    n_part = int(20 + 40 * ctx.beat_pulse)
    for _ in range(n_part):
        ang = float(rng.uniform(0, 2 * np.pi))
        rad = float(rng.uniform(core_r, max_r))
        px = int(cx + np.cos(ang) * rad)
        py = int(cy + np.sin(ang) * rad)
        cv2.circle(frame, (px, py), int(rng.integers(2, 5)), p.accent, -1, cv2.LINE_AA)

    draw_centered_text(frame, ctx.loop_name, (cx, cy - 18), 1.6, p.text, 3)
    if ctx.artist:
        draw_centered_text(frame, ctx.artist, (cx, cy + 28), 0.8, p.secondary, 2)
    meta = f"{int(round(ctx.bpm))} BPM  ·  {ctx.key}"
    draw_centered_text(frame, meta, (cx, int(ctx.height * 0.88)), 1.0, p.accent, 2)
    return add_vignette(frame, 0.2)
