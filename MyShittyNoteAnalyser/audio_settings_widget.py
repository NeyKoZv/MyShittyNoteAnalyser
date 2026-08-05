"""
Shared audio-settings widget — microphone, noise threshold + RMS meter,
buffer size. Used by the tuner SettingsPanel.
"""
import math

from PyQt6.QtWidgets import (QWidget, QLabel, QComboBox, QSlider,
                               QHBoxLayout, QGridLayout)
from PyQt6.QtGui import QPainter, QColor, QPen
from PyQt6.QtCore import Qt, pyqtSignal

from MyShittyNoteAnalyser.constants import (DEFAULT_SAMPLE_RATE, DEFAULT_BLOCK_SIZE,
                       BUFFER_OPTIONS, NOISE_THRESHOLD_DB_MIN,
                       NOISE_THRESHOLD_DB_MAX, NOISE_THRESHOLD_DB_DEFAULT,
                       COLOR_ACCENT_PERFECT, COLOR_ACCENT_GOOD,
                       COLOR_ACCENT_BAD)
from MyShittyNoteAnalyser.note_utils import format_buffer_display

# ── RMS meter dB range ────────────────────────────────────────────
_METER_DB_FLOOR = -60   # corresponds to an empty bar
_METER_DB_CEIL = 0      # corresponds to a full bar


def _rms_to_db(rms: float) -> float:
    """Convert a linear RMS amplitude to dB (20⋅log₁₀), clamped."""
    if rms <= 0:
        return _METER_DB_FLOOR
    db = 20.0 * math.log10(rms)
    return max(db, _METER_DB_FLOOR)


# ── RMS meter (tiny bar) ──────────────────────────────────────────

