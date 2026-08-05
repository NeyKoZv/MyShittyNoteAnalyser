"""
Custom dual-handle range slider for selecting a MIDI note interval.

Paints a horizontal track with two draggable triangular handles and
shows note-name labels below each handle.
"""

from PyQt6.QtWidgets import QWidget
from PyQt6.QtGui import QPainter, QColor, QPen, QFont, QMouseEvent
from PyQt6.QtCore import Qt, pyqtSignal

from MyShittyNoteAnalyser.note_utils import midi_to_note_label

# ── Constants ───────────────────────────────────────────────────────
FULL_MIDI_MIN = 0
FULL_MIDI_MAX = 127
SLIDER_HEIGHT = 64
HANDLE_SIZE = 10      # half-width of the triangular handle
TRACK_Y = 30           # y-position of the horizontal track
TRACK_HEIGHT = 4
LABEL_Y = 48           # y-position of note labels

TRACK_COLOR = "#444444"
ACTIVE_COLOR = "#00ff88"
HANDLE_COLOR = "#ffffff"
LABEL_COLOR = "#aaaaaa"


class RangeSlider(QWidget):
    """A dual-handle slider for selecting a MIDI note range.

    Emits ``range_changed(low_midi, high_midi)`` when either handle moves.
    """

    range_changed = pyqtSignal(int, int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumHeight(SLIDER_HEIGHT)
        self.setMaximumHeight(SLIDER_HEIGHT)
        self.setMouseTracking(True)

        self._low: int = 48    # default C3
        self._high: int = 74   # default D5
        self._dragging: str | None = None   # "low", "high", or None
        self._track_left: int = 0
        self._track_right: int = 1
        self._use_sharps: bool = True

    # ── public API ──────────────────────────────────────────────────

    def set_range(self, low: int, high: int) -> None:
        """Programmatically set both handles (MIDI values 0–127)."""
        self._low = max(FULL_MIDI_MIN, min(FULL_MIDI_MAX, low))
        self._high = max(FULL_MIDI_MIN, min(FULL_MIDI_MAX, high))
        if self._low >= self._high:
            self._high = self._low + 1
        self.update()

    def get_low(self) -> int:
        return self._low

    def get_high(self) -> int:
        return self._high

    def set_notation(self, notation: str) -> None:
        """Update note labels to match the current notation preference."""
        self._use_sharps = (notation == "Sharps")
        self.update()

    # ── geometry helpers ────────────────────────────────────────────

    def _recalc_track(self) -> None:
        """Recalculate track bounds from current widget width."""
        margin = HANDLE_SIZE + 4
        self._track_left = margin
        self._track_right = max(margin + 1, self.width() - margin)

    def _midi_to_x(self, midi: int) -> int:
        frac = (midi - FULL_MIDI_MIN) / (FULL_MIDI_MAX - FULL_MIDI_MIN)
        return int(self._track_left + frac * (self._track_right - self._track_left))

    def _x_to_midi(self, x: int) -> int:
        frac = (x - self._track_left) / (self._track_right - self._track_left)
        return int(FULL_MIDI_MIN + frac * (FULL_MIDI_MAX - FULL_MIDI_MIN))

    # ── mouse handling ──────────────────────────────────────────────

    def mousePressEvent(self, event: QMouseEvent) -> None:
        self._recalc_track()
        x = int(event.position().x())
        low_x = self._midi_to_x(self._low)
        high_x = self._midi_to_x(self._high)

        d_low = abs(x - low_x)
        d_high = abs(x - high_x)

        if d_low <= HANDLE_SIZE + 4:
            self._dragging = "low"
        elif d_high <= HANDLE_SIZE + 4:
            self._dragging = "high"
        # If clicking in the active range between handles, pick closest
        elif low_x < x < high_x:
            self._dragging = "low" if d_low < d_high else "high"
        else:
            self._dragging = None

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        if self._dragging is None:
            return

        self._recalc_track()
        val = self._x_to_midi(int(event.position().x()))
        val = max(FULL_MIDI_MIN, min(FULL_MIDI_MAX, val))

        if self._dragging == "low":
            self._low = min(val, self._high - 1)
        elif self._dragging == "high":
            self._high = max(val, self._low + 1)

        self.range_changed.emit(self._low, self._high)
        self.update()

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        self._dragging = None

    # ── paint ───────────────────────────────────────────────────────

    def paintEvent(self, event):
        self._recalc_track()
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)

        low_x = self._midi_to_x(self._low)
        high_x = self._midi_to_x(self._high)

        # ── Track background ──────────────────────────────────────
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QColor(TRACK_COLOR))
        p.drawRoundedRect(self._track_left, TRACK_Y,
                          self._track_right - self._track_left,
                          TRACK_HEIGHT, 2, 2)

        # ── Active range highlight ────────────────────────────────
        p.setBrush(QColor(ACTIVE_COLOR))
        p.drawRoundedRect(low_x, TRACK_Y, high_x - low_x,
                          TRACK_HEIGHT, 2, 2)

        # ── Handles (triangles pointing down) ─────────────────────
        pen = QPen(QColor(HANDLE_COLOR), 2)
        p.setPen(pen)
        p.setBrush(QColor(HANDLE_COLOR))

        # Low handle
        p.drawLine(low_x, TRACK_Y - HANDLE_SIZE,
                   low_x - HANDLE_SIZE, TRACK_Y - 1)
        p.drawLine(low_x, TRACK_Y - HANDLE_SIZE,
                   low_x + HANDLE_SIZE, TRACK_Y - 1)
        p.drawLine(low_x - HANDLE_SIZE, TRACK_Y - 1,
                   low_x + HANDLE_SIZE, TRACK_Y - 1)

        # High handle
        p.drawLine(high_x, TRACK_Y - HANDLE_SIZE,
                   high_x - HANDLE_SIZE, TRACK_Y - 1)
        p.drawLine(high_x, TRACK_Y - HANDLE_SIZE,
                   high_x + HANDLE_SIZE, TRACK_Y - 1)
        p.drawLine(high_x - HANDLE_SIZE, TRACK_Y - 1,
                   high_x + HANDLE_SIZE, TRACK_Y - 1)

        # ── Labels ────────────────────────────────────────────────
        font = QFont("Helvetica", 8)
        p.setFont(font)
        p.setPen(QColor(LABEL_COLOR))

        low_label = midi_to_note_label(self._low, use_sharps=self._use_sharps)
        high_label = midi_to_note_label(self._high, use_sharps=self._use_sharps)

        # Labels centered under each handle
        p.drawText(low_x - 30, LABEL_Y, 60, 12,
                   Qt.AlignmentFlag.AlignHCenter, low_label)
        p.drawText(high_x - 30, LABEL_Y, 60, 12,
                   Qt.AlignmentFlag.AlignHCenter, high_label)

        p.end()
