"""
Game-mode constants — kept separate from the main tuner constants.

Colours that duplicate the tuner palette are re-exported from ``constants``
so there is a single source of truth for each hex value.
"""
from MyShittyNoteAnalyser.constants import (COLOR_BG_DARKER, COLOR_FG_LABEL,
                                            COLOR_ACCENT_PERFECT, COLOR_ACCENT_BAD)

# ── Display modes ──────────────────────────────────────────────────
GAME_DISPLAY_OPTIONS = ["Letter (Solfege)", "Staff Notation"]
DEFAULT_DISPLAY_LETTER = True
DEFAULT_DISPLAY_STAFF = False

# ── Game modes ─────────────────────────────────────────────────────
GAME_MODES = ["Random", "Scale"]
DEFAULT_GAME_MODE = "Random"

# ── Scale direction (used when game mode is "Scale") ───────────────
SCALE_DIRECTIONS = ["Ascending", "Descending", "Random"]
DEFAULT_SCALE_DIRECTION = "Ascending"

# ── Range categories ───────────────────────────────────────────────
# These correspond to the keys in INSTRUMENT_RANGE_CATEGORIES.
RANGE_CATEGORY_LABELS = {
    "most_played":        "Most played",
    "rarely_played":      "Rarely played",
    "very_rarely_played": "Very rarely played",
}
# Display order (left to right in settings panel).
RANGE_CATEGORY_ORDER = ("most_played", "rarely_played", "very_rarely_played")

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

# ── Staff layout (pixel values) ────────────────────────────────────
STAFF_LINE_COUNT = 5
STAFF_LINE_SPACING = 12         # px between consecutive staff lines
STAFF_TOTAL_HEIGHT = (STAFF_LINE_COUNT - 1) * STAFF_LINE_SPACING  # 48 px
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
# Where a game colour matches a tuner constant, the tuner constant is
# the canonical source; game-specific aliases are kept for readability.
GAME_BG = COLOR_BG_DARKER              # "#1e1e1e"
GAME_STAFF_LINE = "#888888"
GAME_NOTEHEAD = COLOR_ACCENT_PERFECT   # "#00ff88" — bright green fill
GAME_NOTEHEAD_OUTLINE = "#ffffff"
GAME_HOLD_PROGRESS = COLOR_ACCENT_PERFECT  # "#00ff88" — filling bar
GAME_HOLD_EMPTY = "#444444"                # empty bar bg
GAME_HOLD_TEXT = COLOR_FG_LABEL            # "#cccccc"
GAME_OVERLAY_BG = "rgba(0, 0, 0, 0.85)"
GAME_TARGET_TEXT = "#ffffff"               # target note in letter mode
GAME_CORRECT = COLOR_ACCENT_PERFECT        # "#00ff88"
GAME_WRONG = COLOR_ACCENT_BAD             # "#ff5555"
GAME_PITCH_HINT = "#ffcc00"               # amber/yellow — current pitch dot + arrow
GAME_FEEDBACK_BG = "#222222"
GAME_STATS = COLOR_FG_LABEL               # "#cccccc"

# ── Game UI layout (pixel values) ──────────────────────────────────
GAME_TOP_BAR_HEIGHT = 28
GAME_FEEDBACK_HEIGHT = 30
GAME_HOLD_BAR_HEIGHT = 16
GAME_CURRENT_NOTE_HEIGHT = 22
GAME_OVERLAY_WIDTH = 400
GAME_OVERLAY_HEIGHT = 220
GAME_OVERLAY_CORNER_RADIUS = 12

