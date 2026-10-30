"""CRT Retro Wave — synthwave grid, scanlines, RGB fringe."""

from __future__ import annotations

import cv2
import numpy as np

from .base import (
    FrameContext,
    Palette,
    add_grain,
    draw_hud,
    draw_waveform_strip,
    lerp_color,
    resample_spectrum,
    vertical_gradient,
)
from .palettes import get_style_palettes

PALETTES: list[Palette] = get_style_palettes("crt_retro")


def _draw_grid(frame: np.ndarray, p: Palette, t: float, pulse: float) -> None:
    h, w = frame.shape[:2]
    horizon = int(h * 0.42)
    # sun / glow disc
    sun_r = int(90 + 25 * pulse)
    cv2.circle(frame, (w // 2, horizon - 40), sun_r, p.glow, -1, cv2.LINE_AA)
    cv2.circle(frame, (w // 2, horizon - 40), sun_r // 2, lerp_color(p.primary, (255, 255, 255), 0.3), -1)

    # horizontal perspective lines
    for i in range(1, 18):
        y = horizon + int((h - horizon) * (i / 18) ** 1.6)
        alpha = 0.25 + 0.75 * (i / 18)
        color = lerp_color(p.bg_bottom, p.secondary, alpha)
        cv2.line(frame, (0, y), (w, y), color, 1, cv2.LINE_AA)

    # vanishing verticals
    vanish = (w // 2, horizon)
    scroll = (t * 40) % 40
    for i in range(-12, 13):
        x_bottom = int(w / 2 + i * (w / 10) + scroll * np.sign(i or 1))
        cv2.line(frame, vanish, (x_bottom, h), p.primary, 1, cv2.LINE_AA)


def _scanlines(frame: np.ndarray, strength: int = 28) -> np.ndarray:
    out = frame.copy()
    out[::2, :, :] = np.clip(out[::2, :, :].astype(np.int16) - strength, 0, 255).astype(np.uint8)
    return out


def _rgb_fringe(frame: np.ndarray, amount: int = 3) -> np.ndarray:
    b, g, r = cv2.split(frame)
    M = np.float32([[1, 0, amount], [0, 1, 0]])
    r2 = cv2.warpAffine(r, M, (frame.shape[1], frame.shape[0]), borderMode=cv2.BORDER_REFLECT)
    M2 = np.float32([[1, 0, -amount], [0, 1, 0]])
    b2 = cv2.warpAffine(b, M2, (frame.shape[1], frame.shape[0]), borderMode=cv2.BORDER_REFLECT)
    return cv2.merge([b2, g, r2])


def draw_frame(ctx: FrameContext) -> np.ndarray:
    p = ctx.palette
    frame = vertical_gradient(ctx.height, ctx.width, p.bg_top, p.bg_bottom)
    _draw_grid(frame, p, ctx.t, ctx.beat_pulse)

    bands = resample_spectrum(ctx.spectrum, 40)
    horizon = int(ctx.height * 0.42)
    # spectrum mountains above horizon
    xs = np.linspace(0, ctx.width - 1, len(bands)).astype(int)
    pts = [[0, horizon]]
    for x, mag in zip(xs, bands):
        y = horizon - int(mag * ctx.height * 0.22 * (0.8 + 0.2 * ctx.beat_pulse))
        pts.append([int(x), y])
    pts.append([ctx.width - 1, horizon])
    cv2.fillPoly(frame, [np.array(pts, np.int32)], p.accent)

    draw_waveform_strip(
        frame,
        ctx.waveform,
        y_center=horizon + 8,
        height=int(ctx.height * 0.06),
        color=p.secondary,
        mirror=True,
    )

    frame = _scanlines(frame, 22)
    frame = _rgb_fringe(frame, amount=2 + int(3 * ctx.beat_pulse))
    frame = add_grain(frame, 8.0, seed=int(ctx.t * 30) % 10_000)
    draw_hud(frame, ctx, title_scale=2.2)
    return frame
