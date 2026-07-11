"""
Game coordinator — handles game lifecycle, view switching, and state
synchronization between tuner and game modes.

Extracted from gui.py as part of Phase 3 refactoring.
"""
import sounddevice as sd


class GameCoordinator:
    """Orchestrates game mode transitions and tuner↔game state sync."""

    def __init__(self, settings_panel, game_panel, game_settings_panel,
                 view_stack, game_btn):
        self.settings_panel = settings_panel
        self.game_panel = game_panel
        self.game_settings_panel = game_settings_panel
        self._view_stack = view_stack
        self._game_btn = game_btn

        # Callback for when the game needs full analysis enabled/disabled
        self.enable_full_analysis_cb = None
        self.disable_full_analysis_cb = None

        # Callback for device/audio sync from game → main
        self.restart_stream_cb = None

    # ── view switching ───────────────────────────────────────────

    def switch_to_game(self, sample_rate: int,
                        tuner_full_analysis_active: bool = False) -> None:
        """Switch from tuner view to game view, syncing all settings.

        If the tuner had full analysis running, disable it first so the
        game starts with a clean audio pipeline.
        """
        # Stop the tuner's analysis if it was running
        if tuner_full_analysis_active and self.disable_full_analysis_cb:
            self.disable_full_analysis_cb()

        notation = self.settings_panel.get_notation()
        instrument = self.settings_panel.get_instrument()
        min_midi = self.settings_panel.get_min_midi()
        max_midi = self.settings_panel.get_max_midi()

        self.game_panel.set_notation(notation)
        self.game_panel.set_instrument(instrument)
        self.game_panel.set_range(min_midi, max_midi)
        self.game_settings_panel.set_clef(instrument)
        self.game_settings_panel.set_notation(notation)

        # Populate audio devices in game settings
        devices = sd.query_devices()
        clean_names = []
        for dev in devices:
            if dev['max_input_channels'] > 0:
                clean_names.append(dev['name'])
        self.game_settings_panel.populate_devices(clean_names)

        # Sync audio settings from main panel → game panel
        self.game_settings_panel._audio.set_sample_rate(sample_rate)
        self.game_settings_panel._audio.set_device_text(
            self.settings_panel.get_device())
        self.game_settings_panel._audio.set_threshold_value(
            self.settings_panel.get_threshold())

        buf_size = self.settings_panel.get_buffer_size()
        buf_display = f"{buf_size}  (min {sample_rate / buf_size:.0f} Hz)"
        self.game_settings_panel._audio.set_buffer_display(buf_display)

        # Sync game panel settings from game settings panel
        self.game_panel.set_display_mode(
            self.game_settings_panel.get_display_mode())
        self.game_panel.set_game_mode(
            self.game_settings_panel.get_game_mode())
        self.game_panel.set_scale_direction(
            self.game_settings_panel.get_scale_direction())
        self.game_panel.set_game_length(
            self.game_settings_panel.get_game_length())
        self.game_panel.set_hold_duration(
            self.game_settings_panel.get_hold_duration())

        self._view_stack.setCurrentIndex(1)
        self._game_btn.setText("🔬  Back to Tuner")

    def switch_to_tuner(self) -> None:
        """Switch from game view back to tuner view.

        Stops any active game session (including the full-analysis it
        enabled) so the tuner starts clean.
        """
        if self.game_panel.is_active():
            self.stop_game()
        else:
            self.game_settings_panel.set_game_running(False)
        self._view_stack.setCurrentIndex(0)
        self._game_btn.setText("🎮  Play Game")

    # ── game lifecycle ───────────────────────────────────────────

    def start_game(self) -> None:
        self.game_panel.start_game()
        self.game_settings_panel.set_game_running(True)
        if self.enable_full_analysis_cb:
            self.enable_full_analysis_cb()

    def stop_game(self) -> None:
        self.game_panel.stop_game()
        self.game_settings_panel.set_game_running(False)
        if self.disable_full_analysis_cb:
            self.disable_full_analysis_cb()

    # ── game → main audio sync ───────────────────────────────────

    def sync_device_from_game(self) -> None:
        """Sync device from game audio widget → main settings → restart."""
        text = self.game_settings_panel._audio.get_device()
        self.settings_panel._audio.set_device_text(text)
        if self.restart_stream_cb:
            self.restart_stream_cb()

    def sync_threshold_from_game(self, value: float) -> None:
        """Sync noise threshold from game audio widget → main settings."""
        self.settings_panel._audio.set_threshold_value(value)

    def sync_buffer_from_game(self, buf_val: int, sample_rate: int) -> None:
        """Sync buffer size from game audio widget → main settings."""
        buf_display = f"{buf_val}  (min {sample_rate / buf_val:.0f} Hz)"
        self.settings_panel._audio.set_buffer_display(buf_display)
        if self.restart_stream_cb:
            self.restart_stream_cb(buf_val)

    # ── game button handler ──────────────────────────────────────

    def on_game_button(self) -> None:
        """Handle the 🎮 Game button click."""
        if self._view_stack.currentIndex() == 0:
            self.switch_to_game(self.settings_panel._audio.sample_rate)
        else:
            self.switch_to_tuner()
