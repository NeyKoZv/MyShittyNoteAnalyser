"""
Panel coordinator — handles cross-panel settings propagation and UI updates
that were previously inlined in NoteAnalyzerApp.

Extracted from gui.py as part of Phase 3 refactoring.
"""
from MyShittyNoteAnalyser.constants import NOTE_HISTORY_MAXLEN
from MyShittyNoteAnalyser.note_utils import midi_to_note_text, cents_to_accuracy


class PanelCoordinator:
    """Coordinates settings propagation between panels.

    Holds references to all panels and provides methods to propagate
    settings changes. The controller calls these methods when signals fire.
    """

    def __init__(self, settings_panel, tuner_panel, history_panel,
                 info_panel, game_panel=None, game_settings_panel=None):
        self.settings_panel = settings_panel
        self.tuner_panel = tuner_panel
        self.history_panel = history_panel
        self.info_panel = info_panel
        self.game_panel = game_panel
        self.game_settings_panel = game_settings_panel

        # Last detected note (so notation change can refresh info bar)
        self._last_midi: float | None = None
        self._last_cents: float | None = None

    # ── settings propagation ─────────────────────────────────────

    def propagate_notation(self) -> None:
        """Push current notation setting to all panels that need it."""
        notation = self.settings_panel.get_notation()
        self.history_panel.set_notation(notation)
        if self.game_panel:
            self.game_panel.set_notation(notation)
        # Refresh info bar if we have a cached note
        if self._last_midi is not None and self._last_cents is not None:
            self._update_info_from_midi(self._last_midi, self._last_cents)

    def propagate_quantize(self) -> None:
        quantize = self.settings_panel.get_quantize()
        self.history_panel.set_quantize(quantize)

    def propagate_range(self) -> None:
        min_midi = self.settings_panel.get_min_midi()
        max_midi = self.settings_panel.get_max_midi()
        self.tuner_panel.set_range(min_midi, max_midi)
        self.history_panel.set_range(min_midi, max_midi)
        if self.game_panel:
            self.game_panel.set_range(min_midi, max_midi)

    def propagate_reset(self) -> None:
        """Refresh all panels after a factory reset."""
        self.propagate_notation()
        self.propagate_quantize()
        self.propagate_range()

    # ── UI updates from pitch data ───────────────────────────────

    def update_tuner(self, midi_float: float | None) -> None:
        self.tuner_panel.update_tuner(midi_float)

    def update_info_bar(self, midi_float: float, cents: float) -> None:
        """Derive note name + accuracy from MIDI value, push to info panel."""
        self._last_midi = midi_float
        self._last_cents = cents
        self._update_info_from_midi(midi_float, cents)

    def update_game(self, midi_float: float | None,
                     cents: float | None) -> None:
        """Pass detected notes to the game panel if active."""
        if self.game_panel and self.game_panel.is_active():
            self.game_panel.update_game(midi_float, cents)

    def update_history(self, history_copy: list, used: int) -> None:
        """Push history data to the history panel and memory label."""
        self.history_panel.set_history(history_copy)
        self.info_panel.set_memory_usage(used, NOTE_HISTORY_MAXLEN)

        # Sync notation/quantize if they've drifted
        quantize = self.settings_panel.get_quantize()
        notation = self.settings_panel.get_notation()
        if (not hasattr(self.history_panel, 'notation')
                or self.history_panel.notation != notation):
            self.history_panel.set_notation(notation)
        if self.history_panel.quantize != quantize:
            self.history_panel.set_quantize(quantize)

    def update_rms(self, rms: float) -> None:
        """Update RMS meters in both panels."""
        self.settings_panel.set_rms_level(rms)
        if self.game_settings_panel:
            self.game_settings_panel.set_rms_level(rms)

    # ── internal helpers ─────────────────────────────────────────

    def _update_info_from_midi(self, midi_float: float, cents: float) -> None:
        """Derive note name + accuracy from MIDI value, push to info panel."""
        acc, color = cents_to_accuracy(cents)
        midi_rounded = round(midi_float)
        notation = self.settings_panel.get_notation()
        use_sharps = notation == "Sharps"
        solfege, letter = midi_to_note_text(midi_rounded, use_sharps)
        self.info_panel.update_info(solfege, letter, acc, color, cents)
