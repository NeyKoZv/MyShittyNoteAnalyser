from PyQt6.QtWidgets import (QMainWindow, QWidget, QHBoxLayout)
from PyQt6.QtCore import QTimer
import sounddevice as sd

from MyShittyNoteAnalyser.constants import APP_GEOMETRY as _APP_GEOMETRY
from MyShittyNoteAnalyser.settings_panel import SettingsPanel
from MyShittyNoteAnalyser.history_panel import HistoryPanel
from MyShittyNoteAnalyser.audio_stream_manager import AudioStreamManager
from MyShittyNoteAnalyser.panel_coordinator import PanelCoordinator


class NoteAnalyzerApp(QMainWindow):
    """Main application — left column (settings), right column (history full height)."""

    def __init__(self):
        super().__init__()

        self.setWindowTitle("Note Analyzer")

        screen = self.screen().availableGeometry()
        try:
            w_s, h_s = _APP_GEOMETRY.split("x")
            self.resize(int(w_s), int(h_s))
        except Exception:
            self.resize(950, int(screen.height() * 0.9))

        central = QWidget()
        central.setObjectName("CentralWidget")
        self.setCentralWidget(central)
        main_layout = QHBoxLayout(central)
        main_layout.setContentsMargins(8, 6, 8, 6)
        main_layout.setSpacing(8)

        # ── managers ──────────────────────────────────────────────
        self.audio = AudioStreamManager()
        self.coordinator = None   # created after panels exist

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

    def _create_panels(self, main_layout: QHBoxLayout) -> None:
        """Two-column layout: left (settings), right (history)."""

        # ── Left column: Settings ───────────────────────────────
        self.settings_panel = SettingsPanel()
        main_layout.addWidget(self.settings_panel, stretch=0)

        # ── Right column: History (full height) ─────────────────
        self.history_panel = HistoryPanel()
        main_layout.addWidget(self.history_panel, stretch=1)

        # ── Create coordinator ──────────────────────────────────
        self.coordinator = PanelCoordinator(
            self.settings_panel, self.history_panel)

    # ── signal wiring ────────────────────────────────────────────

    def _wire_panel_signals(self) -> None:
        """Connect panel signals to coordinator / controller methods."""
        sp = self.settings_panel

        sp.set_start_stop_callback(self._toggle_analysis)
        sp.audio.buffer_changed.connect(self._on_buffer_changed)
        sp.audio.device_changed.connect(self._on_device_changed)
        sp.notation_changed.connect(self.coordinator.propagate_notation)
        sp.quantize_changed.connect(self.coordinator.propagate_quantize)
        sp.range_changed.connect(self.coordinator.propagate_range)
        sp.reset_requested.connect(self.coordinator.propagate_reset)

        sp.connect_audio_sync(self._sync_audio_settings)

        self.history_panel.set_clear_callback(self._on_clear_history)

    # ── audio manager callbacks ──────────────────────────────────

    def _on_audio_rms(self, rms: float) -> None:
        self.coordinator.update_rms(rms)

    def _on_audio_pitch(self, midi: float | None,
                         cents: float | None) -> None:
        self.coordinator.update_current_note(midi, cents)

    def _on_audio_history(self, history_copy: list, used: int) -> None:
        self.coordinator.update_history(history_copy, used)

    def _on_audio_error(self, msg: str) -> None:
        print(f"Audio error: {msg}")

    # ── audio lifecycle ──────────────────────────────────────────

    def _start_rms_only(self) -> None:
        try:
            device_idx = self._get_device_index()
            self.audio.start_stream(device_idx, self.audio.current_block_size,
                                    self.audio.sample_rate)
            self.settings_panel.set_button_text("▶  Start")
        except Exception as e:
            print(f"Failed to start audio: {e}")

    def _toggle_analysis(self) -> None:
        if self.audio.full_analysis_active:
            self._disable_full_analysis()
        else:
            self._enable_full_analysis()

    def _enable_full_analysis(self) -> None:
        if not self.audio.is_running:
            self._start_rms_only()
        self.audio.enable_full_analysis()
        self._sync_audio_settings()
        self.settings_panel.set_button_text("⏹  Stop")

    def _disable_full_analysis(self) -> None:
        self.audio.disable_full_analysis()
        self.settings_panel.set_button_text("▶  Start")

    def _sync_audio_settings(self) -> None:
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

    def _restart_audio_stream(self) -> None:
        device_idx = self._get_device_index()
        self.audio.restart_stream(device_idx, self.audio.current_block_size,
                                  self.audio.sample_rate)
        self._sync_audio_settings()
        if self.audio.full_analysis_active:
            self.settings_panel.set_button_text("⏹  Stop")
        else:
            self.settings_panel.set_button_text("▶  Start")

    def _request_mic_permission(self) -> None:
        def _probe():
            try:
                idx = self._get_device_index()
                probe = sd.InputStream(
                    device=idx, channels=1,
                    samplerate=self.audio.sample_rate, blocksize=512)
                probe.start()
                probe.stop()
                probe.close()
            except Exception:
                pass
        import threading
        threading.Thread(target=_probe, daemon=True).start()

    # ── history ─────────────────────────────────────────────────

    def _on_clear_history(self) -> None:
        self.audio.clear_history()

    # ── shutdown ─────────────────────────────────────────────────

    def closeEvent(self, event):
        self.audio.stop_stream()
        event.accept()
