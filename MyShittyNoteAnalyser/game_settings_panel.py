"""
Game-mode settings panel — instrument, notation, display mode, game mode,
scale direction, round length, hold duration, audio, and start/stop controls.
"""
from PyQt6.QtWidgets import (QGroupBox, QLabel, QComboBox, QDoubleSpinBox,
                               QPushButton, QVBoxLayout, QGridLayout,
                               QWidget, QHBoxLayout)
from PyQt6.QtCore import Qt, pyqtSignal

from constants import (INSTRUMENTS, DEFAULT_INSTRUMENT,
                       NOTATION_OPTIONS, DEFAULT_NOTATION)
from game_constants import (
    GAME_DISPLAY_MODES, DEFAULT_DISPLAY_MODE,
    GAME_MODES, DEFAULT_GAME_MODE,
    SCALE_DIRECTIONS, DEFAULT_SCALE_DIRECTION,
    GAME_LENGTHS, DEFAULT_GAME_LENGTH,
    HOLD_DURATION_MIN, HOLD_DURATION_MAX,
    HOLD_DURATION_DEFAULT, HOLD_DURATION_STEP,
    INSTRUMENT_CLEF_MAP, DEFAULT_CLEF,
    DEFAULT_NOTATION_BY_INSTRUMENT,
)
from audio_settings_widget import AudioSettingsWidget


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

        # Callbacks set by the controller
        self.start_callback = None
        self.stop_callback = None
        self.display_mode_callback = None
        self.game_mode_callback = None
        self.scale_direction_callback = None
        self.game_length_callback = None
        self.hold_duration_callback = None
        self.instrument_callback = None
        self.notation_callback = None
        self.back_to_tuner_callback = None

        # Shared audio widget
        self._audio = AudioSettingsWidget(label_width=80)
        self._audio._build_buffer_options()

        self._game_active = False
        self._build_ui()

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

    @staticmethod
    def _section_header(text: str) -> QLabel:
        lbl = QLabel(text)
        lbl.setStyleSheet("font-weight: bold; font-size: 8pt;")
        return lbl

    def _add_display_section(self, grid: QGridLayout, r: int) -> int:
        grid.addWidget(self._section_header("─ DISPLAY ─"), r, 0, 1, 2)
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
        grid.addWidget(self._section_header("─ AUDIO ─"), r, 0, 1, 2)
        r += 1
        grid.addWidget(self._audio, r, 0, 1, 2)
        r += 1
        return r

    def _add_game_rules_section(self, grid: QGridLayout, r: int) -> int:
        grid.addWidget(self._section_header("─ GAME RULES ─"), r, 0, 1, 2)
        r += 1

        # Game mode
        grid.addWidget(QLabel("Mode:"), r, 0)
        self._mode_cb = QComboBox()
        self._mode_cb.addItems(GAME_MODES)
        self._mode_cb.setCurrentText(DEFAULT_GAME_MODE)
        self._mode_cb.currentTextChanged.connect(self._on_game_mode_changed)
        grid.addWidget(self._mode_cb, r, 1)
        r += 1

        # Display mode
        grid.addWidget(QLabel("Display:"), r, 0)
        self._display_cb = QComboBox()
        self._display_cb.addItems(GAME_DISPLAY_MODES)
        self._display_cb.setCurrentText(DEFAULT_DISPLAY_MODE)
        self._display_cb.currentTextChanged.connect(self._on_display_changed)
        grid.addWidget(self._display_cb, r, 1)
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
        if self.display_mode_callback:
            self.display_mode_callback(text)

    def _on_notation_changed(self, text: str) -> None:
        self.notation_changed.emit(text)
        if self.notation_callback:
            self.notation_callback(text)

    def _on_instrument_changed(self, text: str) -> None:
        clef = INSTRUMENT_CLEF_MAP.get(text, DEFAULT_CLEF)
        self._clef_lbl.setText(clef.capitalize())
        # Auto-switch notation to instrument's default
        default_notation = DEFAULT_NOTATION_BY_INSTRUMENT.get(
            text, DEFAULT_NOTATION)
        self._notation_cb.blockSignals(True)
        self._notation_cb.setCurrentText(default_notation)
        self._notation_cb.blockSignals(False)
        # Notify notation callback about the auto-change
        self.notation_changed.emit(default_notation)
        if self.notation_callback:
            self.notation_callback(default_notation)
        self.instrument_changed.emit(text)
        if self.instrument_callback:
            self.instrument_callback(text)

    def _on_game_mode_changed(self, text: str) -> None:
        show_direction = (text == "Scale")
        self._direction_lbl.setVisible(show_direction)
        self._direction_cb.setVisible(show_direction)
        self.game_mode_changed.emit(text)
        if self.game_mode_callback:
            self.game_mode_callback(text)

    def _on_scale_direction_changed(self, text: str) -> None:
        self.scale_direction_changed.emit(text)
        if self.scale_direction_callback:
            self.scale_direction_callback(text)

    def _on_length_changed(self, text: str) -> None:
        self.game_length_changed.emit(text)
        if self.game_length_callback:
            self.game_length_callback(text)

    def _on_hold_duration_changed(self, val: float) -> None:
        self.hold_duration_changed.emit(val)
        if self.hold_duration_callback:
            self.hold_duration_callback(val)

    def _on_start_stop(self) -> None:
        if self._game_active:
            self.stop_requested.emit()
            if self.stop_callback:
                self.stop_callback()
        else:
            self.start_requested.emit()
            if self.start_callback:
                self.start_callback()

    def _on_back(self) -> None:
        if self._game_active and self.stop_callback:
            self.stop_callback()
        self.back_to_tuner.emit()
        if self.back_to_tuner_callback:
            self.back_to_tuner_callback()

    # ── public API ──────────────────────────────────────────────────

    def set_game_running(self, active: bool) -> None:
        self._game_active = active
        self._start_btn.setText("⏹  Stop Game" if active else "▶  Start Game")

    def set_clef(self, instrument_name: str) -> None:
        clef = INSTRUMENT_CLEF_MAP.get(instrument_name, DEFAULT_CLEF)
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
        self._audio._build_buffer_options()

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
