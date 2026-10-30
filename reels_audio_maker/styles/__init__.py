"""Style registry: id -> display name, palettes, draw_frame."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Sequence

import numpy as np

from . import crt_retro, glitch_tunnel, lofi_drift, neon_prism, orbital_pulse
from .base import FrameContext, Palette

DrawFn = Callable[[FrameContext], np.ndarray]


@dataclass(frozen=True)
class StyleDef:
    id: str
    name: str
    palettes: Sequence[Palette]
    draw_frame: DrawFn

    def palette_by_id(self, palette_id: str) -> Palette:
        for p in self.palettes:
            if p.id == palette_id:
                return p
        return self.palettes[0]


STYLES: list[StyleDef] = [
    StyleDef("neon_prism", "Neon Prism", neon_prism.PALETTES, neon_prism.draw_frame),
    StyleDef("crt_retro", "CRT Retro Wave", crt_retro.PALETTES, crt_retro.draw_frame),
    StyleDef("orbital_pulse", "Orbital Pulse", orbital_pulse.PALETTES, orbital_pulse.draw_frame),
    StyleDef("glitch_tunnel", "Glitch Tunnel", glitch_tunnel.PALETTES, glitch_tunnel.draw_frame),
    StyleDef("lofi_drift", "LoFi Drift", lofi_drift.PALETTES, lofi_drift.draw_frame),
]

STYLES_BY_ID = {s.id: s for s in STYLES}


def get_style(style_id: str) -> StyleDef:
    return STYLES_BY_ID.get(style_id, STYLES[0])
