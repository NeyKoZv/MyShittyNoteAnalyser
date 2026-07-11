"""
Game-mode settings panel — instrument, notation, display mode, game mode,
scale direction, round length, hold duration, audio, and start/stop controls.
"""
from PyQt6.QtWidgets import (QGroupBox, QLabel, QComboBox, QDoubleSpinBox,
                               QPushButton, QVBoxLayout, QGridLayout)
from PyQt6.QtCore import Qt, pyqtSignal

from MyShittyNoteAnalyser.constants import (INSTRUMENTS, DEFAULT_INSTRUMENT,
                       NOTATION_OPTIONS, DEFAULT_NOTATION)
from MyShittyNoteAnalyser.game_constants import (
    GAME_DISPLAY_MODES, DEFAULT_DISPLAY_MODE,
    GAME_MODES, DEFAULT_GAME_MODE,
    SCALE_DIRECTIONS, DEFAULT_SCALE_DIRECTION,
    GAME_LENGTHS, DEFAULT_GAME_LENGTH,
    HOLD_DURATION_MIN, HOLD_DURATION_MAX,
    HOLD_DURATION_DEFAULT, HOLD_DURATION_STEP,
)
from MyShittyNoteAnalyser.instrument_notation import (
    DEFAULT_CLEF,
    get_clef_for_instrument,
    resolve_notation_on_instrument_change,
)
from MyShittyNoteAnalyser.audio_settings_widget import AudioSettingsWidget
from MyShittyNoteAnalyser.theme import section_header


