from PyQt6.QtWidgets import (QGroupBox, QWidget, QLabel, QComboBox, QSlider,
                                QCheckBox, QSpinBox, QPushButton,
                                QGridLayout, QHBoxLayout, QVBoxLayout)
from PyQt6.QtGui import QPainter, QColor, QPen
from PyQt6.QtCore import Qt

from constants import (MIN_MIDI, MAX_MIDI, INSTRUMENTS,
                       DEFAULT_SAMPLE_RATE, DEFAULT_BLOCK_SIZE,
                       BUFFER_OPTIONS, NOISE_THRESHOLD_DEFAULT,
                       NOISE_THRESHOLD_MIN, NOISE_THRESHOLD_MAX,
                       NOTATION_OPTIONS, DEFAULT_NOTATION, DEFAULT_INSTRUMENT,
                       NOTE_SHARP_LETTER,
                       COLOR_BG_DARK, COLOR_BG_INPUT, COLOR_FG_PRIMARY,
                       COLOR_ACCENT_PERFECT, COLOR_ACCENT_GOOD,
                       COLOR_ACCENT_BAD)


def _note_label(midi: int) -> str:
    """Return a user-friendly note label, e.g. 60 → 'Do (C4)'."""
    from constants import NOTE_SHARP_SOLFEGE as _SOL
    solfege = _SOL[midi % 12]
    letter = NOTE_SHARP_LETTER[midi % 12]
    octave = (midi // 12) - 1
    return f"{solfege} ({letter}{octave})"


class _RMSMeter(QWidget):
    """Tiny bar showing the current RMS level relative to max threshold."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(60, 12)
        self._level: float = 0.0  # fraction 0..1
        self._thresh_pos: float = NOISE_THRESHOLD_DEFAULT / NOISE_THRESHOLD_MAX

    def set_level(self, fraction: float) -> None:
        self._level = max(0.0, min(1.0, fraction))
        self.update()

    def set_threshold_line(self, threshold_fraction: float) -> None:
        self._thresh_pos = max(0.0, min(1.0, threshold_fraction))
        self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        w, h = self.width(), self.height()
        p.fillRect(0, 0, w, h, QColor("#222"))

        if self._level > 0:
            bar_w = int(self._level * w)
            if self._level < 0.3:
                color = QColor(COLOR_ACCENT_PERFECT)
            elif self._level < 0.7:
                color = QColor(COLOR_ACCENT_GOOD)
            else:
                color = QColor(COLOR_ACCENT_BAD)
            p.fillRect(0, 0, bar_w, h, color)

        # threshold marker line — moves with the slider
        line_x = int(self._thresh_pos * w)
        p.setPen(QPen(QColor("#ff4444"), 1))
        p.drawLine(line_x, 0, line_x, h)
        p.end()


class SettingsPanel(QGroupBox):
    """Left-hand panel grouping all user-configurable settings into sections."""

    def __init__(self, parent=None):
        super().__init__("Settings", parent)
        self.setObjectName("SettingsPanel")

        self.sample_rate: int = DEFAULT_SAMPLE_RATE

        # Callbacks set by the controller
        self.toggle_callback = None
        self.buffer_callback = None
        self.device_callback = None
        self.notation_callback = None
        self.quantize_callback = None
        self.min_max_callback = None
        self.reset_callback = None

        self._build_ui()
        self.build_buffer_options()

    # ── UI construction ──────────────────────────────────────────────

    def _build_ui(self) -> None:
        main_layout = QVBoxLayout(self)
        grid = QGridLayout()
        grid.setVerticalSpacing(4)
        grid.setHorizontalSpacing(8)
        main_layout.addLayout(grid)

        r = 0
        r = self._add_audio_section(grid, r)
        r = self._add_display_section(grid, r)
        r = self._add_analysis_section(grid, r)
        self._add_start_button(grid, r)

    @staticmethod
    def _section_header(text: str) -> QLabel:
        lbl = QLabel(text)
        lbl.setStyleSheet("font-weight: bold; font-size: 8pt;")
        return lbl

    def _add_audio_section(self, grid: QGridLayout, r: int) -> int:
        # header
        grid.addWidget(self._section_header("─ AUDIO ─"), r, 0, 1, 3)
        r += 1

        # Microphone
        grid.addWidget(QLabel("Microphone:"), r, 0)
        self._device_cb = QComboBox()
        self._device_cb.setMinimumWidth(220)
        self._device_cb.currentTextChanged.connect(self._on_device_selected)
        grid.addWidget(self._device_cb, r, 1, 1, 2)
        r += 1

        # Noise threshold (scale 0-50 → 0.000-0.050)
        grid.addWidget(QLabel("Noise threshold:"), r, 0)
        thr_widget = QWidget()
        thr_layout = QHBoxLayout(thr_widget)
        thr_layout.setContentsMargins(0, 0, 0, 0)

        self._threshold_slider = QSlider(Qt.Orientation.Horizontal)
        self._threshold_slider.setRange(
            int(NOISE_THRESHOLD_MIN * 1000), int(NOISE_THRESHOLD_MAX * 1000))
        self._threshold_slider.setValue(int(NOISE_THRESHOLD_DEFAULT * 1000))
        self._threshold_slider.valueChanged.connect(self._on_threshold_changed)
        self._threshold_slider.setMaximumWidth(120)
        thr_layout.addWidget(self._threshold_slider)

        self._threshold_lbl = QLabel(f"{NOISE_THRESHOLD_DEFAULT:.3f}")
        self._threshold_lbl.setFixedWidth(42)
        thr_layout.addWidget(self._threshold_lbl)

        # RMS level indicator
        self._rms_meter = _RMSMeter()
        thr_layout.addWidget(self._rms_meter)
        thr_layout.addWidget(QLabel("RMS"))

        grid.addWidget(thr_widget, r, 1, 1, 2)
        r += 1

        # Buffer size
        grid.addWidget(QLabel("Buffer size:"), r, 0)
        self._buffer_cb = QComboBox()
        self._buffer_cb.setMinimumWidth(220)
        self._buffer_cb.currentTextChanged.connect(self._on_buffer_selected)
        grid.addWidget(self._buffer_cb, r, 1, 1, 2)
        r += 1

        return r

    def _add_display_section(self, grid: QGridLayout, r: int) -> int:
        grid.addWidget(self._section_header("─ DISPLAY ─"), r, 0, 1, 3)
        r += 1

        # Instrument
        grid.addWidget(QLabel("Instrument:"), r, 0)
        self._instr_cb = QComboBox()
        self._instr_cb.addItems(list(INSTRUMENTS.keys()))
        self._instr_cb.setCurrentText(DEFAULT_INSTRUMENT)
        grid.addWidget(self._instr_cb, r, 1, 1, 2)
        r += 1

        # Notation
        grid.addWidget(QLabel("Notation:"), r, 0)
        self._notation_cb = QComboBox()
        self._notation_cb.addItems(NOTATION_OPTIONS)
        self._notation_cb.setCurrentText(DEFAULT_NOTATION)
        self._notation_cb.currentTextChanged.connect(self._on_notation_selected)
        grid.addWidget(self._notation_cb, r, 1, 1, 2)
        r += 1

        # Quantize notes
        self._quantize_cb = QCheckBox("Quantize to nearest semitone")
        self._quantize_cb.setChecked(False)
        self._quantize_cb.toggled.connect(self._on_quantize_changed)
        grid.addWidget(self._quantize_cb, r, 0, 1, 3)
        r += 1

        # MIDI range (note-name comboboxes)
        range_widget = QWidget()
        rl = QHBoxLayout(range_widget)
        rl.setContentsMargins(0, 0, 0, 0)
        rl.addWidget(QLabel("Range:"))

        self._min_cb = QComboBox()
        self._min_cb.setMinimumWidth(85)
        for m in range(0, 128):
            self._min_cb.addItem(_note_label(m), m)
        self._min_cb.setCurrentIndex(MIN_MIDI)
        self._min_cb.currentIndexChanged.connect(self._on_min_max_changed)
        rl.addWidget(self._min_cb)

        rl.addWidget(QLabel("to"))

        self._max_cb = QComboBox()
        self._max_cb.setMinimumWidth(85)
        for m in range(0, 128):
            self._max_cb.addItem(_note_label(m), m)
        self._max_cb.setCurrentIndex(MAX_MIDI)
        self._max_cb.currentIndexChanged.connect(self._on_min_max_changed)
        rl.addWidget(self._max_cb)

        rl.addStretch()
        grid.addWidget(range_widget, r, 0, 1, 3)
        r += 1

        return r

    def _add_analysis_section(self, grid: QGridLayout, r: int) -> int:
        grid.addWidget(self._section_header("─ ANALYSIS ─"), r, 0, 1, 3)
        r += 1

        self._continue_cb = QCheckBox("Continue on silence")
        grid.addWidget(self._continue_cb, r, 0, 1, 3)
        r += 1

        self._aubio_cb = QCheckBox("Use aubio (faster detection)")
        self._aubio_cb.setChecked(True)
        grid.addWidget(self._aubio_cb, r, 0, 1, 3)
        r += 1

        return r

    def _add_start_button(self, grid: QGridLayout, r: int) -> None:
        self._start_btn = QPushButton("▶  Start")
        self._start_btn.setMinimumHeight(36)
        grid.addWidget(self._start_btn, r, 0, 1, 3)
        r += 1
        self._reset_btn = QPushButton("↺ Reset defaults")
        self._reset_btn.clicked.connect(self.reset_to_defaults)
        grid.addWidget(self._reset_btn, r, 0, 1, 3)

    # ── signal handlers ──────────────────────────────────────────────

    def _on_threshold_changed(self, val: int) -> None:
        self._threshold_lbl.setText(f"{val / 1000:.3f}")
        self._rms_meter.set_threshold_line((val / 1000) / NOISE_THRESHOLD_MAX)

    def _on_device_selected(self, _text: str) -> None:
        if self.device_callback:
            self.device_callback()

    def _on_buffer_selected(self, text: str) -> None:
        if not text:
            return
        try:
            buf_val = int(text.split()[0])
            if self.buffer_callback:
                self.buffer_callback(buf_val)
        except (ValueError, IndexError):
            pass

    def _on_notation_selected(self, _text: str) -> None:
        if self.notation_callback:
            self.notation_callback()

    def _on_quantize_changed(self):
        if self.quantize_callback:
            self.quantize_callback()

    def _on_min_max_changed(self):
        if self.min_max_callback:
            self.min_max_callback()

    # ── public API ───────────────────────────────────────────────────

    def reset_to_defaults(self) -> None:
        """Reset all widgets to factory defaults."""
        # Reset each widget to its Python-level default
        self._device_cb.blockSignals(True)
        self._device_cb.setCurrentIndex(0)
        self._device_cb.blockSignals(False)

        self._threshold_slider.blockSignals(True)
        self._threshold_slider.setValue(int(NOISE_THRESHOLD_DEFAULT * 1000))
        self._threshold_slider.blockSignals(False)
        self._on_threshold_changed(int(NOISE_THRESHOLD_DEFAULT * 1000))

        self._instr_cb.blockSignals(True)
        self._instr_cb.setCurrentText(DEFAULT_INSTRUMENT)
        self._instr_cb.blockSignals(False)

        self._notation_cb.blockSignals(True)
        self._notation_cb.setCurrentText(DEFAULT_NOTATION)
        self._notation_cb.blockSignals(False)

        self._quantize_cb.blockSignals(True)
        self._quantize_cb.setChecked(False)
        self._quantize_cb.blockSignals(False)

        self._continue_cb.blockSignals(True)
        self._continue_cb.setChecked(False)
        self._continue_cb.blockSignals(False)

        self._aubio_cb.blockSignals(True)
        self._aubio_cb.setChecked(True)
        self._aubio_cb.blockSignals(False)

        self._min_cb.blockSignals(True)
        self._min_cb.setCurrentIndex(MIN_MIDI)
        self._min_cb.blockSignals(False)

        self._max_cb.blockSignals(True)
        self._max_cb.setCurrentIndex(MAX_MIDI)
        self._max_cb.blockSignals(False)

        # buffer default
        display = self.buffer_to_display.get(DEFAULT_BLOCK_SIZE)
        if display:
            idx = self._buffer_cb.findText(display)
            if idx >= 0:
                self._buffer_cb.blockSignals(True)
                self._buffer_cb.setCurrentIndex(idx)
                self._buffer_cb.blockSignals(False)

        # Notify controller to refresh dependent panels
        if self.reset_callback:
            self.reset_callback()

    # ── public API ───────────────────────────────────────────────────

    def set_sample_rate(self, sr: int) -> None:
        self.sample_rate = sr
        current = self._buffer_cb.currentText()
        self.build_buffer_options()
        idx = self._buffer_cb.findText(current)
        if idx >= 0:
            self._buffer_cb.setCurrentIndex(idx)
        else:
            default = f"2048  (min {sr / 2048:.0f} Hz)"
            idx = self._buffer_cb.findText(default)
            if idx >= 0:
                self._buffer_cb.setCurrentIndex(idx)
            elif self._buffer_cb.count() > 0:
                self._buffer_cb.setCurrentIndex(0)

    def build_buffer_options(self) -> None:
        sr = self.sample_rate
        self.buffer_to_display = {}
        self.display_to_buffer = {}
        self._buffer_cb.blockSignals(True)
        self._buffer_cb.clear()
        for b in BUFFER_OPTIONS:
            low_freq = sr / b
            display_str = f"{b}  (min {low_freq:.0f} Hz)"
            self._buffer_cb.addItem(display_str)
            self.buffer_to_display[b] = display_str
            self.display_to_buffer[display_str] = b
        self._buffer_cb.blockSignals(False)

        # Auto-select 2048
        default_str = f"2048  (min {sr / 2048:.0f} Hz)"
        idx = self._buffer_cb.findText(default_str)
        if idx >= 0:
            self._buffer_cb.setCurrentIndex(idx)
        elif self._buffer_cb.count() > 0:
            self._buffer_cb.setCurrentIndex(0)

    def populate_devices(self, device_list: list[str]) -> None:
        self._device_cb.blockSignals(True)
        self._device_cb.clear()
        if device_list:
            self._device_cb.addItems(device_list)
            self._device_cb.setCurrentIndex(0)
        else:
            self._device_cb.addItem("No input device found")
        self._device_cb.blockSignals(False)

    # ── getters (used by controller) ─────────────────────────────────

    def get_device(self) -> str:
        return self._device_cb.currentText()

    def get_buffer_size(self) -> int:
        text = self._buffer_cb.currentText()
        return self.display_to_buffer.get(text, DEFAULT_BLOCK_SIZE)

    def get_threshold(self) -> float:
        return self._threshold_slider.value() / 1000.0

    def get_instrument(self) -> str:
        return self._instr_cb.currentText()

    def get_notation(self) -> str:
        return self._notation_cb.currentText()

    def get_quantize(self) -> bool:
        return self._quantize_cb.isChecked()

    def get_continue(self) -> bool:
        return self._continue_cb.isChecked()

    def get_use_aubio(self) -> bool:
        return self._aubio_cb.isChecked()

    def get_min_midi(self) -> int:
        return self._min_cb.currentData()

    def get_max_midi(self) -> int:
        return self._max_cb.currentData()

    # ── callback setters ─────────────────────────────────────────────

    def set_start_stop_callback(self, callback) -> None:
        self.toggle_callback = callback
        self._start_btn.clicked.connect(callback)

    def set_buffer_callback(self, callback) -> None:
        self.buffer_callback = callback

    def set_device_callback(self, callback) -> None:
        self.device_callback = callback

    def set_notation_callback(self, callback) -> None:
        self.notation_callback = callback

    def set_quantize_callback(self, callback) -> None:
        self.quantize_callback = callback

    def set_min_max_callback(self, callback) -> None:
        self.min_max_callback = callback

    def set_reset_callback(self, callback) -> None:
        self.reset_callback = callback

    def set_button_text(self, text: str) -> None:
        self._start_btn.setText(text)

    def set_rms_level(self, rms: float) -> None:
        """Show the current RMS level (relative to max threshold)."""
        self._rms_meter.set_level(rms / NOISE_THRESHOLD_MAX)