class _RMSMeter(QWidget):
    """Tiny bar showing the current RMS level on a dB scale."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(60, 12)
        self._db_level: float = _METER_DB_FLOOR
        self._db_thresh: float = NOISE_THRESHOLD_DB_DEFAULT

    def _db_to_frac(self, db: float) -> float:
        """Map a dB value to a 0..1 fraction across the meter range."""
        span = _METER_DB_CEIL - _METER_DB_FLOOR
        return max(0.0, min(1.0, (db - _METER_DB_FLOOR) / span))

    def set_level_db(self, db_level: float) -> None:
        self._db_level = max(_METER_DB_FLOOR, db_level)
        self.update()

    def set_threshold_db(self, db_thresh: float) -> None:
        self._db_thresh = db_thresh
        self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        w, h = self.width(), self.height()
        p.fillRect(0, 0, w, h, QColor("#222"))

        level_frac = self._db_to_frac(self._db_level)
        if level_frac > 0:
            bar_w = int(level_frac * w)
            # Colour based on how close the level is to the threshold
            margin_db = self._db_level - self._db_thresh
            if margin_db < -12:
                color = QColor(COLOR_ACCENT_PERFECT)
            elif margin_db < -3:
                color = QColor(COLOR_ACCENT_GOOD)
            else:
                color = QColor(COLOR_ACCENT_BAD)
            p.fillRect(0, 0, bar_w, h, color)

        thresh_frac = self._db_to_frac(self._db_thresh)
        line_x = int(thresh_frac * w)
        p.setPen(QPen(QColor("#ff4444"), 1))
        p.drawLine(line_x, 0, line_x, h)
        p.end()


# ── reusable audio widget ─────────────────────────────────────────

class AudioSettingsWidget(QWidget):
    """Microphone, noise threshold + RMS, buffer size — shared by both panels."""

    # ── signals ──────────────────────────────────────────────────
    device_changed = pyqtSignal()
    buffer_changed = pyqtSignal(int)
    threshold_changed = pyqtSignal(float)

    def __init__(self, label_width: int = 120, parent=None):
        super().__init__(parent)
        self._label_width = label_width
        self.sample_rate: int = DEFAULT_SAMPLE_RATE

        # Internal lookup tables for buffer display strings
        self.buffer_to_display: dict = {}
        self.display_to_buffer: dict = {}

        self._build_ui()
        self.build_buffer_options()

    # ── UI ─────────────────────────────────────────────────────────

    def _build_ui(self) -> None:
        grid = QGridLayout(self)
        grid.setContentsMargins(0, 0, 0, 0)
        grid.setVerticalSpacing(4)
        grid.setHorizontalSpacing(6)

        r = 0

        # Microphone
        mic_lbl = QLabel("Microphone:")
        mic_lbl.setFixedWidth(self._label_width)
        grid.addWidget(mic_lbl, r, 0)
        self._device_cb = QComboBox()
        self._device_cb.setMinimumWidth(180)
        self._device_cb.currentTextChanged.connect(self._on_device_changed)
        grid.addWidget(self._device_cb, r, 1)
        r += 1

        # Noise threshold
        thr_lbl = QLabel("Noise threshold:")
        thr_lbl.setFixedWidth(self._label_width)
        grid.addWidget(thr_lbl, r, 0)

        thr_widget = QWidget()
        thr_layout = QHBoxLayout(thr_widget)
        thr_layout.setContentsMargins(0, 0, 0, 0)
        thr_layout.setSpacing(4)

        self._threshold_slider = QSlider(Qt.Orientation.Horizontal)
        self._threshold_slider.setRange(
            NOISE_THRESHOLD_DB_MIN, NOISE_THRESHOLD_DB_MAX)
        self._threshold_slider.setValue(NOISE_THRESHOLD_DB_DEFAULT)
        self._threshold_slider.valueChanged.connect(
            self._on_threshold_changed)
        self._threshold_slider.setMaximumWidth(100)
        thr_layout.addWidget(self._threshold_slider)

        self._threshold_lbl = QLabel(f"{NOISE_THRESHOLD_DB_DEFAULT} dB")
        self._threshold_lbl.setMinimumWidth(52)
        thr_layout.addWidget(self._threshold_lbl)

        self._rms_meter = _RMSMeter()
        thr_layout.addWidget(self._rms_meter)
        thr_layout.addWidget(QLabel("RMS"))

        grid.addWidget(thr_widget, r, 1)
        r += 1

        # Buffer size
        buf_lbl = QLabel("Buffer size:")
        buf_lbl.setFixedWidth(self._label_width)
        grid.addWidget(buf_lbl, r, 0)
        self._buffer_cb = QComboBox()
        self._buffer_cb.setMinimumWidth(180)
        self._buffer_cb.currentTextChanged.connect(self._on_buffer_changed)
        grid.addWidget(self._buffer_cb, r, 1)
        r += 1

    # ── internal signal handlers ──────────────────────────────────

    def _on_threshold_changed(self, db_val: int) -> None:
        self._threshold_lbl.setText(f"{db_val} dB")
        self._rms_meter.set_threshold_db(db_val)
        self.threshold_changed.emit(float(db_val))

    def _on_device_changed(self, _text: str) -> None:
        self.device_changed.emit()

    def _on_buffer_changed(self, text: str) -> None:
        if not text:
            return
        try:
            buf_val = int(text.split()[0])
            self.buffer_changed.emit(buf_val)
        except (ValueError, IndexError):
            import logging
            logging.getLogger(__name__).debug(
                "Could not parse buffer size from text: %r", text)

    # ── public API ────────────────────────────────────────────────

    def set_rms_level(self, rms: float) -> None:
        """Show the current RMS level on the dB meter."""
        self._rms_meter.set_level_db(_rms_to_db(rms))

    def set_sample_rate(self, sr: int) -> None:
        """Update sample rate and rebuild buffer display strings."""
        self.sample_rate = sr
        current = self._buffer_cb.currentText()
        self.build_buffer_options()
        idx = self._buffer_cb.findText(current)
        if idx >= 0:
            self._buffer_cb.setCurrentIndex(idx)
        else:
            default = format_buffer_display(2048, sr)
            idx = self._buffer_cb.findText(default)
            if idx >= 0:
                self._buffer_cb.setCurrentIndex(idx)
            elif self._buffer_cb.count() > 0:
                self._buffer_cb.setCurrentIndex(0)

    def build_buffer_options(self) -> None:
        sr = self.sample_rate
        self.buffer_to_display.clear()
        self.display_to_buffer.clear()
        self._buffer_cb.blockSignals(True)
        self._buffer_cb.clear()
        for b in BUFFER_OPTIONS:
            display_str = format_buffer_display(b, sr)
            self._buffer_cb.addItem(display_str)
            self.buffer_to_display[b] = display_str
            self.display_to_buffer[display_str] = b
        self._buffer_cb.blockSignals(False)

        # Auto-select 2048
        default_str = format_buffer_display(2048, sr)
        idx = self._buffer_cb.findText(default_str)
        if idx >= 0:
            self._buffer_cb.setCurrentIndex(idx)
        elif self._buffer_cb.count() > 0:
            self._buffer_cb.setCurrentIndex(0)

    def populate_devices(self, device_names: list[str]) -> None:
        """Fill the microphone dropdown."""
        self._device_cb.blockSignals(True)
        self._device_cb.clear()
        if device_names:
            self._device_cb.addItems(device_names)
            self._device_cb.setCurrentIndex(0)
        else:
            self._device_cb.addItem("No input device found")
        self._device_cb.blockSignals(False)

    def set_device_text(self, text: str) -> None:
        """Programmatically set the selected device."""
        self._device_cb.blockSignals(True)
        idx = self._device_cb.findText(text)
        if idx >= 0:
            self._device_cb.setCurrentIndex(idx)
        self._device_cb.blockSignals(False)

    def set_threshold_value(self, db_value: float) -> None:
        """Programmatically set the threshold slider (dB value)."""
        self._threshold_slider.blockSignals(True)
        self._threshold_slider.setValue(int(db_value))
        self._threshold_slider.blockSignals(False)
        self._on_threshold_changed(int(db_value))

    def set_buffer_display(self, text: str) -> None:
        """Programmatically set the buffer by display string."""
        self._buffer_cb.blockSignals(True)
        idx = self._buffer_cb.findText(text)
        if idx >= 0:
            self._buffer_cb.setCurrentIndex(idx)
        self._buffer_cb.blockSignals(False)

    # ── getters ───────────────────────────────────────────────────

    def get_device(self) -> str:
        return self._device_cb.currentText()

    def get_threshold(self) -> float:
        return float(self._threshold_slider.value())

    def get_buffer_size(self) -> int:
        text = self._buffer_cb.currentText()
        return self.display_to_buffer.get(text, DEFAULT_BLOCK_SIZE)
