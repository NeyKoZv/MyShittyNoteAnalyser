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

# ── Note name → MIDI helper ───────────────────────────────────────

# Map note letter (with accidental) to semitone index within the octave.
_NOTE_TO_SEMITONE: dict[str, int] = {
    "C":  0,  "C#": 1,  "Db": 1,
    "D":  2,  "D#": 3,  "Eb": 3,
    "E":  4,
    "F":  5,  "F#": 6,  "Gb": 6,
    "G":  7,  "G#": 8,  "Ab": 8,
    "A":  9,  "A#": 10, "Bb": 10,
    "B": 11,
}


def note_name_to_midi(name: str) -> int:
    """Convert a note name like ``"E3"``, ``"F#3"``, or ``"Bb4"`` to its
    MIDI number (0–127).

    Raises ``ValueError`` if the name cannot be parsed.
    """
    name = name.strip()
    # Split the leading letter(s) from the trailing digit(s)
    i = 0
    while i < len(name) and not name[i].isdigit():
        i += 1
    letter_part = name[:i]
    octave_str = name[i:]

    if not letter_part or not octave_str:
        raise ValueError(f"Cannot parse note name: {name!r}")

    semitone = _NOTE_TO_SEMITONE.get(letter_part)
    if semitone is None:
        raise ValueError(f"Unknown note letter: {letter_part!r}")

    try:
        octave = int(octave_str)
    except ValueError:
        raise ValueError(f"Invalid octave in note name: {name!r}")

    return (octave + 1) * 12 + semitone


# ── Written range categories per instrument ────────────────────────
# Each instrument maps category keys ("most_played", "rarely_played",
# "very_rarely_played") to a dict with:
#   - "ranges": list of (low_midi, high_midi) tuples (allows non-contiguous)
#   - "description": human-readable explanation of the register
#
# The game picks target notes from the union of all enabled categories.

INSTRUMENT_RANGE_CATEGORIES: dict[str, dict[str, dict]] = {
    "Concert (C)": {
        "most_played": {
            "ranges": [(52, 84)],  # E3 – C6
            "description": "Conservative piano default — comfortable, well-centred range.",
        },
        "rarely_played": {
            "ranges": [(36, 51), (85, 96)],  # C2–D#3  +  C#6–C7
            "description": "Low bass and high treble — usable but less commonly sight-read.",
        },
        "very_rarely_played": {
            "ranges": [(97, 108)],  # C#7 – C8
            "description": "Extreme top of the keyboard — rarely encountered outside virtuoso repertoire.",
        },
    },
    "Bb Clarinet": {
        "most_played": {
            "ranges": [(52, 84)],  # E3 – C6
            "description": "Chalumeau, throat tones, and clarion registers combined. Effortless, iconic tone; the break occurs around Bb4/B4.",
        },
        "rarely_played": {
            "ranges": [(85, 91)],  # C#6 – G6
            "description": "Lower altissimo. Standard professional altissimo range; used in orchestral excerpts and advanced solos, requires precise voicing.",
        },
        "very_rarely_played": {
            "ranges": [(92, 96)],  # G#6 – C7
            "description": "Upper/extreme altissimo. Rare, unstable intonation, mostly contemporary solo literature.",
        },
    },
    "A Clarinet": {
        "most_played": {
            "ranges": [(52, 84)],  # E3 – C6
            "description": "Same written range and register structure as Bb clarinet; sounds slightly darker.",
        },
        "rarely_played": {
            "ranges": [(85, 91)],  # C#6 – G6
            "description": "Lower altissimo; professional altissimo range.",
        },
        "very_rarely_played": {
            "ranges": [(92, 96)],  # G#6 – C7
            "description": "Extreme altissimo; rarely called for due to unstable intonation.",
        },
    },
    "Eb Clarinet": {
        "most_played": {
            "ranges": [(52, 84)],  # E3 – C6
            "description": "Same written register structure as Bb/A clarinet (shared Boehm fingering system). Bright and piercing due to transposition, but well-controlled.",
        },
        "rarely_played": {
            "ranges": [(85, 91)],  # C#6 – G6
            "description": "Lower altissimo. Requires very firm embouchure; used in orchestral solos.",
        },
        "very_rarely_played": {
            "ranges": [(92, 96)],  # G#6 – C7
            "description": "Sopranino altissimo. Extremely shrill and difficult to tune.",
        },
    },
    "Bb Trumpet": {
        "most_played": {
            "ranges": [(54, 84)],  # F#3 – C6
            "description": "The 'High C' register. Standard orchestral and big band writing.",
        },
        "rarely_played": {
            "ranges": [(85, 88)],  # C#6 – E6
            "description": "Double high range. Requires controlled air; used in lead jazz and solos.",
        },
        "very_rarely_played": {
            "ranges": [(89, 91)],  # F6 – G6
            "description": "Triple high range. Only for extreme lead trumpet or contemporary soloists.",
        },
    },
    "Alto Sax": {
        "most_played": {
            "ranges": [(58, 90)],  # Bb3 – F#6
            "description": "Standard saxophone range using regular fingerings. Great tone throughout.",
        },
        "rarely_played": {
            "ranges": [(91, 93)],  # G6 – A6
            "description": "Lower altissimo register. Used in advanced jazz and classical solos.",
        },
        "very_rarely_played": {
            "ranges": [(94, 98)],  # Bb6 – D7
            "description": "Extreme altissimo. Fingered with overtones; requires special technique.",
        },
    },
    "Tenor Sax": {
        "most_played": {
            "ranges": [(58, 90)],  # Bb3 – F#6
            "description": "Standard tenor range using regular fingerings. Warm, rich, and powerful.",
        },
        "rarely_played": {
            "ranges": [(91, 93)],  # G6 – A6
            "description": "Lower altissimo. Used in jazz solos and modern classical.",
        },
        "very_rarely_played": {
            "ranges": [(94, 98)],  # Bb6 – D7
            "description": "Extreme altissimo. Very thin tone; rarely written.",
        },
    },
    "French Horn": {
        "most_played": {
            "ranges": [(55, 79)],  # G3 – G5
            "description": "The 'money' register. Effortless, mellow, and controlled.",
        },
        "rarely_played": {
            "ranges": [(48, 54), (80, 84)],  # C3–F#3  +  G#5–C6
            "description": "Low range (dark but requires firm lips) and high range (virtuosic orchestral excerpts).",
        },
        "very_rarely_played": {
            "ranges": [(42, 47), (85, 89)],  # F#2–B2  +  C#6–F6
            "description": "Pedal/low bass (extremely hard to project) and extreme high (only in 20th-century solo works).",
        },
    },
    "Guitar": {
        "most_played": {
            "ranges": [(52, 83)],  # E3 – B5
            "description": "Up to the 12th fret. Best tone and easiest fingerings.",
        },
        "rarely_played": {
            "ranges": [(84, 88)],  # C6 – E6
            "description": "Upper frets (13th-24th). Requires precise left-hand positioning.",
        },
        "very_rarely_played": {
            "ranges": [(89, 91)],  # F6 – G6
            "description": "Absolute top of the 24-fret neck. Thin tone; usually avoided.",
        },
    },
    "Bass Guitar": {
        "most_played": {
            "ranges": [(40, 67)],  # E2 – G4
            "description": "Up to the 12th fret. Full, punchy bass tone.",
        },
        "rarely_played": {
            "ranges": [(68, 72)],  # G#4 – C5
            "description": "High register on the G-string. Useful for solos.",
        },
        "very_rarely_played": {
            "ranges": [(73, 76)],  # C#5 – E5
            "description": "Extreme high frets. Very thin and lacks fundamental bass weight.",
        },
    },
}

