"""Semi-transparent summary overlay shown when a game round ends."""

from PyQt6.QtWidgets import QWidget, QPushButton
from PyQt6.QtGui import QPainter, QColor, QPen, QFont
from PyQt6.QtCore import Qt, QRectF

from MyShittyNoteAnalyser.game_constants import (GAME_OVERLAY_WIDTH, GAME_OVERLAY_HEIGHT,
                                                 GAME_OVERLAY_CORNER_RADIUS,
                                                 GAME_CORRECT, GAME_STATS)


class GameOverlay(QWidget):
    """Semi-transparent overlay shown when a round ends."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._score = 0
        self._streak = 0
        self._best_streak = 0
        self._notes_captured = 0
        self._total_notes = 0
        self._is_endless = False
        self.play_again_callback = None
        self.back_callback = None

        # ── Create buttons eagerly so resizeEvent always has them ──
        # Must be created *before* any setVisible call to avoid hideEvent
        # firing while _play_btn / _back_btn don't exist yet.
        self._play_btn = QPushButton("Play Again", self)
        self._play_btn.setFixedSize(140, 36)
        self._play_btn.setVisible(False)
        self._play_btn.clicked.connect(self._on_play_again)

        self._back_btn = QPushButton("Back to Tuner", self)
        self._back_btn.setFixedSize(140, 36)
        self._back_btn.setVisible(False)
        self._back_btn.clicked.connect(self._on_back)

        self.setVisible(False)

    def show_summary(self, score: int, streak: int, best_streak: int,
                     notes_captured: int, total_notes: int,
                     is_endless: bool) -> None:
        self._score = score
        self._streak = streak
        self._best_streak = best_streak
        self._notes_captured = notes_captured
        self._total_notes = total_notes
        self._is_endless = is_endless
        self.setVisible(True)
        self.raise_()
        self.update()

    def hide_overlay(self) -> None:
        self.setVisible(False)

    def paintEvent(self, event):
        super().paintEvent(event)
        p = QPainter(self)
        w, h = self.width(), self.height()

        # Semi-transparent background
        p.fillRect(self.rect(), QColor(0, 0, 0, 200))

        # Centered card
        card_w = GAME_OVERLAY_WIDTH
        card_h = GAME_OVERLAY_HEIGHT
        card_x = (w - card_w) // 2
        card_y = (h - card_h) // 2
        card_rect = QRectF(card_x, card_y, card_w, card_h)

        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QColor(40, 40, 40))
        p.drawRoundedRect(card_rect, GAME_OVERLAY_CORNER_RADIUS,
                          GAME_OVERLAY_CORNER_RADIUS)

        # Title
        title_font = QFont("Helvetica", 22, QFont.Weight.Bold)
        p.setFont(title_font)
        p.setPen(QColor(GAME_CORRECT))
        if self._is_endless:
            title = "🎵  Game Over"
        else:
            title = "🎉  Round Complete!"
        p.drawText(QRectF(card_x, card_y + 15, card_w, 35),
                   Qt.AlignmentFlag.AlignHCenter, title)

        # Stats
        stat_font = QFont("Helvetica", 13)
        p.setFont(stat_font)
        p.setPen(QColor(GAME_STATS))
        line_y = card_y + 65
        gap = 28

        if not self._is_endless:
            progress = f"{self._notes_captured} / {self._total_notes}"
        else:
            progress = f"{self._notes_captured} captures"
        stats = [
            f"Score:  {self._score}",
            f"Notes:  {progress}",
            f"Best streak:  {self._best_streak}",
        ]
        for s in stats:
            p.drawText(QRectF(card_x + 40, line_y, card_w - 80, 22),
                       Qt.AlignmentFlag.AlignHCenter, s)
            line_y += gap

        p.end()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        # Reposition buttons — always safe, created eagerly in __init__
        w = self.width()
        card_x = (w - GAME_OVERLAY_WIDTH) // 2
        card_y = (self.height() - GAME_OVERLAY_HEIGHT) // 2
        btn_w = 140
        btn_h = 36
        total_btn_w = 2 * btn_w + 20
        btn_start_x = card_x + (GAME_OVERLAY_WIDTH - total_btn_w) // 2
        btn_y = card_y + GAME_OVERLAY_HEIGHT - 55

        self._play_btn.move(btn_start_x, btn_y)
        self._back_btn.move(btn_start_x + btn_w + 20, btn_y)

    def _on_play_again(self) -> None:
        if self.play_again_callback:
            self.play_again_callback()

    def _on_back(self) -> None:
        if self.back_callback:
            self.back_callback()

    def showEvent(self, event):
        super().showEvent(event)
        self._play_btn.setVisible(True)
        self._back_btn.setVisible(True)
        self._play_btn.raise_()
        self._back_btn.raise_()

    def hideEvent(self, event):
        super().hideEvent(event)
        self._play_btn.setVisible(False)
        self._back_btn.setVisible(False)
