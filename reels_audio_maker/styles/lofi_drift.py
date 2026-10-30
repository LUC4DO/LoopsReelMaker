"""LoFi Drift — soft gradients, floating particles, gentle waveform."""

from __future__ import annotations

import cv2
import numpy as np

from .base import (
    FrameContext,
    Palette,
    add_grain,
    add_vignette,
    draw_hud,
    draw_waveform_strip,
    lerp_color,
    resample_spectrum,
    vertical_gradient,
)
from .palettes import get_style_palettes

PALETTES: list[Palette] = get_style_palettes("lofi_drift")


def draw_frame(ctx: FrameContext) -> np.ndarray:
    p = ctx.palette
    # Load pre-rendered gradient background (with vignette)
    frame = vertical_gradient(ctx.height, ctx.width, p.bg_top, p.bg_bottom,
                              style_id="lofi_drift", palette_id=p.id)

    # soft glowing blobs reactive to low bands
    bands = resample_spectrum(ctx.spectrum, 8)
    for i, mag in enumerate(bands):
        cx = int(ctx.width * (0.15 + 0.1 * i) + 40 * np.sin(ctx.t * 0.3 + i))
        cy = int(ctx.height * (0.35 + 0.05 * np.sin(ctx.t * 0.25 + i * 0.7)))
        radius = int(80 + mag * 180 + 20 * ctx.beat_pulse)
        overlay = frame.copy()
        color = lerp_color(p.primary, p.accent, i / max(len(bands) - 1, 1))
        cv2.circle(overlay, (cx, cy), radius, color, -1, cv2.LINE_AA)
        frame = cv2.addWeighted(overlay, 0.18 + 0.1 * mag, frame, 0.82 - 0.1 * mag, 0)

    # floating particles
    rng = np.random.default_rng(7)
    for i in range(60):
        base_x = rng.random()
        base_y = rng.random()
        px = int((base_x * ctx.width + ctx.t * 12 * (0.5 + base_x)) % ctx.width)
        py = int((base_y * ctx.height + np.sin(ctx.t * 0.5 + i) * 20) % ctx.height)
        cv2.circle(frame, (px, py), int(1 + 2 * rng.random()), p.glow, -1, cv2.LINE_AA)

    draw_waveform_strip(
        frame,
        ctx.waveform,
        y_center=int(ctx.height * 0.70),
        height=int(ctx.height * 0.10),
        color=p.secondary,
        mirror=True,
    )

    frame = add_grain(frame, 6.0, seed=int(ctx.t * 5) % 10_000)
    frame = add_vignette(frame, 0.6)
    draw_hud(frame, ctx, title_scale=2.0)
    return frame
