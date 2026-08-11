"""Self-contained metronome widget with a live beat indicator.

Generates its own click sounds on the fly (numpy + sounddevice) — no
external audio files required. Shows a small visual representation of the
current beat inside the measure, and lets you choose the time signature
(4/4, 3/4, ...) that controls how many beats are displayed.
"""

import numpy as np
import sounddevice as sd
from PyQt6.QtCore import Qt, QTimer, QSize, QPointF, QEvent
from PyQt6.QtGui import QPainter, QColor, QPen, QFont
from PyQt6.QtWidgets import (QGroupBox, QWidget, QLabel, QSpinBox, QComboBox,
                             QPushButton, QCheckBox, QHBoxLayout, QVBoxLayout,
                             QGridLayout, QAbstractSpinBox)

from MyShittyNoteAnalyser.constants import (COLOR_ACCENT_PERFECT,
                                            COLOR_FG_SECONDARY)

# ── configuration ───────────────────────────────────────────────────
TIME_SIGNATURES = ["4/4", "3/4", "2/4", "5/4", "6/8", "7/8"]
DEFAULT_TIME_SIGNATURE = "4/4"
DEFAULT_BPM = 90
MIN_BPM, MAX_BPM = 30, 240

_CLICK_SR = 44100
_ACCENT_FREQ = 1760.0     # A6 — strong tick on beat 1 (downbeat)
_NORMAL_FREQ = 1174.0     # D6 — softer tick on the other beats
_CLICK_SECONDS = 0.035
_CLICK_GAIN = 0.55


def beats_per_measure(time_signature: str) -> int:
    """Return the number of beats in a measure for e.g. '4/4' → 4."""
    try:
        return max(1, int(time_signature.split("/")[0]))
    except (ValueError, AttributeError):
        return 4


