"""Musical staff canvas widget — paints clef and target notehead."""

import os

from PyQt6.QtWidgets import QWidget
from PyQt6.QtGui import QPainter, QColor, QPen, QFont
from PyQt6.QtCore import Qt, QRectF
from PyQt6.QtSvg import QSvgRenderer

from game_constants import (GAME_BG, GAME_STAFF_LINE, GAME_NOTEHEAD,
                            GAME_NOTEHEAD_OUTLINE,
                            STAFF_LINE_COUNT, STAFF_LINE_SPACING,
                            STAFF_MARGIN_TOP, STAFF_MARGIN_BOTTOM,
                            NOTEHEAD_WIDTH, NOTEHEAD_HEIGHT,
                            NOTEHEAD_TILT, LEDGER_LINE_EXTEND,
                            CLEF_WIDTH, CLEF_MARGIN,
                            TREBLE_BOTTOM_LINE_MIDI, BASS_BOTTOM_LINE_MIDI)
from note_utils import resource_path, midi_to_staff_y, ledger_lines


class StaffCanvas(QWidget):
    """Paints a musical staff with clef and target notehead."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAutoFillBackground(True)
        p = self.palette()
        p.setColor(self.backgroundRole(), QColor(GAME_BG))
        self.setPalette(p)
        self.setMinimumHeight(160)

        self._target_midi: int = 60  # middle C
        self._clef: str = "treble"

        # SVG renderers (loaded lazily)
        self._treble_renderer: QSvgRenderer | None = None
        self._bass_renderer: QSvgRenderer | None = None
        self._load_svgs()

    def _load_svgs(self) -> None:
        treble_path = resource_path("trebleClef_v2.svg")
        bass_path = resource_path("bassClef_v2.svg")
        if os.path.exists(treble_path):
            self._treble_renderer = QSvgRenderer(treble_path, self)
        if os.path.exists(bass_path):
            self._bass_renderer = QSvgRenderer(bass_path, self)

    def set_target(self, midi: int) -> None:
        self._target_midi = midi
        self.update()

    def set_clef(self, clef: str) -> None:
        self._clef = clef
        self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        w, h = self.width(), self.height()

        clef = self._clef
        bottom_line_midi = (TREBLE_BOTTOM_LINE_MIDI if clef == "treble"
                            else BASS_BOTTOM_LINE_MIDI)

        # ── staff geometry ──────────────────────────────────────
        staff_total_height = (STAFF_LINE_COUNT - 1) * STAFF_LINE_SPACING
        staff_top = STAFF_MARGIN_TOP
        staff_bottom = staff_top + staff_total_height

        # Center staff vertically in available space
        avail = h - STAFF_MARGIN_TOP - STAFF_MARGIN_BOTTOM
        offset_y = max(0, (avail - staff_total_height) // 2)
        staff_top += offset_y
        staff_bottom += offset_y

        # ── clef symbol ─────────────────────────────────────────
        clef_x = 10

        if clef == "treble":
            # Treble v2: viewBox 95×153, fills it well
            clef_w = CLEF_WIDTH
            clef_h = int(staff_total_height * 2.2)
            clef_y = int(staff_top - staff_total_height * 0.25)
        else:
            # Bass v2: viewBox 744×1052, content occupies ~middle 55%
            # Render wider so the clef is proportional to staff
            clef_w = int(CLEF_WIDTH * 1.6)
            clef_h = int(staff_total_height * 2.0)
            clef_y = int(staff_top - staff_total_height * 0.35)

        renderer = (self._treble_renderer if clef == "treble"
                    else self._bass_renderer)
        if renderer is not None and renderer.isValid():
            renderer.render(p, QRectF(clef_x, clef_y, clef_w, clef_h))
        else:
            # Fallback: unicode glyph
            font = QFont("Helvetica", 28, QFont.Weight.Bold)
            p.setFont(font)
            p.setPen(QColor(GAME_STAFF_LINE))
            p.drawText(clef_x, staff_top + int(staff_total_height * 0.6),
                       "𝄞" if clef == "treble" else "𝄢")

        # ── staff lines ─────────────────────────────────────────
        line_start = clef_x + clef_w + CLEF_MARGIN
        line_end = w - 20
        pen = QPen(QColor(GAME_STAFF_LINE), 1.5)
        p.setPen(pen)

        for i in range(STAFF_LINE_COUNT):
            ly = int(staff_top + i * STAFF_LINE_SPACING)
            p.drawLine(line_start, ly, line_end, ly)

        # ── ledger lines ────────────────────────────────────────
        target = self._target_midi
        target_y = midi_to_staff_y(target, bottom_line_midi,
                                    staff_top, staff_bottom)
        ledgers = ledger_lines(target, bottom_line_midi)
        ledger_pen = QPen(QColor(GAME_STAFF_LINE), 1.5)
        p.setPen(ledger_pen)

        note_x = int(line_start + (line_end - line_start) / 2)
        ledger_lx = note_x - NOTEHEAD_WIDTH // 2 - LEDGER_LINE_EXTEND
        ledger_rx = note_x + NOTEHEAD_WIDTH // 2 + LEDGER_LINE_EXTEND

        for lmidi in ledgers:
            ly = midi_to_staff_y(lmidi, bottom_line_midi,
                                  staff_top, staff_bottom)
            p.drawLine(int(ledger_lx), int(ly), int(ledger_rx), int(ly))

        # ── notehead ────────────────────────────────────────────
        rh = NOTEHEAD_HEIGHT // 2
        rw = NOTEHEAD_WIDTH // 2
        note_x_center = int(line_start + (line_end - line_start) / 2)
        note_y_center = int(target_y)

        p.save()
        p.translate(note_x_center, note_y_center)
        p.rotate(NOTEHEAD_TILT)
        p.setPen(QPen(QColor(GAME_NOTEHEAD_OUTLINE), 1.5))
        p.setBrush(QColor(GAME_NOTEHEAD))
        p.drawEllipse(QRectF(-rw, -rh, 2 * rw, 2 * rh))
        p.restore()

        p.end()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.update()
