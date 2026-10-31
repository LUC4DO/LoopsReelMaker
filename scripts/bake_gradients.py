#!/usr/bin/env python3
"""
Generate ultra-high-quality gradient background images for the 5 color palettes.

Each palette gets ONE gradient background (style-agnostic), used across all 5 styles.

Features:
- Oklab perceptual color space interpolation (no muddy midtones, hue-preserving)
- Expanded range: lighter top → darker bottom for maximum visual depth
- 16-bit PNG output (48-bit RGB, 65536 levels/channel → zero banding at source)
- Float32 precision throughout

Run once: python scripts/bake_gradients.py
"""

from __future__ import annotations

import sys
from pathlib import Path

import cv2
import numpy as np

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from reels_audio_maker.styles.palettes import STYLE_PALETTES

# Export resolution (Instagram Reels 1440p vertical)
W, H = 1440, 2560

OUT_DIR = Path(__file__).resolve().parent.parent / "assets" / "gradients"

# Gradient expansion factors
# Make top lighter (toward white) and bottom darker (toward black)
TOP_LIGHTEN_FACTOR = 0.35   # How much to lighten the top (0.0 = no change, 1.0 = white)
BOTTOM_DARKEN_FACTOR = 0.45 # How much to darken the bottom (0.0 = no change, 1.0 = black)


# ──────────────────────────────────────────────────────────────────────
# Oklab color space (perceptually uniform, D65 white point)
# Reference: https://bottosson.github.io/posts/oklab/
# ──────────────────────────────────────────────────────────────────────

def _srgb_to_linear(rgb: np.ndarray) -> np.ndarray:
    """sRGB [0,1] → linear RGB [0,1]. Vectorized for (..., 3)."""
    mask = rgb <= 0.04045
    return np.where(mask, rgb / 12.92, ((rgb + 0.055) / 1.055) ** 2.4)


def _linear_to_srgb(linear: np.ndarray) -> np.ndarray:
    """Linear RGB [0,1] → sRGB [0,1]. Vectorized for (..., 3)."""
    linear = np.maximum(linear, 0.0)
    mask = linear <= 0.0031308
    return np.where(mask, linear * 12.92, 1.055 * (linear ** (1 / 2.4)) - 0.055)


# Linear RGB (D65) → LMS (cone responses) - from Oklab paper
_LINEAR_RGB_TO_LMS = np.array([
    [0.4122214708, 0.5363325363, 0.0514459929],
    [0.2119034982, 0.6806995451, 0.1073969566],
    [0.0883024619, 0.2817188376, 0.6299787005],
], dtype=np.float32)

# LMS → Linear RGB (D65) - inverse
_LMS_TO_LINEAR_RGB = np.array([
    [4.0767416621, -3.3077115913, 0.2309699292],
    [-1.2684380046, 2.6097574011, -0.3413193965],
    [-0.0041960863, -0.7034186147, 1.7076147010],
], dtype=np.float32)

# LMS (cube root) → Oklab
_LMS_CUBEROOT_TO_OKLAB = np.array([
    [0.2104542553, 0.7936177850, -0.0040720468],
    [1.9779984951, -2.4285922050, 0.4505937099],
    [0.0259040371, 0.7827717662, -0.8086757660],
], dtype=np.float32)

# Oklab → LMS (cube root) - inverse
_OKLAB_TO_LMS_CUBEROOT = np.array([
    [1.0000000000, 0.3963377774, 0.2158037573],
    [1.0000000000, -0.1055613458, -0.0638541728],
    [1.0000000000, -0.0894841775, -1.2914855480],
], dtype=np.float32)


def srgb_to_oklab(rgb_0_255: np.ndarray) -> np.ndarray:
    """sRGB uint8/float [0,255] → Oklab float32. Input is RGB order."""
    rgb = rgb_0_255.astype(np.float32) / 255.0
    linear = _srgb_to_linear(rgb)
    lms = linear @ _LINEAR_RGB_TO_LMS.T
    lms_cbrt = np.cbrt(np.maximum(lms, 0))
    return (lms_cbrt @ _LMS_CUBEROOT_TO_OKLAB.T).astype(np.float32)


def oklab_to_srgb(oklab: np.ndarray) -> np.ndarray:
    """Oklab float32 → sRGB float32 [0,255]. Output is RGB order."""
    lms_cbrt = oklab @ _OKLAB_TO_LMS_CUBEROOT.T
    lms = lms_cbrt ** 3
    linear = lms @ _LMS_TO_LINEAR_RGB.T
    rgb = _linear_to_srgb(linear)
    return np.clip(rgb * 255.0, 0.0, 255.0).astype(np.float32)


