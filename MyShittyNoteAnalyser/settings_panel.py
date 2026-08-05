from PyQt6.QtWidgets import (QGroupBox, QLabel, QComboBox,
                                QCheckBox, QPushButton,
                                QGridLayout, QHBoxLayout, QVBoxLayout)
from PyQt6.QtCore import pyqtSignal

from MyShittyNoteAnalyser.constants import (MIN_MIDI, MAX_MIDI, INSTRUMENTS,
                                            DEFAULT_SAMPLE_RATE,
                                            NOISE_THRESHOLD_DB_DEFAULT,
                                            NOTATION_OPTIONS, DEFAULT_NOTATION, DEFAULT_INSTRUMENT)
from MyShittyNoteAnalyser.audio_settings_widget import AudioSettingsWidget
from MyShittyNoteAnalyser.instrument_notation import resolve_notation_on_instrument_change
from MyShittyNoteAnalyser.metronome_widget import MetronomeWidget
from MyShittyNoteAnalyser.range_slider import RangeSlider
from MyShittyNoteAnalyser.theme import section_separator


class SettingsPanel(QGroupBox):
    """Compact settings panel with collapsible sections."""

    # ── signals ──────────────────────────────────────────────────
    notation_changed = pyqtSignal(str)
    quantize_changed = pyqtSignal(bool)
    range_changed = pyqtSignal(int, int)
    reset_requested = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__("Settings", parent)
        self.setObjectName("SettingsPanel")
        self.setFixedWidth(320)

        self.sample_rate: int = DEFAULT_SAMPLE_RATE

        # Shared audio widget (compact label width)
        self._audio = AudioSettingsWidget(label_width=80)

        self._build_ui()

    # ── public access to sub-components ─────────────────────────────

    @property
    def audio(self):
        """Public access to the shared AudioSettingsWidget."""
        return self._audio

    def connect_audio_sync(self, callback) -> None:
        """Wire all audio-relevant setting changes to *callback*."""
        self._instr_cb.currentTextChanged.connect(lambda _: callback())
        self._audio.threshold_changed.connect(lambda _v: callback())
        self._aubio_cb.toggled.connect(lambda _: callback())
        self._continue_cb.toggled.connect(lambda _: callback())

    # ── UI construction ──────────────────────────────────────────────

    def _build_ui(self) -> None:
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(6)
        main_layout.setContentsMargins(8, 16, 8, 8)

        # ── Audio section ───────────────────────────────────────────
        self._add_section_label(main_layout, "🎤  Audio")
        self._audio.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(self._audio)
        main_layout.addWidget(section_separator())

        # ── Display section ─────────────────────────────────────────
        self._add_section_label(main_layout, "🎵  Display")

        # Instrument + Notation in one row
        disp_grid = QGridLayout()
        disp_grid.setVerticalSpacing(4)
        disp_grid.setHorizontalSpacing(6)

        disp_grid.addWidget(QLabel("Instrument:"), 0, 0)
        self._instr_cb = QComboBox()
        self._instr_cb.addItems(list(INSTRUMENTS.keys()))
        self._instr_cb.setCurrentText(DEFAULT_INSTRUMENT)
        self._instr_cb.currentTextChanged.connect(self._on_instrument_changed)
        disp_grid.addWidget(self._instr_cb, 0, 1)

        disp_grid.addWidget(QLabel("Notation:"), 1, 0)
        self._notation_cb = QComboBox()
        self._notation_cb.addItems(NOTATION_OPTIONS)
        self._notation_cb.setCurrentText(DEFAULT_NOTATION)
        self._notation_cb.currentTextChanged.connect(self._on_notation_selected)
        disp_grid.addWidget(self._notation_cb, 1, 1)

        main_layout.addLayout(disp_grid)

        # Range slider
        range_label = QLabel("Range:")
        range_label.setStyleSheet("padding-top: 2px;")
        main_layout.addWidget(range_label)
        self._range_slider = RangeSlider()
        self._range_slider.set_range(MIN_MIDI, MAX_MIDI)
        self._range_slider.set_notation(DEFAULT_NOTATION)
        self._range_slider.range_changed.connect(self._on_range_changed)
        main_layout.addWidget(self._range_slider)

        # Quantize
        self._quantize_cb = QCheckBox("Quantize to semitone")
        self._quantize_cb.setChecked(False)
        self._quantize_cb.toggled.connect(self._on_quantize_changed)
        main_layout.addWidget(self._quantize_cb)

        main_layout.addWidget(section_separator())

        # ── Analysis section ────────────────────────────────────────
        self._add_section_label(main_layout, "⚙️  Analysis")
        self._continue_cb = QCheckBox("Continue on silence")
        main_layout.addWidget(self._continue_cb)
        self._aubio_cb = QCheckBox("Use aubio (faster detection)")
        self._aubio_cb.setChecked(True)
        main_layout.addWidget(self._aubio_cb)

        main_layout.addWidget(section_separator())

        # ── Buttons ─────────────────────────────────────────────────
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(6)
        self._start_btn = QPushButton("▶  Start")
        self._start_btn.setMinimumHeight(32)
        self._start_btn.setMinimumWidth(90)
        btn_layout.addWidget(self._start_btn, stretch=2)
        self._reset_btn = QPushButton("↺  Reset")
        self._reset_btn.setMinimumHeight(32)
        self._reset_btn.clicked.connect(self.reset_to_defaults)
        btn_layout.addWidget(self._reset_btn, stretch=1)
        main_layout.addLayout(btn_layout)

        # ── Metronome (self-contained, under Start/Reset) ───────────
        self._metronome = MetronomeWidget()
        main_layout.addWidget(self._metronome)

        main_layout.addStretch()

    def _add_section_label(self, layout, text: str) -> None:
        lbl = QLabel(text)
        lbl.setStyleSheet("color: #888; font-size: 11px; font-weight: bold; "
                          "padding-top: 4px; padding-bottom: 2px;")
        layout.addWidget(lbl)

    # ── signal handlers ──────────────────────────────────────────────

    def _on_notation_selected(self, text: str) -> None:
        self._range_slider.set_notation(text)
        self.notation_changed.emit(text)

    def _on_quantize_changed(self, checked: bool) -> None:
        self.quantize_changed.emit(checked)

    def _on_range_changed(self, low: int, high: int) -> None:
        self.range_changed.emit(low, high)

    def _on_instrument_changed(self, text: str) -> None:
        """Auto-switch notation to the instrument's default (flats/sharps)."""
        default_notation = resolve_notation_on_instrument_change(text)
        self._notation_cb.blockSignals(True)
        self._notation_cb.setCurrentText(default_notation)
        self._notation_cb.blockSignals(False)
        self._range_slider.set_notation(default_notation)
        self.notation_changed.emit(default_notation)

    # ── public API ───────────────────────────────────────────────────

    def reset_to_defaults(self) -> None:
        """Reset all widgets to factory defaults."""
        self._audio.set_threshold_value(NOISE_THRESHOLD_DB_DEFAULT)
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

        self._range_slider.blockSignals(True)
        self._range_slider.set_range(MIN_MIDI, MAX_MIDI)
        self._range_slider.set_notation(DEFAULT_NOTATION)
        self._range_slider.blockSignals(False)

        self._metronome.reset_to_defaults()

        self.reset_requested.emit()

    def set_sample_rate(self, sr: int) -> None:
        self.sample_rate = sr
        self._audio.set_sample_rate(sr)

    def populate_devices(self, device_list: list[str]) -> None:
        self._audio.populate_devices(device_list)

    # ── getters (used by controller) ─────────────────────────────────

    def get_device(self) -> str:
        return self._audio.get_device()

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
        return self._range_slider.get_low()

    def get_max_midi(self) -> int:
        return self._range_slider.get_high()

    # ── setters ────────────────────────────────────────────────────

    def set_start_stop_callback(self, callback) -> None:
        self._start_btn.clicked.connect(callback)

    def set_button_text(self, text: str) -> None:
        self._start_btn.setText(text)

    def set_rms_level(self, rms: float) -> None:
        self._audio.set_rms_level(rms)