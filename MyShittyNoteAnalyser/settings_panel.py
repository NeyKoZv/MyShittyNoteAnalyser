from PyQt6.QtWidgets import (QGroupBox, QWidget, QLabel, QComboBox, QSlider,
                                QCheckBox, QSpinBox, QPushButton,
                                QGridLayout, QHBoxLayout, QVBoxLayout)
from PyQt6.QtCore import Qt, pyqtSignal

from MyShittyNoteAnalyser.constants import (MIN_MIDI, MAX_MIDI, INSTRUMENTS,
                                            DEFAULT_SAMPLE_RATE,
                                            NOISE_THRESHOLD_DEFAULT,
                                            NOTATION_OPTIONS, DEFAULT_NOTATION, DEFAULT_INSTRUMENT)
from MyShittyNoteAnalyser.audio_settings_widget import AudioSettingsWidget
from MyShittyNoteAnalyser.note_utils import midi_to_note_label
from MyShittyNoteAnalyser.instrument_notation import resolve_notation_on_instrument_change
from MyShittyNoteAnalyser.theme import section_header


class SettingsPanel(QGroupBox):
    """Left-hand panel grouping all user-configurable settings into sections."""

    # ── signals ──────────────────────────────────────────────────
    notation_changed = pyqtSignal(str)
    quantize_changed = pyqtSignal(bool)
    range_changed = pyqtSignal(int, int)
    instrument_changed = pyqtSignal(str)
    start_stop_toggled = pyqtSignal()
    reset_requested = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__("Settings", parent)
        self.setObjectName("SettingsPanel")

        self.sample_rate: int = DEFAULT_SAMPLE_RATE

        # Shared audio widget
        self._audio = AudioSettingsWidget(label_width=100)

        self._build_ui()

    # ── public access to sub-components ─────────────────────────────

    @property
    def audio(self):
        """Public access to the shared AudioSettingsWidget."""
        return self._audio

    def connect_audio_sync(self, callback) -> None:
        """Wire all audio-relevant setting changes to *callback*.

        This replaces the previous pattern of reaching into private
        widgets (_instr_cb, _aubio_cb, _continue_cb, _audio) from
        outside the class.
        """
        self._instr_cb.currentTextChanged.connect(lambda _: callback())
        self._audio.threshold_changed.connect(lambda _v: callback())
        self._aubio_cb.toggled.connect(lambda _: callback())
        self._continue_cb.toggled.connect(lambda _: callback())

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

    def _add_audio_section(self, grid: QGridLayout, r: int) -> int:
        grid.addWidget(section_header("─ AUDIO ─"), r, 0, 1, 3)
        r += 1
        grid.addWidget(self._audio, r, 0, 1, 3)
        r += 1
        return r

    def _add_display_section(self, grid: QGridLayout, r: int) -> int:
        grid.addWidget(section_header("─ DISPLAY ─"), r, 0, 1, 3)
        r += 1

        # Instrument
        grid.addWidget(QLabel("Instrument:"), r, 0)
        self._instr_cb = QComboBox()
        self._instr_cb.addItems(list(INSTRUMENTS.keys()))
        self._instr_cb.setCurrentText(DEFAULT_INSTRUMENT)
        self._instr_cb.currentTextChanged.connect(self._on_instrument_changed)
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
            self._min_cb.addItem(midi_to_note_label(m, use_sharps=True), m)
        self._min_cb.setCurrentIndex(MIN_MIDI)
        self._min_cb.currentIndexChanged.connect(self._on_min_max_changed)
        rl.addWidget(self._min_cb)

        rl.addWidget(QLabel("to"))

        self._max_cb = QComboBox()
        self._max_cb.setMinimumWidth(85)
        for m in range(0, 128):
            self._max_cb.addItem(midi_to_note_label(m, use_sharps=True), m)
        self._max_cb.setCurrentIndex(MAX_MIDI)
        self._max_cb.currentIndexChanged.connect(self._on_min_max_changed)
        rl.addWidget(self._max_cb)

        rl.addStretch()
        grid.addWidget(range_widget, r, 0, 1, 3)
        r += 1

        return r

    def _add_analysis_section(self, grid: QGridLayout, r: int) -> int:
        grid.addWidget(section_header("─ ANALYSIS ─"), r, 0, 1, 3)
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

    def _on_notation_selected(self, _text: str) -> None:
        self.notation_changed.emit(_text)

    def _on_quantize_changed(self):
        checked = self._quantize_cb.isChecked()
        self.quantize_changed.emit(checked)

    def _on_min_max_changed(self):
        min_val = self._min_cb.currentData()
        max_val = self._max_cb.currentData()
        self.range_changed.emit(min_val, max_val)

    def _on_instrument_changed(self, text: str) -> None:
        """Auto-switch notation to the instrument's default (flats/sharps)."""
        default_notation = resolve_notation_on_instrument_change(text)
        self._notation_cb.blockSignals(True)
        self._notation_cb.setCurrentText(default_notation)
        self._notation_cb.blockSignals(False)
        self.notation_changed.emit(default_notation)
        self.instrument_changed.emit(text)

    # ── public API ───────────────────────────────────────────────────

    def reset_to_defaults(self) -> None:
        """Reset all widgets to factory defaults."""
        # Audio settings
        self._audio.set_threshold_value(NOISE_THRESHOLD_DEFAULT)
        self._audio.build_buffer_options()

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

        self.reset_requested.emit()

    # ── public API ───────────────────────────────────────────────────

    def set_sample_rate(self, sr: int) -> None:
        self.sample_rate = sr
        self._audio.set_sample_rate(sr)

    def build_buffer_options(self) -> None:
        self._audio.build_buffer_options()

    def populate_devices(self, device_list: list[str]) -> None:
        self._audio.populate_devices(device_list)

    # ── getters (used by controller) ─────────────────────────────────

    def get_device(self) -> str:
        return self._audio.get_device()

    def get_buffer_size(self) -> int:
        return self._audio.get_buffer_size()

    def get_threshold(self) -> float:
        return self._audio.get_threshold()

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

    # ── setters (used to sync from game settings) ────────────────────

    def set_device_text(self, text: str) -> None:
        self._audio.set_device_text(text)

    def set_threshold_value(self, value: float) -> None:
        self._audio.set_threshold_value(value)

    def set_buffer_display(self, text: str) -> None:
        self._audio.set_buffer_display(text)

    def set_start_stop_callback(self, callback) -> None:
        self._start_btn.clicked.connect(callback)
        self._start_btn.clicked.connect(self.start_stop_toggled.emit)

    def set_button_text(self, text: str) -> None:
        self._start_btn.setText(text)

    def set_rms_level(self, rms: float) -> None:
        self._audio.set_rms_level(rms)