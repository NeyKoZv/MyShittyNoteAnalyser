"""
Game-mode constants — kept separate from the main tuner constants.
"""

from constants import INSTRUMENTS, NOTE_SHARP_SOLFEGE, NOTE_SHARP_LETTER, \
    NOTE_FLAT_SOLFEGE, NOTE_FLAT_LETTER

# ── Display modes ──────────────────────────────────────────────────
GAME_DISPLAY_MODES = ["Letter (Solfege)", "Staff Notation"]
DEFAULT_DISPLAY_MODE = "Letter (Solfege)"

# ── Game modes ─────────────────────────────────────────────────────
GAME_MODES = ["Random", "Scale"]
DEFAULT_GAME_MODE = "Random"

# ── Scale direction (used when game mode is "Scale") ───────────────
SCALE_DIRECTIONS = ["Ascending", "Descending", "Random"]
DEFAULT_SCALE_DIRECTION = "Ascending"

# ── Game lengths ───────────────────────────────────────────────────
GAME_LENGTHS = ["Endless", "10 notes", "20 notes", "30 notes"]
DEFAULT_GAME_LENGTH = "Endless"

# ── Timing ─────────────────────────────────────────────────────────
HOLD_DURATION_DEFAULT = 1.0          # seconds to hold the correct note
HOLD_DURATION_MIN = 0.5
HOLD_DURATION_MAX = 3.0
HOLD_DURATION_STEP = 0.1
MATCH_TOLERANCE_CENTS = 25           # ± cents to count as a "hit"
SCORE_PER_NOTE = 100

# ── Clef by instrument ─────────────────────────────────────────────
INSTRUMENT_CLEF_MAP = {
    "Concert (C)":      "treble",
    "Bb Clarinet":      "treble",
    "A Clarinet":       "treble",
    "Eb Clarinet":      "treble",
    "Bb Trumpet":       "treble",
    "Alto Sax":         "treble",
    "Tenor Sax":        "treble",
    "French Horn":      "treble",
    "Guitar":           "treble",
    "Bass Guitar":      "bass",
}
DEFAULT_CLEF = "treble"

# ── Written range per instrument (MIDI values) ─────────────────────
# These are the WRITTEN (transposed) ranges a sight-reader sees.
# The game picks target notes from within the instrument's written range.
INSTRUMENT_WRITTEN_RANGE = {
    "Concert (C)":      (52,  96),   # E3  – C7  (conservative piano default)
    "Bb Clarinet":      (52,  96),   # E3  – C7
    "A Clarinet":       (52,  96),   # E3  – C7
    "Eb Clarinet":      (55, 100),   # G3  – E7
    "Bb Trumpet":       (54,  88),   # F#3 – E6
    "Alto Sax":         (58,  89),   # Bb3 – F6
    "Tenor Sax":        (58,  89),   # Bb3 – F6
    "French Horn":      (42,  77),   # F#2 – F5
    "Guitar":           (52,  88),   # E3  – E6
    "Bass Guitar":      (40,  67),   # E2  – G4
}
# ── Default notation per instrument ─────────────────────────────────
# Wind instruments in flat keys (Bb, Eb, F) → Flats
# String instruments in sharp keys (G, D, A, E) → Sharps
# User can override at any time via the notation dropdown.
DEFAULT_NOTATION_BY_INSTRUMENT = {
    "Concert (C)":      "Flats",
    "Bb Clarinet":      "Flats",
    "A Clarinet":       "Flats",
    "Eb Clarinet":      "Flats",
    "Bb Trumpet":       "Flats",
    "Alto Sax":         "Flats",
    "Tenor Sax":        "Flats",
    "French Horn":      "Flats",
    "Guitar":           "Sharps",
    "Bass Guitar":      "Sharps",
}
# ── Staff layout (pixel values) ────────────────────────────────────
STAFF_LINE_COUNT = 5
STAFF_LINE_SPACING = 12         # px between consecutive staff lines
STAFF_MARGIN_TOP = 40           # px above top line
STAFF_MARGIN_BOTTOM = 20        # px below bottom line
NOTEHEAD_WIDTH = 14
NOTEHEAD_HEIGHT = 10
NOTEHEAD_TILT = -12             # degrees (ellipse tilt for oval notehead)
LEDGER_LINE_EXTEND = 6          # px past notehead on each side
CLEF_WIDTH = 48                 # reserved width for clef symbol
CLEF_MARGIN = 10                # px gap between clef and staff lines

# Treble clef reference: bottom line = E4 (MIDI 64)
TREBLE_BOTTOM_LINE_MIDI = 64    # E4
# Bass clef reference: bottom line = G2 (MIDI 43)
BASS_BOTTOM_LINE_MIDI = 43      # G2

# ── Game UI colors ─────────────────────────────────────────────────
GAME_BG = "#1e1e1e"
GAME_STAFF_LINE = "#888888"
GAME_NOTEHEAD = "#00ff88"        # bright green fill for target note
GAME_NOTEHEAD_OUTLINE = "#ffffff"
GAME_HOLD_PROGRESS = "#00ff88"   # filling bar
GAME_HOLD_EMPTY = "#444444"      # empty bar bg
GAME_HOLD_TEXT = "#cccccc"
GAME_OVERLAY_BG = "rgba(0, 0, 0, 0.85)"
GAME_TARGET_TEXT = "#ffffff"     # target note in letter mode
GAME_CORRECT = "#00ff88"
GAME_WRONG = "#ff5555"
GAME_FEEDBACK_BG = "#222222"
GAME_STATS = "#cccccc"

# ── Game UI layout (pixel values) ──────────────────────────────────
GAME_TOP_BAR_HEIGHT = 28
GAME_FEEDBACK_HEIGHT = 30
GAME_HOLD_BAR_HEIGHT = 16
GAME_CURRENT_NOTE_HEIGHT = 22
GAME_OVERLAY_WIDTH = 400
GAME_OVERLAY_HEIGHT = 220
GAME_OVERLAY_CORNER_RADIUS = 12

