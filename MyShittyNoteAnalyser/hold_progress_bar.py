"""Hold-duration progress bar widget for the note training game."""

from PyQt6.QtWidgets import QWidget
from PyQt6.QtGui import QPainter, QColor, QPen, QFont, QLinearGradient, QBrush
from PyQt6.QtCore import Qt, QRectF

from game_constants import (GAME_HOLD_PROGRESS, GAME_HOLD_EMPTY,
                            GAME_HOLD_TEXT, GAME_HOLD_BAR_HEIGHT,
                            HOLD_DURATION_DEFAULT)


class HoldProgressBar(QWidget):
    """Shows hold duration progress as a filling horizontal bar."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._fraction = 0.0
        self._hold_duration = HOLD_DURATION_DEFAULT
        self.setMinimumWidth(200)

    def set_fraction(self, frac: float) -> None:
        self._fraction = max(0.0, min(1.0, frac))
        self.update()

    def set_hold_duration(self, duration: float) -> None:
        self._hold_duration = duration
        self.update()

    def reset(self) -> None:
        self._fraction = 0.0
        self.update()

    def paintEvent(self, event):
        super().paintEvent(event)
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        w = self.width()
        h = self.height()

        bar_height = GAME_HOLD_BAR_HEIGHT
        text_height = 16     # space reserved for the label above the bar
        top_pad = text_height + 4
        bar_y = top_pad      # bar starts below the text
        margin = 40
        bar_x = margin
        bar_w = w - 2 * margin

        # Background
        bg_rect = QRectF(bar_x, bar_y, bar_w, bar_height)
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QColor(GAME_HOLD_EMPTY))
        p.drawRoundedRect(bg_rect, 4, 4)

        # Progress fill
        if self._fraction > 0:
            fill_w = int(bar_w * self._fraction)
            if fill_w > 0:
                gradient = QLinearGradient(bar_x, 0, bar_x + bar_w, 0)
                gradient.setColorAt(0.0, QColor("#005522"))
                gradient.setColorAt(1.0, QColor(GAME_HOLD_PROGRESS))
                p.setBrush(QBrush(gradient))
                fill_rect = QRectF(bar_x, bar_y, fill_w, bar_height)
                p.drawRoundedRect(fill_rect, 4, 4)

        # Text (above the bar, with padding so it isn't clipped)
        p.setPen(QColor(GAME_HOLD_TEXT))
        p.setFont(QFont("Helvetica", 9))
        elapsed = self._fraction * self._hold_duration
        hold_text = f"Hold   {elapsed:.1f}s   /   {self._hold_duration:.1f}s"
        p.drawText(QRectF(bar_x, 0, bar_w, text_height),
                   Qt.AlignmentFlag.AlignCenter, hold_text)

        p.end()
