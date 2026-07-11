"""Main application window — thin orchestrator composing panels and managers.

Refactored in Phase 3: audio logic → AudioStreamManager,
settings propagation → PanelCoordinator, game → GameCoordinator.
"""
from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                                QStackedWidget, QPushButton)
from PyQt6.QtCore import QTimer

from constants import (APP_GEOMETRY, DEFAULT_SAMPLE_RATE, DEFAULT_BLOCK_SIZE,
                       NOTE_HISTORY_MAXLEN)
from settings_panel import SettingsPanel
from tuner_panel import TunerPanel
from history_panel import HistoryPanel
from info_panel import InfoPanel
from game_panel import GamePanel
from game_settings_panel import GameSettingsPanel
from audio_stream_manager import AudioStreamManager
from panel_coordinator import PanelCoordinator
from game_coordinator import GameCoordinator


class NoteAnalyzerApp(QMainWindow):
    """Main application — creates panels, wires managers, handles shutdown."""

    def __init__(self):
        super().__init__()

        self.setWindowTitle("Note Analyzer")

        # 90% of available screen height, respect user's width preference
        screen = self.screen().availableGeometry()
        try:
            w_s, _ = APP_GEOMETRY.split("x")
            self.resize(int(w_s), int(screen.height() * 0.9))
        except Exception:
            self.resize(950, int(screen.height() * 0.9))

        # Dark background on the central widget
        central = QWidget()
        central.setObjectName("CentralWidget")
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(10, 5, 10, 5)
        main_layout.setSpacing(5)

        # ── managers ──────────────────────────────────────────────
        self.audio = AudioStreamManager()
        self.coordinator = None   # created after panels exist
        self.game_coord = None    # created after panels exist

        # ── build UI ──────────────────────────────────────────────
        self._create_panels(main_layout)

        # ── wire audio manager callbacks ──────────────────────────
        self.audio.on_rms = self._on_audio_rms
        self.audio.on_pitch = self._on_audio_pitch
        self.audio.on_history_updated = self._on_audio_history
        self.audio.on_error = self._on_audio_error

        # ── populate devices & start ──────────────────────────────
        self._populate_devices()
        QTimer.singleShot(0, self._request_mic_permission)
        QTimer.singleShot(500, self._start_rms_only)

        # ── wire panel signals ────────────────────────────────────
        self._wire_panel_signals()

        # Push initial settings to the history panel
        self.history_panel.set_notation(self.settings_panel.get_notation())
        self.history_panel.set_quantize(self.settings_panel.get_quantize())
        self.history_panel.set_range(
            self.settings_panel.get_min_midi(),
            self.settings_panel.get_max_midi())

    # ── layout ───────────────────────────────────────────────────

    def _create_panels(self, main_layout: QVBoxLayout) -> None:
        """Build the panel layout with QStackedWidget for tuner↔game switching."""

        # ── Page 0: Tuner / Analyzer view ────────────────────────
        tuner_view = QWidget()
        tuner_layout = QVBoxLayout(tuner_view)
        tuner_layout.setContentsMargins(0, 0, 0, 0)
        tuner_layout.setSpacing(5)

        top_widget = QWidget()
        top_layout = QHBoxLayout(top_widget)
        top_layout.setContentsMargins(0, 0, 0, 0)

        self.settings_panel = SettingsPanel()
        top_layout.addWidget(self.settings_panel, stretch=1)

        self.tuner_panel = TunerPanel()
        top_layout.addWidget(self.tuner_panel, stretch=0)
        tuner_layout.addWidget(top_widget, stretch=0)

        self.history_panel = HistoryPanel()
        tuner_layout.addWidget(self.history_panel, stretch=1)

        self.info_panel = InfoPanel()
        tuner_layout.addWidget(self.info_panel, stretch=0)

        # ── Page 1: Game view ────────────────────────────────────
        game_view = QWidget()
        game_layout = QVBoxLayout(game_view)
        game_layout.setContentsMargins(0, 0, 0, 0)
        game_layout.setSpacing(8)

        self.game_settings_panel = GameSettingsPanel()
        game_layout.addWidget(self.game_settings_panel, stretch=0)

        self.game_panel = GamePanel()
        game_layout.addWidget(self.game_panel, stretch=1)

        # ── Stacked widget ───────────────────────────────────────
        self._view_stack = QStackedWidget()
        self._view_stack.addWidget(tuner_view)   # index 0
        self._view_stack.addWidget(game_view)     # index 1

        main_layout.addWidget(self._view_stack, stretch=1)

        # ── Game button bar ──────────────────────────────────────
        btn_bar = QWidget()
        btn_layout = QHBoxLayout(btn_bar)
        btn_layout.setContentsMargins(0, 0, 0, 0)
        btn_layout.addStretch()
        self._game_btn = QPushButton("🎮  Play Game")
        self._game_btn.setMinimumHeight(30)
        self._game_btn.setMaximumWidth(150)
        self._game_btn.setToolTip("Switch to Note Training Game mode")
        self._game_btn.clicked.connect(self._on_game_button)
        btn_layout.addWidget(self._game_btn)
        main_layout.insertWidget(0, btn_bar)

        # ── Create coordinators ──────────────────────────────────
        self.coordinator = PanelCoordinator(
            self.settings_panel, self.tuner_panel,
            self.history_panel, self.info_panel,
            self.game_panel, self.game_settings_panel)
        self.game_coord = GameCoordinator(
            self.settings_panel, self.game_panel,
            self.game_settings_panel, self._view_stack, self._game_btn)

        # ── Game coordinator callbacks ───────────────────────────
        self.game_coord.enable_full_analysis_cb = self._enable_full_analysis
        self.game_coord.disable_full_analysis_cb = self._disable_full_analysis
        self.game_coord.restart_stream_cb = self._restart_audio_stream

        # ── Wire game panel signals ──────────────────────────────
        self.game_settings_panel.display_mode_callback = self.game_panel.set_display_mode
        self.game_settings_panel.game_mode_callback = self.game_panel.set_game_mode
        self.game_settings_panel.scale_direction_callback = self.game_panel.set_scale_direction
        self.game_settings_panel.game_length_callback = self.game_panel.set_game_length
        self.game_settings_panel.hold_duration_callback = self.game_panel.set_hold_duration
        self.game_settings_panel.instrument_callback = self.game_panel.set_instrument
        self.game_settings_panel.notation_callback = self.game_panel.set_notation

        # Wire game's audio widget → sync to main settings
        self.game_settings_panel._audio.device_callback = self._on_game_device_changed
        self.game_settings_panel._audio.threshold_changed_callback = self.game_coord.sync_threshold_from_game
        self.game_settings_panel._audio.buffer_callback = self._on_game_buffer_changed

    # ── signal wiring ────────────────────────────────────────────

    def _wire_panel_signals(self) -> None:
        """Connect panel signals to coordinator methods."""
        sp = self.settings_panel

        # Settings panel
        sp.set_start_stop_callback(self._toggle_analysis)
        sp.set_buffer_callback(self._on_buffer_changed)
        sp.set_device_callback(self._on_device_changed)
        sp.set_notation_callback(self.coordinator.propagate_notation)
        sp.set_quantize_callback(self.coordinator.propagate_quantize)
        sp.set_min_max_callback(self.coordinator.propagate_range)
        sp.set_reset_callback(self.coordinator.propagate_reset)

        # ── sync audio-relevant settings to the audio manager in real-time ──
        # These must be synced whenever changed, not just at analysis start,
        # because the processing thread reads cached copies.
        sp._instr_cb.currentTextChanged.connect(
            lambda _: self._sync_audio_settings())
        sp._audio.threshold_changed.connect(
            lambda _v: self._sync_audio_settings())
        sp._aubio_cb.toggled.connect(
            lambda _: self._sync_audio_settings())
        sp._continue_cb.toggled.connect(
            lambda _: self._sync_audio_settings())

        # History panel
        self.history_panel.set_clear_callback(self._on_clear_history)

        # Game settings → game coordinator
        gsp = self.game_settings_panel
        gsp.start_callback = self.game_coord.start_game
        gsp.stop_callback = self.game_coord.stop_game
        gsp.back_to_tuner_callback = self.game_coord.switch_to_tuner

        # Game panel
        self.game_panel.back_to_tuner_callback = self.game_coord.switch_to_tuner

    # ── audio manager callbacks ──────────────────────────────────

    def _on_audio_rms(self, rms: float) -> None:
        """RMS level update → push to meters in both panels."""
        self.coordinator.update_rms(rms)

    def _on_audio_pitch(self, midi: float | None,
                         cents: float | None) -> None:
        """Pitch data → route to tuner or game based on active view."""
        if self._view_stack.currentIndex() == 0:
            self.coordinator.update_tuner(midi)
            if midi is not None and cents is not None:
                self.coordinator.update_info_bar(midi, cents)
        self.coordinator.update_game(midi, cents)

    def _on_audio_history(self, history_copy: list, used: int) -> None:
        """History update → push to history panel."""
        self.coordinator.update_history(history_copy, used)

    def _on_audio_error(self, msg: str) -> None:
        self.info_panel.show_error(msg)

    # ── audio lifecycle ──────────────────────────────────────────

    def _start_rms_only(self) -> None:
        """Start audio streaming in RMS-only mode (live on launch)."""
        try:
            device_idx = self._get_device_index()
            self.audio.start_stream(device_idx, self.audio.current_block_size,
                                    self.audio.sample_rate)
            self.settings_panel.set_button_text("▶  Start")
        except Exception as e:
            self.info_panel.show_error(str(e))

    def _toggle_analysis(self) -> None:
        """Toggle between full analysis and RMS-only mode."""
        if self.audio.full_analysis_active:
            self._disable_full_analysis()
        else:
            self._enable_full_analysis()

    def _enable_full_analysis(self) -> None:
        """Enable pitch detection + history."""
        if not self.audio.is_running:
            self._start_rms_only()
        self.audio.enable_full_analysis()
        self._sync_audio_settings()
        self.settings_panel.set_button_text("⏹  Stop")

    def _disable_full_analysis(self) -> None:
        """Drop back to RMS-only."""
        self.audio.disable_full_analysis()
        self.settings_panel.set_button_text("▶  Start")

    def _sync_audio_settings(self) -> None:
        """Push current UI settings to the audio manager before processing."""
        self.audio.noise_threshold = self.settings_panel.get_threshold()
        self.audio.instrument_name = self.settings_panel.get_instrument()
        self.audio.use_aubio = self.settings_panel.get_use_aubio()
        self.audio.continue_on_silence = self.settings_panel.get_continue()

    # ── device management ────────────────────────────────────────

    def _populate_devices(self) -> None:
        names = self.audio.enumerate_devices()
        self.settings_panel.populate_devices(names)
        self._on_device_changed()

    def _get_device_index(self) -> int:
        selected = self.settings_panel.get_device()
        return self.audio.get_device_index(selected)

    def _on_device_changed(self) -> None:
        device_idx = self._get_device_index()
        sr = self.audio.query_sample_rate(device_idx)
        self.audio.sample_rate = int(sr)
        self.settings_panel.set_sample_rate(self.audio.sample_rate)
        if self.audio.is_running:
            self._restart_audio_stream()

    def _on_buffer_changed(self, new_block_size: int) -> None:
        self.audio.current_block_size = int(new_block_size)
        if self.audio.is_running:
            self._restart_audio_stream()

    def _restart_audio_stream(self, buf_val: int | None = None) -> None:
        """Restart the audio stream preserving full-analysis state."""
        if buf_val is not None:
            self.audio.current_block_size = buf_val
        device_idx = self._get_device_index()
        self.audio.restart_stream(device_idx, self.audio.current_block_size,
                                  self.audio.sample_rate)
        self._sync_audio_settings()
        if self.audio.full_analysis_active:
            self.settings_panel.set_button_text("⏹  Stop")
        else:
            self.settings_panel.set_button_text("▶  Start")

    def _request_mic_permission(self) -> None:
        """Probe microphone in a background thread for OS permission dialog."""
        import threading

        def _probe():
            try:
                idx = self._get_device_index()
                probe = __import__('sounddevice').InputStream(
                    device=idx, channels=1,
                    samplerate=self.audio.sample_rate, blocksize=512)
                probe.start()
                probe.stop()
                probe.close()
            except Exception:
                pass
        threading.Thread(target=_probe, daemon=True).start()

    # ── game → main audio sync ──────────────────────────────────

    def _on_game_device_changed(self) -> None:
        self.game_coord.sync_device_from_game()

    def _on_game_buffer_changed(self, buf_val: int) -> None:
        self.game_coord.sync_buffer_from_game(buf_val, self.audio.sample_rate)

    # ── view switching ──────────────────────────────────────────

    def _on_game_button(self) -> None:
        if self._view_stack.currentIndex() == 0:
            self.game_coord.switch_to_game(
                self.audio.sample_rate,
                tuner_full_analysis_active=self.audio.full_analysis_active)
        else:
            self.game_coord.switch_to_tuner()

    # ── history ─────────────────────────────────────────────────

    def _on_clear_history(self) -> None:
        self.audio.clear_history()

    # ── shutdown ─────────────────────────────────────────────────

    def closeEvent(self, event):
        self.audio.stop_stream()
        event.accept()
