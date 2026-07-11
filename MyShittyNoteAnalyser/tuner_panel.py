from PyQt6.QtWidgets import QWidget
from PyQt6.QtGui import QPainter, QColor, QPen, QFont
from PyQt6.QtCore import Qt

from MyShittyNoteAnalyser.constants import (MIN_MIDI, MAX_MIDI, NOTE_SHARP_LETTER,
                                            COLOR_BG_DARKER, COLOR_TUNER_TICK, COLOR_TUNER_LABEL,
                                            COLOR_ACCENT_PERFECT,
                                            TUNER_WIDTH, TUNER_HEIGHT, TUNER_MARGIN, TUNER_DOT_RADIUS)
from MyShittyNoteAnalyser.note_utils import midi_to_y, midi_to_letter_octave


class TunerPanel(QWidget):
    """Vertical slider showing the current note position against the MIDI range."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAutoFillBackground(True)
        p = self.palette()
        p.setColor(self.backgroundRole(), QColor(COLOR_BG_DARKER))
        self.setPalette(p)
        self.setFixedWidth(TUNER_WIDTH)
        self.setMinimumHeight(TUNER_HEIGHT)

        self.min_midi: int = MIN_MIDI
        self.max_midi: int = MAX_MIDI
        self._midi_float: float | None = None

        # computed in paintEvent
        self._plot_bottom: float = 0.0
        self._plot_height: float = 0.0

    def set_range(self, min_midi: int, max_midi: int) -> None:
        self.min_midi = min_midi
        self.max_midi = max_midi
        self.update()

    def update_tuner(self, midi_float: float | None) -> None:
        self._midi_float = midi_float
        self.update()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        w = self.width()
        h = self.height()

        margin = TUNER_MARGIN
        plot_top = margin
        plot_bottom = h - margin
        plot_height = plot_bottom - plot_top
        self._plot_bottom = plot_bottom
        self._plot_height = plot_height

        if self.max_midi <= self.min_midi:
            p.end()
            return

        # scale ticks + labels (every 3 semitones)
        tick_pen = QPen(QColor(COLOR_TUNER_TICK), 1)
        label_font = QFont("Helvetica", 7)
        for midi in range(self.min_midi, self.max_midi + 1, 3):
            y = int(midi_to_y(midi, self.min_midi, self.max_midi,
                              plot_top, plot_bottom))

            p.setPen(tick_pen)
            p.drawLine(w - 10, y, w, y)

            label = midi_to_letter_octave(midi, use_sharps=True)
            p.setPen(QColor(COLOR_TUNER_LABEL))
            p.setFont(label_font)
            p.drawText(0, y - 7, w - 14, 14,
                       Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter,
                       label)

        # indicator dot
        if self._midi_float is not None:
            clamped = max(self.min_midi, min(self.max_midi, self._midi_float))
            dy = midi_to_y(clamped, self.min_midi, self.max_midi,
                           plot_top, plot_bottom)
            r = TUNER_DOT_RADIUS

            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(QColor(COLOR_ACCENT_PERFECT))
            p.drawEllipse(int(w / 2 - r), int(dy - r), 2 * r, 2 * r)

        p.end()