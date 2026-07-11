from PyQt6.QtWidgets import QWidget, QLabel, QHBoxLayout
from PyQt6.QtGui import QPainter, QColor, QPen, QFont
from PyQt6.QtCore import Qt

from MyShittyNoteAnalyser.constants import (COLOR_BG_DARKER,
                                            COLOR_BG_METER, COLOR_FG_PRIMARY,
                                            COLOR_FG_SECONDARY, COLOR_METER_TICK,
                                            COLOR_METER_CENTER,
                                            METER_WIDTH, METER_HEIGHT)


class CentsMeter(QWidget):
    """Custom paint widget for the -50..+50 cents deviation meter."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(METER_WIDTH, METER_HEIGHT)
        self._indicator_x: float = 75.0
        self._indicator_color = COLOR_FG_PRIMARY

    def set_value(self, cents: float, color_hex: str) -> None:
        x = 75 + (cents / 50.0) * 75
        self._indicator_x = max(0.0, min(150.0, x))
        self._indicator_color = color_hex
        self.update()

    def paintEvent(self, event):
        p = QPainter(self)

        # background
        p.fillRect(self.rect(), QColor(COLOR_BG_METER))

        # tick marks at -50, -25, 0, +25, +50
        tpen = QPen(QColor(COLOR_METER_TICK), 1)
        p.setPen(tpen)
        for tx in (0, 37, 75, 112, 150):
            p.drawLine(tx, 0, tx, 4)

        # center line (0 cents)
        cpen = QPen(QColor(COLOR_METER_CENTER), 2)
        p.setPen(cpen)
        p.drawLine(75, 0, 75, 15)

        # indicator rectangle
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QColor(self._indicator_color))
        ix = int(self._indicator_x)
        p.drawRect(ix - 5, 2, 10, 11)

        p.end()


class InfoPanel(QWidget):
    """Bottom bar showing note name, accuracy, cents meter, and memory usage."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self) -> None:
        self.setAutoFillBackground(True)
        p = self.palette()
        p.setColor(self.backgroundRole(), QColor(COLOR_BG_DARKER))
        self.setPalette(p)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 4, 10, 4)

        # note & accuracy label (fixed width so the meter doesn't jump)
        self.acc_label = QLabel("")
        self.acc_label.setFont(QFont("Helvetica", 18))
        self.acc_label.setFixedWidth(220)
        self.acc_label.setStyleSheet(f"color: {COLOR_FG_PRIMARY};")
        layout.addWidget(self.acc_label)

        # deviation detail
        self.detail_label = QLabel("")
        self.detail_label.setFont(QFont("Helvetica", 12))
        self.detail_label.setStyleSheet(f"color: {COLOR_FG_SECONDARY};")
        layout.addWidget(self.detail_label)

        # cents meter
        self.cents_meter = CentsMeter(self)
        layout.addWidget(self.cents_meter)

        layout.addStretch()

        # memory usage (right-aligned)
        self.memory_label = QLabel("")
        self.memory_label.setFont(QFont("Helvetica", 9))
        self.memory_label.setStyleSheet(f"color: {COLOR_FG_SECONDARY};")
        layout.addWidget(self.memory_label)

    # ── public API (unchanged signatures) ──────────────────────────────

    def set_memory_usage(self, used: int, total: int) -> None:
        pct = (used / total) * 100 if total > 0 else 0
        self.memory_label.setText(f"{pct:.0f}% used ({used:,} / {total:,})")

    def update_info(self, solfege: str, letter: str, acc_text: str,
                    color: str, cents: float) -> None:
        self.acc_label.setText(f"{solfege} ({letter})  {acc_text}")
        self.acc_label.setStyleSheet(f"color: {color};")
        self.detail_label.setText(f"Deviation: {cents:+.1f} cents")
        self.cents_meter.set_value(cents, color)

    def show_error(self, msg: str) -> None:
        self.acc_label.setText(f"ERROR: {msg}")
        self.acc_label.setStyleSheet("color: #ff5555;")
        self.detail_label.setText("")