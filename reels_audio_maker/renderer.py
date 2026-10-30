"""Export-only frame composition at Reels resolution."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from .audio_analysis import (
    AudioAnalysis,
    beat_pulse_at,
    spectrum_at,
    waveform_window,
)
from .styles import StyleDef, get_style
from .styles.base import FrameContext, Palette, finalize_frame

# Instagram Reels 1440p vertical
EXPORT_WIDTH = 1440
EXPORT_HEIGHT = 2560
EXPORT_FPS = 30
MAX_DURATION_SEC = 30.0


@dataclass
class RenderSettings:
    style_id: str
    palette_id: str
    loop_name: str
    artist: str
    bpm: float
    key: str
    width: int = EXPORT_WIDTH
    height: int = EXPORT_HEIGHT
    fps: int = EXPORT_FPS


def video_duration(analysis: AudioAnalysis) -> float:
    return min(MAX_DURATION_SEC, float(analysis.duration))


def make_context(
    analysis: AudioAnalysis,
    settings: RenderSettings,
    t: float,
    palette: Palette,
) -> FrameContext:
    return FrameContext(
        width=settings.width,
        height=settings.height,
        t=t,
        duration=video_duration(analysis),
        bpm=settings.bpm,
        key=settings.key,
        loop_name=settings.loop_name,
        artist=settings.artist,
        spectrum=spectrum_at(analysis, t),
        waveform=waveform_window(analysis, t),
        beat_pulse=beat_pulse_at(t, settings.bpm),
        palette=palette,
    )


def draw_export_frame(
    analysis: AudioAnalysis,
    settings: RenderSettings,
    t: float,
) -> np.ndarray:
    style: StyleDef = get_style(settings.style_id)
    palette = style.palette_by_id(settings.palette_id)
    ctx = make_context(analysis, settings, t, palette)
    return style.draw_frame(ctx)
