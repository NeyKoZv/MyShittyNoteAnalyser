"""Shared note-display helper functions used by both tuner and game panels."""

import os

from constants import (NOTE_SHARP_SOLFEGE, NOTE_SHARP_LETTER,
                       NOTE_FLAT_SOLFEGE, NOTE_FLAT_LETTER)


def resource_path(filename: str) -> str:
    """Get the absolute path to a resource file."""
    return os.path.join(os.path.dirname(os.path.abspath(__file__)),
                        "resources", filename)


def midi_to_note_text(midi: int, use_sharps: bool) -> tuple[str, str]:
    """Return (solfege, letter+octave) for a MIDI note number."""
    idx = midi % 12
    octave = (midi // 12) - 1
    if use_sharps:
        solf = NOTE_SHARP_SOLFEGE[idx]
        letter = f"{NOTE_SHARP_LETTER[idx]}{octave}"
    else:
        solf = NOTE_FLAT_SOLFEGE[idx]
        letter = f"{NOTE_FLAT_LETTER[idx]}{octave}"
    return solf, letter


def midi_to_staff_y(midi: int, bottom_line_midi: int,
                     staff_top_y: float, staff_bottom_y: float) -> float:
    """Convert a MIDI pitch to a y-coordinate on the staff.

    Returns the y position for the center of the notehead (ellipse).
    """
    staff_height = staff_bottom_y - staff_top_y
    # 8 semitones per staff height (bottom line to top line = 8 semitones)
    semitones_per_staff = 8.0
    half_steps = midi - bottom_line_midi
    frac = half_steps / semitones_per_staff
    # staff_bottom_y is bottom line, staff_top_y is top line
    return staff_bottom_y - frac * staff_height


def ledger_lines(midi: int, bottom_line_midi: int) -> list[int]:
    """Return the MIDI values that need ledger lines for a given note.

    A ledger line is drawn for each value divisible by 2 that is outside
    the staff range and at or beyond the note's position.
    """
    staff_bottom = bottom_line_midi
    staff_top = bottom_line_midi + 8  # 5 lines = 4 gaps = 8 semitones
    lines = []
    # Ledger lines below the staff
    below = staff_bottom - 1
    while below >= midi:
        if below % 2 == 0:
            lines.append(below)
        below -= 1
    # Ledger lines above the staff
    above = staff_top + 1
    while above <= midi:
        if above % 2 == 0:
            lines.append(above)
        above += 1
    return lines
