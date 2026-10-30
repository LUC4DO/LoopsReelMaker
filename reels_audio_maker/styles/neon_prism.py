"""Neon Prism — extruded 3D spectrum bars + mirrored waveform."""

from __future__ import annotations

import cv2
import numpy as np

from .base import (
    FrameContext,
    Palette,
    draw_hud,
    draw_waveform_strip,
    lerp_color,
    perspective_bar_poly,
    resample_spectrum,
    vertical_gradient,
)
from .palettes import get_style_palettes

PALETTES: list[Palette] = get_style_palettes("neon_prism")


def draw_frame(ctx: FrameContext) -> np.ndarray:
    p = ctx.palette
    # Load pre-rendered gradient background (with vignette)
    frame = vertical_gradient(ctx.height, ctx.width, p.bg_top, p.bg_bottom,
                              style_id="neon_prism", palette_id=p.id)
    bands = resample_spectrum(ctx.spectrum, 52)
    pulse = 0.85 + 0.25 * ctx.beat_pulse

    base_y = int(ctx.height * 0.72)
    margin = int(ctx.width * 0.08)
    usable = ctx.width - 2 * margin
    bar_w = max(8, usable // len(bands) - 6)
    depth = int(18 + 10 * ctx.beat_pulse)
    max_h = int(ctx.height * 0.38)

    for i, mag in enumerate(bands):
        x = margin + i * (usable // len(bands))
        bar_h = int(mag * max_h * pulse)
        if bar_h < 4:
            continue
        face = lerp_color(p.primary, p.accent, i / max(len(bands) - 1, 1))
        side = lerp_color(face, (0, 0, 0), 0.35)
        top = lerp_color(face, p.glow, 0.4)
        poly = perspective_bar_poly(x, base_y, bar_w, bar_h, depth)
        # face
        cv2.fillPoly(
            frame,
            [np.array([[x, base_y], [x + bar_w, base_y], [x + bar_w, base_y - bar_h], [x, base_y - bar_h]], np.int32)],
            face,
        )
        # top
        cv2.fillPoly(
            frame,
            [
                np.array(
                    [
                        [x, base_y - bar_h],
                        [x + bar_w, base_y - bar_h],
                        [x + bar_w + depth, base_y - bar_h - depth],
                        [x + depth, base_y - bar_h - depth],
                    ],
                    np.int32,
                )
            ],
            top,
        )
        # side
        cv2.fillPoly(
            frame,
            [
                np.array(
                    [
                        [x + bar_w, base_y],
                        [x + bar_w + depth, base_y - depth],
                        [x + bar_w + depth, base_y - bar_h - depth],
                        [x + bar_w, base_y - bar_h],
                    ],
                    np.int32,
                )
            ],
            side,
        )
        cv2.polylines(frame, [poly[:4]], True, p.glow, 1, cv2.LINE_AA)

    draw_waveform_strip(
        frame,
        ctx.waveform,
        y_center=int(ctx.height * 0.82),
        height=int(ctx.height * 0.08),
        color=p.secondary,
        mirror=True,
    )
    draw_hud(frame, ctx, title_scale=2.4)
    # No vignette
    return frame
