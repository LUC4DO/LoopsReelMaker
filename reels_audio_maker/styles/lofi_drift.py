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

PALETTES: list[Palette] = [
    Palette(
        "study_lamp",
        "Study Lamp",
        bg_top=(38, 46, 59),
        bg_bottom=(21, 25, 34),
        primary=(120, 170, 220),
        secondary=(90, 130, 180),
        accent=(160, 200, 240),
        text=(245, 240, 230),
        glow=(180, 200, 220),
    ),
    Palette(
        "rain_window",
        "Rain Window",
        bg_top=(42, 34, 29),
        bg_bottom=(21, 17, 15),
        primary=(180, 160, 140),
        secondary=(140, 130, 120),
        accent=(200, 190, 180),
        text=(235, 235, 240),
        glow=(190, 185, 180),
    ),
    Palette(
        "cafe_sepia",
        "Cafe Sepia",
        bg_top=(34, 46, 59),
        bg_bottom=(17, 25, 34),
        primary=(80, 140, 200),
        secondary=(60, 100, 150),
        accent=(120, 180, 220),
        text=(245, 235, 220),
        glow=(140, 180, 210),
    ),
    Palette(
        "pastel_dusk",
        "Pastel Dusk",
        bg_top=(59, 42, 51),
        bg_bottom=(29, 21, 29),
        primary=(200, 160, 220),
        secondary=(160, 180, 230),
        accent=(220, 190, 230),
        text=(250, 245, 250),
        glow=(210, 180, 230),
    ),
    Palette(
        "midnight_tea",
        "Midnight Tea",
        bg_top=(29, 21, 17),
        bg_bottom=(10, 6, 5),
        primary=(140, 120, 100),
        secondary=(100, 90, 80),
        accent=(180, 160, 140),
        text=(230, 225, 220),
        glow=(160, 140, 120),
    ),
]


def draw_frame(ctx: FrameContext) -> np.ndarray:
    p = ctx.palette
    # static gradient using defined top and bottom colors
    frame = vertical_gradient(ctx.height, ctx.width, p.bg_top, p.bg_bottom)

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