class GameSettingsPanel(QGroupBox):
    """Game-mode-specific settings, shown alongside the game panel."""

    # ── signals ──────────────────────────────────────────────────
    start_requested = pyqtSignal()
    stop_requested = pyqtSignal()
    display_mode_changed = pyqtSignal(str)
    game_mode_changed = pyqtSignal(str)
    scale_direction_changed = pyqtSignal(str)
    game_length_changed = pyqtSignal(str)
    hold_duration_changed = pyqtSignal(float)
    instrument_changed = pyqtSignal(str)
    notation_changed = pyqtSignal(str)
    back_to_tuner = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__("Game Settings", parent)
        self.setObjectName("GameSettingsPanel")

        # Shared audio widget
        self._audio = AudioSettingsWidget(label_width=80)

        self._game_active = False
        self._build_ui()

    # ── public access to sub-components ─────────────────────────────

    @property
    def audio(self):
        """Public access to the shared AudioSettingsWidget."""
        return self._audio

    # ── UI construction ─────────────────────────────────────────────

    def _build_ui(self) -> None:
        main_layout = QVBoxLayout(self)
        grid = QGridLayout()
        grid.setVerticalSpacing(6)
        grid.setHorizontalSpacing(8)
        main_layout.addLayout(grid)

        r = 0
        r = self._add_display_section(grid, r)
        r = self._add_audio_section(grid, r)
        r = self._add_game_rules_section(grid, r)
        self._add_buttons(grid, r)

    def _add_display_section(self, grid: QGridLayout, r: int) -> int:
        grid.addWidget(section_header("─ DISPLAY ─"), r, 0, 1, 2)
        r += 1

        # Instrument
        grid.addWidget(QLabel("Instrument:"), r, 0)
        self._instr_cb = QComboBox()
        self._instr_cb.addItems(list(INSTRUMENTS.keys()))
        self._instr_cb.setCurrentText(DEFAULT_INSTRUMENT)
        self._instr_cb.currentTextChanged.connect(self._on_instrument_changed)
        grid.addWidget(self._instr_cb, r, 1)
        r += 1

        # Notation
        grid.addWidget(QLabel("Notation:"), r, 0)
        self._notation_cb = QComboBox()
        self._notation_cb.addItems(NOTATION_OPTIONS)
        self._notation_cb.setCurrentText(DEFAULT_NOTATION)
        self._notation_cb.currentTextChanged.connect(self._on_notation_changed)
        grid.addWidget(self._notation_cb, r, 1)
        r += 1

        # Clef indicator (read-only)
        grid.addWidget(QLabel("Clef:"), r, 0)
        self._clef_lbl = QLabel(DEFAULT_CLEF.capitalize())
        self._clef_lbl.setStyleSheet("color: #00ff88; font-weight: bold;")
        grid.addWidget(self._clef_lbl, r, 1)
        r += 1

        return r

    def _add_audio_section(self, grid: QGridLayout, r: int) -> int:
        grid.addWidget(section_header("─ AUDIO ─"), r, 0, 1, 2)
        r += 1
        grid.addWidget(self._audio, r, 0, 1, 2)
        r += 1
        return r

    def _add_game_rules_section(self, grid: QGridLayout, r: int) -> int:
        grid.addWidget(section_header("─ GAME RULES ─"), r, 0, 1, 2)
        r += 1

        # Game mode
        grid.addWidget(QLabel("Mode:"), r, 0)
        self._mode_cb = QComboBox()
        self._mode_cb.addItems(GAME_MODES)
        self._mode_cb.setCurrentText(DEFAULT_GAME_MODE)
        self._mode_cb.currentTextChanged.connect(self._on_game_mode_changed)
        grid.addWidget(self._mode_cb, r, 1)
        r += 1

        # Scale direction — hidden unless Mode is "Scale"
        self._direction_lbl = QLabel("Direction:")
        grid.addWidget(self._direction_lbl, r, 0)
        self._direction_cb = QComboBox()
        self._direction_cb.addItems(SCALE_DIRECTIONS)
        self._direction_cb.setCurrentText(DEFAULT_SCALE_DIRECTION)
        self._direction_cb.currentTextChanged.connect(
            self._on_scale_direction_changed)
        grid.addWidget(self._direction_cb, r, 1)
        self._direction_lbl.setVisible(False)
        self._direction_cb.setVisible(False)
        r += 1

        # Display mode
        grid.addWidget(QLabel("Display:"), r, 0)
        self._display_cb = QComboBox()
        self._display_cb.addItems(GAME_DISPLAY_MODES)
        self._display_cb.setCurrentText(DEFAULT_DISPLAY_MODE)
        self._display_cb.currentTextChanged.connect(self._on_display_changed)
        grid.addWidget(self._display_cb, r, 1)
        r += 1

        # Game length
        grid.addWidget(QLabel("Length:"), r, 0)
        self._length_cb = QComboBox()
        self._length_cb.addItems(GAME_LENGTHS)
        self._length_cb.setCurrentText(DEFAULT_GAME_LENGTH)
        self._length_cb.currentTextChanged.connect(self._on_length_changed)
        grid.addWidget(self._length_cb, r, 1)
        r += 1

        # Hold duration
        grid.addWidget(QLabel("Hold (s):"), r, 0)
        self._hold_spin = QDoubleSpinBox()
        self._hold_spin.setRange(
            HOLD_DURATION_MIN, HOLD_DURATION_MAX)
        self._hold_spin.setSingleStep(HOLD_DURATION_STEP)
        self._hold_spin.setValue(HOLD_DURATION_DEFAULT)
        self._hold_spin.valueChanged.connect(self._on_hold_duration_changed)
        grid.addWidget(self._hold_spin, r, 1)
        r += 1

        return r

    def _add_buttons(self, grid: QGridLayout, r: int) -> None:
        # Start / Stop
        self._start_btn = QPushButton("▶  Start Game")
        self._start_btn.setMinimumHeight(36)
        self._start_btn.clicked.connect(self._on_start_stop)
        grid.addWidget(self._start_btn, r, 0, 1, 2)
        r += 1

        # Back to Tuner
        self._back_btn = QPushButton("←  Back to Tuner")
        self._back_btn.setMinimumHeight(30)
        self._back_btn.clicked.connect(self._on_back)
        grid.addWidget(self._back_btn, r, 0, 1, 2)

    # ── signal handlers ─────────────────────────────────────────────

    def _on_display_changed(self, text: str) -> None:
        self.display_mode_changed.emit(text)

    def _on_notation_changed(self, text: str) -> None:
        self.notation_changed.emit(text)

    def _on_instrument_changed(self, text: str) -> None:
        clef = get_clef_for_instrument(text)
        self._clef_lbl.setText(clef.capitalize())
        # Auto-switch notation to instrument's default
        default_notation = resolve_notation_on_instrument_change(text)
        self._notation_cb.blockSignals(True)
        self._notation_cb.setCurrentText(default_notation)
        self._notation_cb.blockSignals(False)
        # Notify about the auto-change
        self.notation_changed.emit(default_notation)
        self.instrument_changed.emit(text)

    def _on_game_mode_changed(self, text: str) -> None:
        show_direction = (text == "Scale")
        self._direction_lbl.setVisible(show_direction)
        self._direction_cb.setVisible(show_direction)
        self.game_mode_changed.emit(text)

    def _on_scale_direction_changed(self, text: str) -> None:
        self.scale_direction_changed.emit(text)

    def _on_length_changed(self, text: str) -> None:
        self.game_length_changed.emit(text)

    def _on_hold_duration_changed(self, val: float) -> None:
        self.hold_duration_changed.emit(val)

    def _on_start_stop(self) -> None:
        if self._game_active:
            self.stop_requested.emit()
        else:
            self.start_requested.emit()

    def _on_back(self) -> None:
        if self._game_active:
            self.stop_requested.emit()
        self.back_to_tuner.emit()

    # ── public API ──────────────────────────────────────────────────

    def set_game_running(self, active: bool) -> None:
        self._game_active = active
        self._start_btn.setText("⏹  Stop Game" if active else "▶  Start Game")

    def set_clef(self, instrument_name: str) -> None:
        clef = get_clef_for_instrument(instrument_name)
        self._clef_lbl.setText(clef.capitalize())
        # Keep instrument combo in sync
        self._instr_cb.blockSignals(True)
        self._instr_cb.setCurrentText(instrument_name)
        self._instr_cb.blockSignals(False)

    def set_notation(self, notation: str) -> None:
        """Sync notation combo from external change."""
        self._notation_cb.blockSignals(True)
        self._notation_cb.setCurrentText(notation)
        self._notation_cb.blockSignals(False)

    def build_buffer_options(self) -> None:
        self._audio.build_buffer_options()

    def populate_devices(self, device_names: list) -> None:
        self._audio.populate_devices(device_names)

    # ── getters ─────────────────────────────────────────────────────

    def get_instrument(self) -> str:
        return self._instr_cb.currentText()

    def get_display_mode(self) -> str:
        return self._display_cb.currentText()

    def get_game_mode(self) -> str:
        return self._mode_cb.currentText()

    def get_scale_direction(self) -> str:
        return self._direction_cb.currentText()

    def get_game_length(self) -> str:
        return self._length_cb.currentText()

    def get_hold_duration(self) -> float:
        return self._hold_spin.value()

    def get_notation(self) -> str:
        return self._notation_cb.currentText()

    # ── audio delegates ─────────────────────────────────────────────

    def get_device(self) -> str:
        return self._audio.get_device()

    def get_threshold(self) -> float:
        return self._audio.get_threshold()

    def get_buffer_size(self) -> int:
        return self._audio.get_buffer_size()

    def set_sample_rate(self, sr: int) -> None:
        self._audio.set_sample_rate(sr)

    def set_rms_level(self, rms: float) -> None:
        self._audio.set_rms_level(rms)

    def set_device_text(self, text: str) -> None:
        self._audio.set_device_text(text)

    def set_threshold_value(self, value: float) -> None:
        self._audio.set_threshold_value(value)

    def set_buffer_display(self, text: str) -> None:
        self._audio.set_buffer_display(text)
