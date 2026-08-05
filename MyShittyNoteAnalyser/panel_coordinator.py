
class PanelCoordinator:
    """Coordinates settings propagation between panels.

    Holds references to all panels and provides methods to propagate
    settings changes. The controller calls these methods when signals fire.
    """

    def __init__(self, settings_panel, history_panel):
        self.settings_panel = settings_panel
        self.history_panel = history_panel

    # ── settings propagation ─────────────────────────────────────

    def propagate_notation(self) -> None:
        """Push current notation setting to all panels that need it."""
        notation = self.settings_panel.get_notation()
        self.history_panel.set_notation(notation)

    def propagate_quantize(self) -> None:
        quantize = self.settings_panel.get_quantize()
        self.history_panel.set_quantize(quantize)

    def propagate_range(self) -> None:
        min_midi = self.settings_panel.get_min_midi()
        max_midi = self.settings_panel.get_max_midi()
        self.history_panel.set_range(min_midi, max_midi)

    def propagate_reset(self) -> None:
        """Refresh all panels after a factory reset."""
        self.propagate_notation()
        self.propagate_quantize()
        self.propagate_range()

    # ── UI updates from pitch data ───────────────────────────────

    def update_current_note(self, midi_float: float | None,
                             cents: float | None) -> None:
        """Route current pitch to the history panel's live indicator."""
        self.history_panel.set_current_note(midi_float, cents)

    def update_history(self, history_copy: list, used: int) -> None:
        """Push history data to the history panel.

        *used* is accepted for callback compatibility but not used directly.
        """
        _ = used  # accepted for callback compatibility
        self.history_panel.set_history(history_copy)

        # Sync notation/quantize if they've drifted
        quantize = self.settings_panel.get_quantize()
        notation = self.settings_panel.get_notation()
        if self.history_panel.notation != notation:
            self.history_panel.set_notation(notation)
        if self.history_panel.quantize != quantize:
            self.history_panel.set_quantize(quantize)

    def update_rms(self, rms: float) -> None:
        """Update RMS meter."""
        self.settings_panel.set_rms_level(rms)