class _BeatIndicator(QWidget):
    """Paints one dot per beat; the currently-sounding beat lights up."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._beats = 4
        self._current = -1           # -1 = nothing sounding
        self.setMinimumHeight(52)

    # ── public ─────────────────────────────────────────────────────

    def set_beats(self, beats: int) -> None:
        self._beats = max(1, beats)
        self._current = -1
        self.update()

    def set_current_beat(self, beat: int) -> None:
        """*beat* is the 0-based index of the sounding beat, or -1."""
        self._current = beat
        self.update()

    def sizeHint(self) -> QSize:
        return QSize(160, 52)

    # ── paint ──────────────────────────────────────────────────────

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        w, h = self.width(), self.height()
        n = self._beats
        dot_r = 16
        gap = 8
        total_w = n * dot_r * 2 + (n - 1) * gap
        x0 = (w - total_w) / 2
        cy = h / 2

        font = QFont("Helvetica", 10, QFont.Weight.Bold)
        p.setFont(font)

        for i in range(n):
            cx = x0 + dot_r + i * (dot_r * 2 + gap)
            active = (i == self._current)
            if active:
                p.setBrush(QColor(COLOR_ACCENT_PERFECT))
                p.setPen(QPen(QColor("#ffffff"), 2))
                text_pen = QColor("#000000")
            else:
                p.setBrush(QColor("#3c3c3c"))
                p.setPen(QPen(QColor("#666666"), 1))
                text_pen = QColor(COLOR_FG_SECONDARY)
            p.drawEllipse(int(cx - dot_r), int(cy - dot_r),
                          dot_r * 2, dot_r * 2)
            p.setPen(text_pen)
            p.drawText(int(cx - dot_r), int(cy - dot_r), dot_r * 2, dot_r * 2,
                       Qt.AlignmentFlag.AlignCenter, str(i + 1))
        p.end()


class _DragSpinBox(QSpinBox):
    """Spinbox that scrubs its value by click-and-drag, like Unity.

    Click the field to focus it and type a value; press and drag instead to
    change the value — dragging up/right increases, down/left decreases.

    Note: the spinbox's internal QLineEdit covers the whole field, so the
    mouse events are intercepted via an event filter on that line edit.
    Global coordinates are used so the drag stays consistent even after
    the mouse is grabbed.
    """

    _SENSITIVITY = 0.2     # value units per pixel of drag

    def __init__(self, parent=None):
        super().__init__(parent)
        self._press_global: QPointF | None = None
        self._start_value: int = 0
        self._scrubbing: bool = False
        self.lineEdit().installEventFilter(self)

    # ── shared scrub state ──────────────────────────────────────────

    def _begin_press(self, event) -> None:
        self._press_global = event.globalPosition()
        self._start_value = self.value()
        self._scrubbing = False
        self.setFocus(Qt.FocusReason.MouseFocusReason)

    def _handle_move(self, event) -> bool:
        """Update the value while dragging. Returns True if consumed."""
        if self._press_global is None:
            return False
        if not (event.buttons() & Qt.MouseButton.LeftButton):
            return False
        delta = event.globalPosition() - self._press_global
        # Small dead-zone before entering scrub mode so a plain click
        # still behaves as click-to-edit.
        if (not self._scrubbing
                and abs(delta.x()) + abs(delta.y()) > 4):
            self._scrubbing = True
            self.lineEdit().deselect()      # drop any partial text selection
            self.setCursor(Qt.CursorShape.SizeAllCursor)
            self.grabMouse()
        if self._scrubbing:
            step = int(round((delta.x() - delta.y())
                             * self._SENSITIVITY))
            self.setValue(self._start_value + step)
            return True
        return False

    def _end(self) -> None:
        if self._scrubbing:
            self.releaseMouse()
        self._scrubbing = False
        self._press_global = None
        self.unsetCursor()

    # ── event routing ───────────────────────────────────────────────

    def eventFilter(self, obj, event):
        if obj is self.lineEdit():
            t = event.type()
            if (t == QEvent.Type.MouseButtonPress
                    and event.button() == Qt.MouseButton.LeftButton):
                # Track the press for scrubbing, but let the line edit
                # handle it normally — focus + cursor placement, no select-all.
                self._begin_press(event)
                return False
            if t == QEvent.Type.MouseMove and self._handle_move(event):
                return True
            if t == QEvent.Type.MouseButtonRelease:
                self._end()
        return super().eventFilter(obj, event)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._begin_press(event)
            event.accept()
            return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self._handle_move(event):
            event.accept()
            return
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        self._end()
        super().mouseReleaseEvent(event)


class MetronomeWidget(QGroupBox):
    """Compact, self-contained metronome with a beat visualizer."""

    def __init__(self, parent=None):
        super().__init__("⏱  Metronome", parent)
        self.setObjectName("MetronomeWidget")

        self._beats = beats_per_measure(DEFAULT_TIME_SIGNATURE)
        self._current_beat = 0
        self._click_cache: dict = {}

        self._timer = QTimer(self)
        self._timer.timeout.connect(self._on_tick)

        self._build_ui()
        self._update_interval()

    # ── UI construction ─────────────────────────────────────────────

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setSpacing(6)
        layout.setContentsMargins(8, 14, 8, 8)

        # BPM + Time signature row
        grid = QGridLayout()
        grid.setHorizontalSpacing(6)
        grid.setVerticalSpacing(4)

        grid.addWidget(QLabel("BPM:"), 0, 0)
        bpm_row = QHBoxLayout()
        bpm_row.setSpacing(3)

        self._bpm_spin = _DragSpinBox()
        self._bpm_spin.setRange(MIN_BPM, MAX_BPM)
        self._bpm_spin.setValue(DEFAULT_BPM)
        self._bpm_spin.setSuffix(" bpm")
        # Dedicated +/- buttons are used instead — the spinbox's built-in
        # arrows break under the app stylesheet (up button unreachable).
        self._bpm_spin.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.NoButtons)
        self._bpm_spin.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._bpm_spin.setFixedWidth(64)
        self._bpm_spin.valueChanged.connect(self._on_bpm_changed)
        bpm_row.addWidget(self._bpm_spin)

        self._bpm_down_btn = QPushButton("−")
        self._bpm_down_btn.setFixedSize(26, 22)
        self._bpm_down_btn.setStyleSheet("padding: 0px; min-width: 0px;")
        self._bpm_down_btn.setAutoRepeat(True)
        self._bpm_down_btn.setToolTip("Decrease BPM")
        self._bpm_down_btn.clicked.connect(self._bpm_spin.stepDown)
        bpm_row.addWidget(self._bpm_down_btn)

        self._bpm_up_btn = QPushButton("+")
        self._bpm_up_btn.setFixedSize(26, 22)
        self._bpm_up_btn.setStyleSheet("padding: 0px; min-width: 0px;")
        self._bpm_up_btn.setAutoRepeat(True)
        self._bpm_up_btn.setToolTip("Increase BPM")
        self._bpm_up_btn.clicked.connect(self._bpm_spin.stepUp)
        bpm_row.addWidget(self._bpm_up_btn)

        grid.addLayout(bpm_row, 0, 1)

        grid.addWidget(QLabel("Time:"), 0, 2)
        self._time_cb = QComboBox()
        self._time_cb.addItems(TIME_SIGNATURES)
        self._time_cb.setCurrentText(DEFAULT_TIME_SIGNATURE)
        self._time_cb.currentTextChanged.connect(self._on_time_changed)
        grid.addWidget(self._time_cb, 0, 3)

        layout.addLayout(grid)

        # Visual beat indicator (current note/beat within the measure)
        self._indicator = _BeatIndicator()
        self._indicator.set_beats(self._beats)
        layout.addWidget(self._indicator)

        # Start / Stop + sound toggle
        row = QHBoxLayout()
        row.setSpacing(6)
        self._start_btn = QPushButton("▶  Start")
        self._start_btn.setMinimumHeight(26)
        self._start_btn.clicked.connect(self.toggle)
        row.addWidget(self._start_btn, stretch=2)
        self._sound_cb = QCheckBox("🔊")
        self._sound_cb.setChecked(True)
        self._sound_cb.setToolTip("Play click sound")
        row.addWidget(self._sound_cb)
        layout.addLayout(row)

    # ── internal ────────────────────────────────────────────────────

    def _update_interval(self) -> None:
        bpm = max(MIN_BPM, self._bpm_spin.value())
        self._timer.setInterval(int(60000 / bpm))

    def _on_bpm_changed(self, _value: int) -> None:
        self._update_interval()

    def _on_time_changed(self, text: str) -> None:
        self._beats = beats_per_measure(text)
        self._indicator.set_beats(self._beats)
        self._current_beat = 0
        if not self._timer.isActive():
            self._indicator.set_current_beat(-1)

    def _on_tick(self) -> None:
        accent = (self._current_beat == 0)
        if self._sound_cb.isChecked():
            self._play_click(accent)
        self._indicator.set_current_beat(self._current_beat)
        self._current_beat = (self._current_beat + 1) % self._beats

    # ── click synthesis (self-sufficient, no external files) ────────

    def _synthesize_click(self, accent: bool, sr: int) -> np.ndarray:
        n = max(1, int(_CLICK_SECONDS * sr))
        t = np.arange(n, dtype=np.float64) / sr
        freq = _ACCENT_FREQ if accent else _NORMAL_FREQ
        envelope = np.exp(-t * 160.0)
        wave = np.sin(2 * np.pi * freq * t) * envelope * _CLICK_GAIN
        return wave.astype(np.float32)

    def _output_samplerate(self) -> int:
        try:
            dev = sd.default.device
            out = dev[1] if isinstance(dev, tuple) else dev
            info = sd.query_devices(out)
            return int(info["default_samplerate"])
        except Exception:
            return _CLICK_SR

    def _play_click(self, accent: bool) -> None:
        try:
            sr = self._output_samplerate()
            key = (sr, accent)
            wav = self._click_cache.get(key)
            if wav is None:
                wav = self._synthesize_click(accent, sr)
                self._click_cache[key] = wav
            sd.play(wav, samplerate=sr)
        except Exception as exc:
            print(f"Metronome audio error: {exc}")

    # ── public API ──────────────────────────────────────────────────

    def toggle(self) -> None:
        if self._timer.isActive():
            self.stop()
        else:
            self.start()

    def start(self) -> None:
        self._current_beat = 0
        self._update_interval()
        self._timer.start()
        self._start_btn.setText("⏹  Stop")
        self._on_tick()

    def stop(self) -> None:
        self._timer.stop()
        self._start_btn.setText("▶  Start")
        self._indicator.set_current_beat(-1)
        try:
            sd.stop()
        except Exception:
            pass

    def reset_to_defaults(self) -> None:
        """Reset BPM/time controls. A running metronome keeps running."""
        self._bpm_spin.blockSignals(True)
        self._bpm_spin.setValue(DEFAULT_BPM)
        self._bpm_spin.blockSignals(False)
        self._time_cb.blockSignals(True)
        self._time_cb.setCurrentText(DEFAULT_TIME_SIGNATURE)
        self._time_cb.blockSignals(False)
        self._beats = beats_per_measure(DEFAULT_TIME_SIGNATURE)
        self._indicator.set_beats(self._beats)
        self._current_beat = 0
        self._update_interval()
