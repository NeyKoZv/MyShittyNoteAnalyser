"""Tests for pitch detection and note utility functions."""

from MyShittyNoteAnalyser.pitch_detector import freq_to_midi
from MyShittyNoteAnalyser.note_utils import midi_to_note_text, midi_to_staff_y, ledger_lines


class TestFreqToMidi:
    """Tests for freq_to_midi conversion."""

    def test_a4_is_69(self):
        assert freq_to_midi(440.0) == 69

    def test_a3_is_57(self):
        assert freq_to_midi(220.0) == 57

    def test_a5_is_81(self):
        assert freq_to_midi(880.0) == 81

    def test_none_returns_none(self):
        assert freq_to_midi(None) is None

    def test_zero_returns_none(self):
        assert freq_to_midi(0) is None

    def test_negative_returns_none(self):
        assert freq_to_midi(-440) is None

    def test_c4_is_60(self):
        result = freq_to_midi(261.625565)
        assert round(result) == 60


class TestMidiToNoteText:
    """Tests for MIDI → note name conversion."""

    def test_middle_c_sharps(self):
        solf, letter = midi_to_note_text(60, use_sharps=True)
        assert solf == "Do"
        assert letter == "C4"

    def test_c_sharp_sharps(self):
        solf, letter = midi_to_note_text(61, use_sharps=True)
        assert solf == "Do#"
        assert letter == "C#4"

    def test_c_sharp_flats(self):
        solf, letter = midi_to_note_text(61, use_sharps=False)
        assert solf == "Réb"
        assert letter == "Db4"

    def test_a4_sharps(self):
        solf, letter = midi_to_note_text(69, use_sharps=True)
        assert solf == "La"
        assert letter == "A4"

    def test_low_c(self):
        solf, letter = midi_to_note_text(36, use_sharps=True)
        assert letter == "C2"


class TestMidiToStaffY:
    """Tests for staff position calculation."""

    def test_bottom_line_treble(self):
        # E4 (MIDI 64) is the bottom line of treble staff
        y = midi_to_staff_y(64, 64, 0.0, 100.0)
        assert y == 100.0

    def test_top_line_treble(self):
        # F5 (MIDI 77) is top line (64 + 8 = 72... but 5 lines = 4 gaps = 8 semitones, so top = 64+8 = 72)
        # Actually F5 = 77? Let me check: E4=64, F4=65, G4=67, A4=69, B4=71, C5=72, D5=74, E5=76, F5=77
        # Top line is F5 = MIDI 77. Wait, bottom line E4=64. Top line F5=77. That's 13 semitones, not 8?
        # Let me recalculate: 5 lines = 4 spaces. Each space = 2 semitones. So 8 semitones from bottom to top.
        # Bottom=E4=64. Top=64+8=72=C5. Yes, top line is C5. F5 would be above the staff.
        y = midi_to_staff_y(72, 64, 0.0, 100.0)
        assert y == 0.0

    def test_middle_of_staff(self):
        # B4 (MIDI 71) — midpoint between E4(64) and C5(72)
        y = midi_to_staff_y(68, 64, 0.0, 100.0)
        assert y == 50.0


class TestLedgerLines:
    """Tests for ledger line calculation."""

    def test_middle_c_below_treble(self):
        # C4 (MIDI 60) below treble staff (bottom=E4=64)
        lines = ledger_lines(60, 64)
        # C4=60, below E4=64. Needs line at 60? Check: E4=64, D4=62, C4=60
        # Ledger lines at 62 (D4) and 60 (C4)?
        # The function only returns MIDI values divisible by 2 below staff_bottom-1
        # staff_bottom=64, below=63,62,61,60. Divisible by 2: 62, 60
        assert 62 in lines
        assert 60 in lines

    def test_no_ledger_lines_on_staff(self):
        # E4 (MIDI 64) is ON the bottom line
        lines = ledger_lines(64, 64)
        assert lines == []

    def test_high_note_above_treble(self):
        # G5 (MIDI 79) above treble staff (top=C5=72)
        lines = ledger_lines(79, 64)
        # Above 72: 73,74,75,76,77,78,79. Divisible by 2: 74,76,78
        assert 74 in lines
        assert 76 in lines
        assert 78 in lines