def expand_gradient_range(top_bgr: tuple, bottom_bgr: tuple) -> tuple[tuple, tuple]:
    """
    Expand gradient range: lighten top toward white, darken bottom toward black.

    Uses Oklab lightness (L) for perceptually correct expansion.

    Returns: (expanded_top_bgr, expanded_bottom_bgr)
    """
    # Convert BGR → RGB → Oklab
    top_rgb = np.array([top_bgr[2], top_bgr[1], top_bgr[0]], dtype=np.float32)
    bot_rgb = np.array([bottom_bgr[2], bottom_bgr[1], bottom_bgr[0]], dtype=np.float32)

    top_oklab = srgb_to_oklab(top_rgb)   # [L, a, b]
    bot_oklab = srgb_to_oklab(bot_rgb)

    # Expand in Oklab: lighten top (increase L), darken bottom (decrease L)
    # L ranges 0-1 in Oklab
    top_L_expanded = min(1.0, top_oklab[0] + TOP_LIGHTEN_FACTOR * (1.0 - top_oklab[0]))
    bot_L_expanded = max(0.0, bot_oklab[0] - BOTTOM_DARKEN_FACTOR * bot_oklab[0])

    expanded_top_oklab = np.array([top_L_expanded, top_oklab[1], top_oklab[2]], dtype=np.float32)
    expanded_bot_oklab = np.array([bot_L_expanded, bot_oklab[1], bot_oklab[2]], dtype=np.float32)

    # Convert back to sRGB
    expanded_top_rgb = oklab_to_srgb(expanded_top_oklab)
    expanded_bot_rgb = oklab_to_srgb(expanded_bot_oklab)

    # Convert RGB → BGR
    expanded_top_bgr = tuple(expanded_top_rgb[::-1].astype(int))
    expanded_bot_bgr = tuple(expanded_bot_rgb[::-1].astype(int))

    return expanded_top_bgr, expanded_bot_bgr


# ──────────────────────────────────────────────────────────────────────
# Gradient Generation (no vignette)
# ──────────────────────────────────────────────────────────────────────

def generate_gradient_oklab(top_bgr: tuple, bottom_bgr: tuple) -> np.ndarray:
    """
    Generate vertical gradient in Oklab space for perceptual correctness.

    Args:
        top_bgr: BGR tuple (0..255) for top color
        bottom_bgr: BGR tuple (0..255) for bottom color

    Returns:
        Float32 array (H, W, 3) in BGR [0, 255] - ready for 16-bit PNG
    """
    # Convert BGR → RGB
    top_rgb = np.array([top_bgr[2], top_bgr[1], top_bgr[0]], dtype=np.float32)
    bot_rgb = np.array([bottom_bgr[2], bottom_bgr[1], bottom_bgr[0]], dtype=np.float32)

    top_oklab = srgb_to_oklab(top_rgb)
    bot_oklab = srgb_to_oklab(bot_rgb)

    # Interpolate in Oklab (perceptually uniform)
    t = np.linspace(0, 1, H, dtype=np.float32).reshape(H, 1, 1)

    grad_oklab = top_oklab.reshape(1, 1, 3) * (1 - t) + bot_oklab.reshape(1, 1, 3) * t
    grad_oklab = np.tile(grad_oklab, (1, W, 1))

    # Convert back to sRGB float32 [0, 255]
    grad_srgb = oklab_to_srgb(grad_oklab)

    # Convert RGB → BGR for OpenCV
    return grad_srgb[:, :, ::-1]


def save_16bit_png(path: Path, frame_bgr_float32: np.ndarray) -> None:
    """Save float32 BGR [0, 255] as 16-bit PNG (48-bit RGB)."""
    frame_rgb = frame_bgr_float32[:, :, ::-1]  # BGR → RGB
    frame_16 = np.clip(frame_rgb * 257.0, 0, 65535).astype(np.uint16)
    cv2.imwrite(str(path), frame_16, [cv2.IMWRITE_PNG_COMPRESSION, 1])


# ──────────────────────────────────────────────────────────────────────
# Main
# ──────────────────────────────────────────────────────────────────────

def main() -> int:
    print(f"Generating ultra-high-quality gradients into {OUT_DIR}")
    print(f"  Resolution: {W}×{H}")
    print(f"  Color space: Oklab perceptual interpolation")
    print(f"  Range expansion: Top lighten={TOP_LIGHTEN_FACTOR}, Bottom darken={BOTTOM_DARKEN_FACTOR}")
    print(f"  No vignette")
    print(f"  Output: 16-bit PNG (48-bit RGB)")
    print()

    OUT_DIR.mkdir(parents=True, exist_ok=True)

    # Get the 5 palettes from neon_prism (first style in STYLE_PALETTES)
    palettes = STYLE_PALETTES["neon_prism"]

    print(f"Generating {len(palettes)} palette gradients...")

    for palette in palettes:
        top = palette.bg_top    # BGR
        bottom = palette.bg_bottom  # BGR

        # Expand the gradient range
        expanded_top, expanded_bottom = expand_gradient_range(top, bottom)

        print(f"  {palette.id}.png")
        print(f"      Original:    Top={top}, Bottom={bottom}")
        print(f"      Expanded:    Top={expanded_top}, Bottom={expanded_bottom}")

        frame = generate_gradient_oklab(expanded_top, expanded_bottom)

        out_path = OUT_DIR / f"{palette.id}.png"
        save_16bit_png(out_path, frame)

        # Verify
        verify = cv2.imread(str(out_path), cv2.IMREAD_UNCHANGED)
        print(f"      Saved: {verify.shape}, dtype={verify.dtype}, range=[{verify.min()}, {verify.max()}]")

    print(f"\nDone! Generated {len(palettes)} ultra-high-quality 16-bit gradient images.")
    return 0


if __name__ == "__main__":
    exit(main())