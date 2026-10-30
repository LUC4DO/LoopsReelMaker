"""Central palette registry — all 25 palettes defined in one place."""

from .base import Palette

# Neon Prism (5)
CYBER_MAGENTA = Palette(
    "cyber_magenta", "Cyber Magenta",
    bg_top=(34, 0, 34), bg_bottom=(8, 0, 17),
    primary=(255, 0, 220), secondary=(180, 80, 255),
    accent=(0, 255, 240), text=(255, 240, 255), glow=(255, 100, 255),
)

ELECTRIC_CYAN = Palette(
    "electric_cyan", "Electric Cyan",
    bg_top=(25, 17, 0), bg_bottom=(8, 4, 0),
    primary=(255, 230, 0), secondary=(255, 160, 40),
    accent=(80, 255, 255), text=(240, 255, 255), glow=(255, 255, 120),
)

ACID_LIME = Palette(
    "acid_lime", "Acid Lime",
    bg_top=(4, 21, 4), bg_bottom=(0, 6, 0),
    primary=(40, 255, 80), secondary=(0, 200, 120),
    accent=(200, 255, 0), text=(230, 255, 230), glow=(100, 255, 100),
)

HOT_AMBER = Palette(
    "hot_amber", "Hot Amber",
    bg_top=(0, 12, 34), bg_bottom=(0, 4, 12),
    primary=(0, 160, 255), secondary=(0, 90, 255),
    accent=(40, 220, 255), text=(255, 245, 230), glow=(0, 200, 255),
)

ULTRA_VIOLET = Palette(
    "ultra_violet", "Ultra Violet",
    bg_top=(42, 0, 25), bg_bottom=(12, 0, 8),
    primary=(255, 60, 180), secondary=(200, 40, 255),
    accent=(255, 180, 255), text=(255, 230, 255), glow=(255, 120, 255),
)

# CRT Retro Wave (5)
SUNSET_HORIZON = Palette(
    "sunset_horizon", "Sunset Horizon",
    bg_top=(51, 17, 68), bg_bottom=(17, 4, 8),
    primary=(0, 120, 255), secondary=(180, 0, 255),
    accent=(80, 220, 255), text=(255, 240, 255), glow=(100, 180, 255),
)

NIGHT_DRIVE = Palette(
    "night_drive", "Night Drive",
    bg_top=(34, 8, 4), bg_bottom=(8, 0, 0),
    primary=(255, 180, 40), secondary=(255, 80, 120),
    accent=(200, 255, 255), text=(230, 250, 255), glow=(255, 200, 100),
)

MIAMI_VICE = Palette(
    "miami_vice", "Miami Vice",
    bg_top=(59, 17, 42), bg_bottom=(21, 4, 12),
    primary=(255, 100, 255), secondary=(255, 220, 80),
    accent=(100, 255, 220), text=(255, 245, 255), glow=(255, 150, 255),
)

PHOSPHOR_GREEN = Palette(
    "phosphor_green", "Phosphor Green",
    bg_top=(6, 17, 4), bg_bottom=(1, 4, 0),
    primary=(40, 255, 60), secondary=(20, 180, 40),
    accent=(180, 255, 180), text=(200, 255, 200), glow=(80, 255, 100),
)

VAPOR_PINK = Palette(
    "vapor_pink", "Vapor Pink",
    bg_top=(42, 12, 34), bg_bottom=(12, 4, 17),
    primary=(255, 120, 220), secondary=(200, 180, 255),
    accent=(255, 200, 255), text=(255, 240, 255), glow=(255, 160, 255),
)

# Orbital Pulse (5)
DEEP_OCEAN = Palette(
    "deep_ocean", "Deep Ocean",
    bg_top=(34, 12, 4), bg_bottom=(8, 4, 0),
    primary=(255, 180, 40), secondary=(200, 120, 20),
    accent=(255, 220, 120), text=(240, 250, 255), glow=(255, 200, 100),
)

SOFT_AURORA = Palette(
    "soft_aurora", "Soft Aurora",
    bg_top=(25, 17, 8), bg_bottom=(8, 6, 4),
    primary=(180, 255, 120), secondary=(255, 160, 200),
    accent=(120, 255, 220), text=(245, 255, 250), glow=(200, 255, 200),
)

GOLD_PULSE = Palette(
    "gold_pulse", "Gold Pulse",
    bg_top=(12, 17, 29), bg_bottom=(4, 6, 10),
    primary=(40, 190, 255), secondary=(20, 140, 220),
    accent=(120, 230, 255), text=(255, 250, 240), glow=(80, 210, 255),
)

ROSE_QUARTZ = Palette(
    "rose_quartz", "Rose Quartz",
    bg_top=(29, 12, 25), bg_bottom=(10, 4, 8),
    primary=(200, 140, 255), secondary=(255, 160, 200),
    accent=(255, 200, 230), text=(255, 240, 250), glow=(230, 180, 255),
)

