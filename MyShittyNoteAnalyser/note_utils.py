"""Shared note-display helper functions used by both tuner and game panels."""

import os

from MyShittyNoteAnalyser.constants import (NOTE_SHARP_SOLFEGE, NOTE_SHARP_LETTER,
                                            NOTE_FLAT_SOLFEGE, NOTE_FLAT_LETTER,
                                            COLOR_ACCENT_PERFECT, COLOR_ACCENT_NICE,
                                            COLOR_ACCENT_GOOD, COLOR_ACCENT_BAD)


# ── resource path ────────────────────────────────────────────────────

def resource_path(filename: str) -> str:
    """Get the absolute path to a resource file."""
    return os.path.join(os.path.dirname(os.path.abspath(__file__)),
                        "resources", filename)


# ── MIDI ↔ note name conversion ─────────────────────────────────────

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


def midi_to_note_label(midi: int, use_sharps: bool) -> str:
    """Return a user-friendly combined label, e.g. 60 → 'Do (C4)'."""
    solf, letter = midi_to_note_text(midi, use_sharps)
    return f"{solf} ({letter})"


def midi_to_letter_octave(midi: int, use_sharps: bool) -> str:
    """Return letter+octave only, e.g. 60 → 'C4'."""
    _, letter = midi_to_note_text(midi, use_sharps)
    return letter


# ── cents → accuracy color ──────────────────────────────────────────

def cents_to_color(cents: float) -> str:
    """Map a cents-deviation to an accuracy colour constant."""
    a = abs(cents)
    if a < 5:
        return COLOR_ACCENT_PERFECT
    if a < 20:
        return COLOR_ACCENT_NICE
    if a < 50:
        return COLOR_ACCENT_GOOD
    return COLOR_ACCENT_BAD


def cents_to_accuracy(cents: float) -> tuple[str, str]:
    """Return (label, color_hex) for a cents deviation, e.g. ('Perfect', '#00ff88')."""
    a = abs(cents)
    if a < 5:
        return "Perfect", COLOR_ACCENT_PERFECT
    if a < 20:
        return "Nice", COLOR_ACCENT_NICE
    if a < 50:
        return "Good", COLOR_ACCENT_GOOD
    return "Bad", COLOR_ACCENT_BAD


# ── MIDI ↔ pixel position ───────────────────────────────────────────

def midi_to_y(midi: float, min_midi: int, max_midi: int,
              top_y: float, bottom_y: float) -> float:
    """Map a MIDI value (float or int) to a vertical pixel position.

    ``top_y`` is the canvas coordinate of the *highest* MIDI,
    ``bottom_y`` is the canvas coordinate of the *lowest* MIDI.
    """
    if max_midi <= min_midi:
        return bottom_y
    frac = (midi - min_midi) / (max_midi - min_midi)
    return bottom_y - frac * (bottom_y - top_y)


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


# ── ledger lines ────────────────────────────────────────────────────

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


# ── buffer display formatting ───────────────────────────────────────

def format_buffer_display(buf_size: int, sample_rate: int) -> str:
    """Return a standardised buffer-size display string.

    Example: ``format_buffer_display(2048, 44100)`` → ``"2048  (min 22 Hz)"``.
    """
    return f"{buf_size}  (min {sample_rate / buf_size:.0f} Hz)"
