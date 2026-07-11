from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout)
from PyQt6.QtCore import QTimer

import sounddevice as sd
import threading
import queue
import numpy as np
from collections import deque

from constants import (INSTRUMENTS, NOTE_SHARP_LETTER, NOTE_SHARP_SOLFEGE,
                       NOTE_FLAT_LETTER, NOTE_FLAT_SOLFEGE,
                       COLOR_BG_DARK, COLOR_BG_DARKER,
                       COLOR_ACCENT_PERFECT, COLOR_ACCENT_NICE,
                       COLOR_ACCENT_GOOD, COLOR_ACCENT_BAD,
                       NOTE_HISTORY_MAXLEN, DEFAULT_SAMPLE_RATE,
                       DEFAULT_BLOCK_SIZE, APP_GEOMETRY,
                       DEFAULT_NOTATION)
from pitch_detector import detect_pitch, freq_to_midi
from settings_panel import SettingsPanel
from tuner_panel import TunerPanel
from history_panel import HistoryPanel
from info_panel import InfoPanel


class NoteAnalyzerApp(QMainWindow):
    """Main application controller — wires audio capture to the UI panels."""

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

        # ── audio parameters ──────────────────────────────────────────
        self.sample_rate: int = DEFAULT_SAMPLE_RATE
        self.current_block_size: int = DEFAULT_BLOCK_SIZE

        # ── state ─────────────────────────────────────────────────────
        self.is_running: bool = False
        self.audio_queue: queue.Queue = queue.Queue()
        self.stream: sd.InputStream | None = None

        # Thread-safe note history
        self.note_history: deque = deque(maxlen=NOTE_HISTORY_MAXLEN)
        self._history_lock = threading.Lock()

        # GUI coalescing
        self.update_pending: bool = False
        self.pending_midi: float | None = None
        self.pending_cents: float | None = None
        self.pending_rms: float | None = None

        # Last detected note (so notation change can refresh info bar)
        self._last_midi: float | None = None
        self._last_cents: float | None = None

        # ── build UI ──────────────────────────────────────────────────
        self._create_panels(main_layout)
        self._populate_devices()


        # Trigger OS microphone permission dialog after the window shows
        QTimer.singleShot(0, self._request_mic_permission)

        # ── wire callbacks ────────────────────────────────────────────
        self.settings_panel.set_start_stop_callback(self.toggle_analysis)
        self.settings_panel.set_buffer_callback(self._on_buffer_changed)
        self.settings_panel.set_device_callback(self._on_device_changed)
        self.settings_panel.set_notation_callback(self._on_notation_changed)
        self.settings_panel.set_quantize_callback(self._on_quantize_changed)
        self.settings_panel.set_min_max_callback(self._on_min_max_changed)
        self.settings_panel.set_reset_callback(self._on_reset)

        self.current_block_size = self.settings_panel.get_buffer_size()

        # Push initial settings to the history panel
        self.history_panel.set_notation(self.settings_panel.get_notation())
        self.history_panel.set_quantize(self.settings_panel.get_quantize())
        self.history_panel.set_range(
            self.settings_panel.get_min_midi(),
            self.settings_panel.get_max_midi())

    # ── layout ───────────────────────────────────────────────────────

    def _create_panels(self, main_layout: QVBoxLayout) -> None:
        """Build the panel layout: settings | tuner (top), history, info bar."""

        # top row: settings + tuner
        top_widget = QWidget()
        top_layout = QHBoxLayout(top_widget)
        top_layout.setContentsMargins(0, 0, 0, 0)

        self.settings_panel = SettingsPanel()
        top_layout.addWidget(self.settings_panel, stretch=1)

        self.tuner_panel = TunerPanel()
        top_layout.addWidget(self.tuner_panel, stretch=0)

        main_layout.addWidget(top_widget, stretch=0)

        # history (middle, fills remaining space)
        self.history_panel = HistoryPanel()
        self.history_panel.set_clear_callback(self._on_clear_history)
        main_layout.addWidget(self.history_panel, stretch=1)

        # info bar (bottom)
        self.info_panel = InfoPanel()
        main_layout.addWidget(self.info_panel, stretch=0)

    # ── device management ────────────────────────────────────────────

    def _populate_devices(self) -> None:
        devices = sd.query_devices()
        self._device_name_to_index = {}
        clean_names = []
        for i, dev in enumerate(devices):
            if dev['max_input_channels'] > 0:
                name = dev['name']
                self._device_name_to_index[name] = i
                clean_names.append(name)
        self.settings_panel.populate_devices(clean_names)
        self._on_device_changed()

    def _get_device_index(self) -> int:
        selected = self.settings_panel.get_device()
        idx = self._device_name_to_index.get(selected)
        if idx is not None:
            return idx
        device = sd.default.device
        return device[0] if isinstance(device, tuple) else device

    def _on_device_changed(self) -> None:
        device_idx = self._get_device_index()
        try:
            dev_info = sd.query_devices(device_idx)
            sr = dev_info.get('default_samplerate', DEFAULT_SAMPLE_RATE)
        except Exception:
            sr = self.sample_rate
        self.sample_rate = int(sr)
        self.settings_panel.set_sample_rate(self.sample_rate)
        if self.is_running:
            self.stop_analysis()
            self.start_analysis()

    def _on_buffer_changed(self, new_block_size: int) -> None:
        self.current_block_size = int(new_block_size)
        if self.is_running:
            self.stop_analysis()
            self.start_analysis()

    def _request_mic_permission(self) -> None:
        """Probe microphone in a background thread so the UI isn't blocked
        if the OS shows a permission dialog."""
        import threading
        def _probe():
            try:
                idx = self._get_device_index()
                probe = sd.InputStream(device=idx, channels=1,
                                       samplerate=self.sample_rate, blocksize=512)
                probe.start()
                probe.stop()
                probe.close()
            except Exception:
                pass  # permission denied or no device — user will see error later
        threading.Thread(target=_probe, daemon=True).start()

    # ── callback handlers ────────────────────────────────────────────

    def _on_notation_changed(self) -> None:
        notation = self.settings_panel.get_notation()
        self.history_panel.set_notation(notation)
        # Refresh the info bar immediately with the new notation
        if self._last_midi is not None and self._last_cents is not None:
            self._update_info_from_midi(self._last_midi, self._last_cents)

    def _on_quantize_changed(self) -> None:
        self.history_panel.set_quantize(self.settings_panel.get_quantize())

    def _on_min_max_changed(self) -> None:
        min_midi = self.settings_panel.get_min_midi()
        max_midi = self.settings_panel.get_max_midi()
        self.tuner_panel.set_range(min_midi, max_midi)
        self.history_panel.set_range(min_midi, max_midi)

    def _on_reset(self) -> None:
        """Refresh all panels after a factory reset."""
        self._on_notation_changed()
        self._on_quantize_changed()
        self._on_min_max_changed()
        self.current_block_size = self.settings_panel.get_buffer_size()

    # ── analysis lifecycle ───────────────────────────────────────────

    def toggle_analysis(self) -> None:
        if self.is_running:
            self.stop_analysis()
        else:
            self.start_analysis()

    def start_analysis(self) -> None:
        device_idx = self._get_device_index()
        block_size = self.current_block_size
        sr = self.sample_rate

        try:
            self.stream = sd.InputStream(
                device=device_idx,
                channels=1,
                samplerate=sr,
                blocksize=block_size,
                callback=self.audio_callback,
            )
            self.stream.start()
            self.is_running = True
            self.settings_panel.set_button_text("⏹  Stop")
            self.processing_thread = threading.Thread(
                target=self.process_audio, daemon=True)
            self.processing_thread.start()
        except Exception as e:
            self.info_panel.show_error(str(e))

    def stop_analysis(self) -> None:
        self.is_running = False
        self.update_pending = False
        self.pending_midi = None
        if self.stream:
            self.stream.stop()
            self.stream.close()
            self.stream = None
        self.settings_panel.set_button_text("▶  Start")
        while not self.audio_queue.empty():
            try:
                self.audio_queue.get_nowait()
            except queue.Empty:
                break

    def audio_callback(self, indata, frames, time_info, status) -> None:
        if status:
            print("Audio status:", status)
        self.audio_queue.put(indata.copy())

    # ── audio processing (background thread) ─────────────────────────

    def process_audio(self) -> None:
        while self.is_running:
            try:
                data = self.audio_queue.get(timeout=0.1)
            except queue.Empty:
                continue
            audio = data.flatten()

            rms = np.sqrt(np.mean(audio ** 2))
            threshold = self.settings_panel.get_threshold()
            if rms < threshold:
                if self.settings_panel.get_continue():
                    with self._history_lock:
                        self.note_history.append(None)
                    self.schedule_gui_update(midi=None, rms=rms)
                else:
                    self.schedule_gui_update(midi=None, rms=rms)
                continue

            use_aubio = self.settings_panel.get_use_aubio()
            freq = detect_pitch(audio, self.sample_rate, self.current_block_size,
                                use_aubio=use_aubio)
            if freq is None or freq <= 0:
                continue

            midi = freq_to_midi(freq)
            if midi is None:
                continue

            instr = self.settings_panel.get_instrument()
            offset = INSTRUMENTS.get(instr, 0)
            midi_written = midi + offset
            midi_rounded = round(midi_written)
            cents = (midi_written - midi_rounded) * 100

            with self._history_lock:
                self.note_history.append((midi_written, cents))

            self.schedule_gui_update(midi=midi_written, cents=cents, rms=rms)

    # ── GUI coalescing ───────────────────────────────────────────────

    def schedule_gui_update(self, midi: float | None = None,
                             cents: float | None = None,
                             rms: float | None = None) -> None:
        if self.update_pending:
            if midi is not None:
                self.pending_midi = midi
            if cents is not None:
                self.pending_cents = cents
            if rms is not None:
                self.pending_rms = rms
            return
        self.pending_midi = midi
        self.pending_cents = cents
        self.pending_rms = rms
        self.update_pending = True
        QTimer.singleShot(0, self._perform_gui_update)

    def _perform_gui_update(self) -> None:
        self.update_pending = False
        midi_to_use = self.pending_midi
        cents = self.pending_cents
        rms = self.pending_rms
        self.pending_midi = None
        self.pending_cents = None
        self.pending_rms = None

        self._update_tuner(midi_to_use)
        if midi_to_use is not None and cents is not None:
            self._last_midi = midi_to_use
            self._last_cents = cents
            self._update_info_from_midi(midi_to_use, cents)
        if rms is not None:
            self.settings_panel.set_rms_level(rms)
        self._update_history()

    # ── info / tuner / history helpers ───────────────────────────────

    def _update_info_from_midi(self, midi_float: float, cents: float) -> None:
        """Derive note name + accuracy from MIDI value, push to info panel."""
        abs_cents = abs(cents)
        if abs_cents < 5:
            acc, color = "Perfect", COLOR_ACCENT_PERFECT
        elif abs_cents < 20:
            acc, color = "Nice", COLOR_ACCENT_NICE
        elif abs_cents < 50:
            acc, color = "Good", COLOR_ACCENT_GOOD
        else:
            acc, color = "Bad", COLOR_ACCENT_BAD

        midi_rounded = round(midi_float)
        note_idx = midi_rounded % 12
        notation = self.settings_panel.get_notation()
        use_sharps = notation == "Sharps"
        letter = (NOTE_SHARP_LETTER if use_sharps else NOTE_FLAT_LETTER)[note_idx]
        solfege = (NOTE_SHARP_SOLFEGE if use_sharps else NOTE_FLAT_SOLFEGE)[note_idx]

        self.info_panel.update_info(solfege, letter, acc, color, cents)

    def _update_tuner(self, midi_float: float | None) -> None:
        self.tuner_panel.update_tuner(midi_float)

    def _on_clear_history(self) -> None:
        with self._history_lock:
            self.note_history.clear()
        self._update_history()

    def _update_history(self) -> None:
        with self._history_lock:
            history_copy = list(self.note_history)
            used = len(self.note_history)
        self.history_panel.set_history(history_copy)
        self.info_panel.set_memory_usage(used, NOTE_HISTORY_MAXLEN)
        quantize = self.settings_panel.get_quantize()
        notation = self.settings_panel.get_notation()
        if (not hasattr(self.history_panel, 'notation')
                or self.history_panel.notation != notation):
            self.history_panel.set_notation(notation)
        if self.history_panel.quantize != quantize:
            self.history_panel.set_quantize(quantize)

    # ── shutdown ─────────────────────────────────────────────────────

    def closeEvent(self, event):
        self.stop_analysis()
        event.accept()