MONO_EMBER = Palette(
    "mono_ember", "Mono Ember",
    bg_top=(15, 15, 15), bg_bottom=(4, 4, 4),
    primary=(200, 200, 200), secondary=(140, 140, 140),
    accent=(255, 180, 80), text=(245, 245, 245), glow=(255, 220, 180),
)

# Glitch Tunnel (5)
RAVE_RGB = Palette(
    "rave_rgb", "Rave RGB",
    bg_top=(8, 0, 0), bg_bottom=(0, 0, 8),
    primary=(0, 0, 255), secondary=(0, 255, 0),
    accent=(255, 0, 255), text=(255, 255, 255), glow=(255, 255, 0),
)

TOXIC_WASTE = Palette(
    "toxic_waste", "Toxic Waste",
    bg_top=(4, 17, 4), bg_bottom=(0, 4, 0),
    primary=(0, 255, 80), secondary=(0, 200, 255),
    accent=(40, 255, 40), text=(220, 255, 220), glow=(100, 255, 0),
)

ICE_BREAKER = Palette(
    "ice_breaker", "Ice Breaker",
    bg_top=(34, 17, 4), bg_bottom=(12, 4, 0),
    primary=(255, 220, 120), secondary=(255, 180, 60),
    accent=(200, 255, 255), text=(240, 250, 255), glow=(255, 255, 200),
)

BLOOD_NEON = Palette(
    "blood_neon", "Blood Neon",
    bg_top=(4, 0, 17), bg_bottom=(0, 0, 4),
    primary=(40, 40, 255), secondary=(0, 0, 180),
    accent=(80, 120, 255), text=(255, 230, 230), glow=(100, 80, 255),
)

MONOCHROME_STATIC = Palette(
    "monochrome_static", "Monochrome Static",
    bg_top=(17, 17, 17), bg_bottom=(0, 0, 0),
    primary=(220, 220, 220), secondary=(140, 140, 140),
    accent=(255, 255, 255), text=(245, 245, 245), glow=(200, 200, 200),
)

# LoFi Drift (5)
STUDY_LAMP = Palette(
    "study_lamp", "Study Lamp",
    bg_top=(38, 46, 59), bg_bottom=(21, 25, 34),
    primary=(120, 170, 220), secondary=(90, 130, 180),
    accent=(160, 200, 240), text=(245, 240, 230), glow=(180, 200, 220),
)

RAIN_WINDOW = Palette(
    "rain_window", "Rain Window",
    bg_top=(42, 34, 29), bg_bottom=(21, 17, 15),
    primary=(180, 160, 140), secondary=(140, 130, 120),
    accent=(200, 190, 180), text=(235, 235, 240), glow=(190, 185, 180),
)

CAFE_SEPIA = Palette(
    "cafe_sepia", "Cafe Sepia",
    bg_top=(34, 46, 59), bg_bottom=(17, 25, 34),
    primary=(80, 140, 200), secondary=(60, 100, 150),
    accent=(120, 180, 220), text=(245, 235, 220), glow=(140, 180, 210),
)

PASTEL_DUSK = Palette(
    "pastel_dusk", "Pastel Dusk",
    bg_top=(59, 42, 51), bg_bottom=(29, 21, 29),
    primary=(200, 160, 220), secondary=(160, 180, 230),
    accent=(220, 190, 230), text=(250, 245, 250), glow=(210, 180, 230),
)

MIDNIGHT_TEA = Palette(
    "midnight_tea", "Midnight Tea",
    bg_top=(29, 21, 17), bg_bottom=(10, 6, 5),
    primary=(140, 120, 100), secondary=(100, 90, 80),
    accent=(180, 160, 140), text=(230, 225, 220), glow=(160, 140, 120),
)


# Convenience mapping: style_id -> list of palette objects
STYLE_PALETTES = {
    "neon_prism": [
        CYBER_MAGENTA, ELECTRIC_CYAN, ACID_LIME, HOT_AMBER, ULTRA_VIOLET,
    ],
    "crt_retro": [
        SUNSET_HORIZON, NIGHT_DRIVE, MIAMI_VICE, PHOSPHOR_GREEN, VAPOR_PINK,
    ],
    "orbital_pulse": [
        DEEP_OCEAN, SOFT_AURORA, GOLD_PULSE, ROSE_QUARTZ, MONO_EMBER,
    ],
    "glitch_tunnel": [
        RAVE_RGB, TOXIC_WASTE, ICE_BREAKER, BLOOD_NEON, MONOCHROME_STATIC,
    ],
    "lofi_drift": [
        STUDY_LAMP, RAIN_WINDOW, CAFE_SEPIA, PASTEL_DUSK, MIDNIGHT_TEA,
    ],
}


def get_palette(palette_id: str) -> Palette | None:
    """Look up a single palette by its id across all styles."""
    for palettes in STYLE_PALETTES.values():
        for p in palettes:
            if p.id == palette_id:
                return p
    return None


def get_style_palettes(style_id: str) -> list[Palette]:
    """Return the list of palettes for a given style."""
    return STYLE_PALETTES.get(style_id, [])