# Standard range-category keys, ordered from easiest to hardest.
RANGE_CATEGORY_KEYS = ("most_played", "rarely_played", "very_rarely_played")

# Default enabled categories when no user preference is set.
DEFAULT_ENABLED_CATEGORIES = {"most_played"}


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


def get_range_categories_for_instrument(
    instrument_name: str,
) -> dict[str, dict]:
    """Return the full range-category dict for *instrument_name*.

    Falls back to the "Concert (C)" categories for unknown instruments.
    """
    return INSTRUMENT_RANGE_CATEGORIES.get(
        instrument_name,
        INSTRUMENT_RANGE_CATEGORIES["Concert (C)"],
    )


def get_midi_notes_for_categories(
    instrument_name: str,
    enabled_categories: set[str] | None = None,
) -> list[int]:
    """Return a sorted, deduplicated list of MIDI note numbers available
    for the given *instrument_name* across the *enabled_categories*.

    If *enabled_categories* is ``None`` or empty, ``"most_played"`` is used.
    """
    if not enabled_categories:
        enabled_categories = DEFAULT_ENABLED_CATEGORIES

    cats = get_range_categories_for_instrument(instrument_name)
    notes: set[int] = set()
    for key in enabled_categories:
        cat = cats.get(key)
        if cat is None:
            continue
        for low, high in cat.get("ranges", []):
            notes.update(range(low, high + 1))
    return sorted(notes)


def get_written_range_for_instrument(instrument_name: str) -> tuple[int, int]:
    """Return the (min_midi, max_midi) covering the *full* written range
    for *instrument_name* (union of all categories).

    Falls back to (21, 108) — the full piano range — for unknown instruments.

    .. deprecated::
        Prefer :func:`get_midi_notes_for_categories` for game note selection.
        This function is kept for backward compatibility.
    """
    all_notes = get_midi_notes_for_categories(
        instrument_name,
        enabled_categories=set(RANGE_CATEGORY_KEYS),
    )
    if not all_notes:
        return (21, 108)
    return (all_notes[0], all_notes[-1])


def resolve_notation_on_instrument_change(instrument_name: str) -> str:
    """Convenience: return the notation that should be auto-selected
    when the user picks *instrument_name*.

    Currently delegates to ``get_default_notation_for_instrument``,
    but exists as a single entry-point so future logic (e.g. user
    preference persistence) can be added here without touching UI code.
    """
    return get_default_notation_for_instrument(instrument_name)
