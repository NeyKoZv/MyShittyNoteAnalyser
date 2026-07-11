"""
Instrument ↔ notation mapping and helper functions.

Encapsulates the relationships between an instrument and its
associated clef, written range, and default notation choice.
"""
from MyShittyNoteAnalyser.constants import DEFAULT_NOTATION, DEFAULT_NOTATION_BY_INSTRUMENT

# ── Clef per instrument ─────────────────────────────────────────────
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


# ── Helper functions ────────────────────────────────────────────────

def get_clef_for_instrument(instrument_name: str) -> str:
    """Return the staff clef for *instrument_name*.

    Falls back to ``DEFAULT_CLEF`` ("treble") for unknown instruments.
    """
    return INSTRUMENT_CLEF_MAP.get(instrument_name, DEFAULT_CLEF)


def get_default_notation_for_instrument(instrument_name: str) -> str:
    """Return the recommended notation ("Sharps" or "Flats") for *instrument_name*.

    Falls back to ``DEFAULT_NOTATION`` from the global constants.
    """
    return DEFAULT_NOTATION_BY_INSTRUMENT.get(instrument_name, DEFAULT_NOTATION)


def get_written_range_for_instrument(instrument_name: str) -> tuple[int, int]:
    """Return the (min_midi, max_midi) written range for *instrument_name*.

    Falls back to (21, 108) — the full piano range — for unknown instruments.
    """
    return INSTRUMENT_WRITTEN_RANGE.get(instrument_name, (21, 108))


def resolve_notation_on_instrument_change(instrument_name: str) -> str:
    """Convenience: return the notation that should be auto-selected
    when the user picks *instrument_name*.

    Currently delegates to ``get_default_notation_for_instrument``,
    but exists as a single entry-point so future logic (e.g. user
    preference persistence) can be added here without touching UI code.
    """
    return get_default_notation_for_instrument(instrument_name)
