"""The Strategist — brand design tokens (single source of truth).

Black & orange, flat and analytical. See DESIGN.md for the rules behind these.
"""

COLORS = {
    # surfaces
    "bg": "#000000",          # pure black canvas, no lighting
    "bg_raised": "#121519",   # cards, panels
    "grid": "#1E2328",        # hairlines, axes, gridlines
    # maps
    "land": "#1B262C",        # dark slate land
    "land_edge": "#2C3A42",   # borders / coastlines
    "water": "#0A0B0D",       # water = canvas
    # accents
    "orange": "#F28C28",      # brand accent: the point of the frame
    "orange_dim": "#7A4A1C",  # secondary orange (inactive, fills)
    "red": "#D9573B",         # adversary / danger / negative
    "blue": "#4EA8DE",        # the "other side" / contrast (use sparingly)
    # text
    "text": "#ECE9E4",        # primary text (off-white)
    "muted": "#8A9099",       # secondary text
    "faint": "#4A5058",       # tertiary text, sources
}

# role -> (font file stem, size px at 1080 wide)
TYPE = {
    "kicker":   ("Barlow-SemiBold", 26),     # UPPERCASE, tracking 4
    "title":    ("Barlow-SemiBold", 72),
    "subtitle": ("Barlow-Medium", 34),
    "h2":       ("Barlow-SemiBold", 46),
    "label":    ("Barlow-Medium", 34),
    "body":     ("Barlow-Regular", 32),
    "meta":     ("Barlow-Medium", 24),       # sources, legends
    "big":      ("Barlow-SemiBold", 170),    # hero numbers
    "map_city": ("Barlow-Medium", 30),
    "map_area": ("BarlowCondensed-Medium", 40),  # region names on maps
    "caption":  ("Barlow-Bold", 76),         # spoken-word captions in videos
}

# Vertical (Shorts) safe area: keep essential content inside this box.
CANVAS = (1080, 1920)
SAFE = {"left": 70, "right": 1010, "top": 170, "bottom": 1500}

# Production defaults for every episode (voice, pacing).
PRODUCTION = {
    "voice": "am_fenrir",    # Kokoro "Voice 2", unmodified (no pitch shift, EQ or blending)
    "speed": 1.05,           # narration speed
    "lead": 0.45,            # s of silence at the start of each slide before the voice starts
    "tail": 0.75,            # s after the voice ends before the slide's animation timeline ends
    "hold": 2.0,             # extra s each slide stays fully built before switching (reading time)
    "transition_sfx": None,  # sound on slide change (None = silent)
    "sfx_muted": ["whoosh", "whoosh_short", "swoosh"],   # sound effects never used
}
