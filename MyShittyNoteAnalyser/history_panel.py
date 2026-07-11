from PyQt6.QtWidgets import (QWidget, QGroupBox, QPushButton, QScrollBar,
                                QVBoxLayout, QHBoxLayout)
from PyQt6.QtGui import QPainter, QColor, QPen, QFont
from PyQt6.QtCore import Qt, pyqtSignal

from MyShittyNoteAnalyser.constants import (MIN_MIDI, MAX_MIDI, NOTE_SHARP_LETTER, NOTE_SHARP_SOLFEGE,
                                            NOTE_FLAT_LETTER, NOTE_FLAT_SOLFEGE,
                                            COLOR_BG_DARK, COLOR_BG_DARKER, COLOR_BG_CANVAS,
                                            COLOR_BG_INPUT, COLOR_FG_PRIMARY,
                                            COLOR_GRID_LINE, COLOR_GRID_LABEL,
                                            HISTORY_NOTE_GAP, HISTORY_SCALE_WIDTH,
                                            DEFAULT_NOTATION)
from MyShittyNoteAnalyser.note_utils import cents_to_color, midi_to_y

_NOTE_GAP = HISTORY_NOTE_GAP
_SCALE_W = HISTORY_SCALE_WIDTH


class _HistoryCanvas(QWidget):
    """Single paint widget: scale labels on the left, scrolling notes on the right."""

    def __init__(self, panel: 'HistoryPanel', parent=None):
        super().__init__(parent)
        self.panel = panel
        self.setAutoFillBackground(True)
        p = self.palette()
        p.setColor(self.backgroundRole(), QColor(COLOR_BG_CANVAS))
        self.setPalette(p)
        self.setMinimumHeight(200)

    # ── helpers ──────────────────────────────────────────────────────

    def _recalc_midi_positions(self) -> None:
        h = self.height()
        if h < 10:
            h = 400
        top, bottom = 10, h - 10
        pn = self.panel
        pn._midi_to_y = {}
        pn._plot_top = top
        pn._plot_bottom = bottom
        pn._plot_height = bottom - top
        for midi in range(pn.min_midi, pn.max_midi + 1):
            pn._midi_to_y[midi] = midi_to_y(
                midi, pn.min_midi, pn.max_midi, top, bottom)

    def _get_y(self, midi_float: float) -> float:
        pn = self.panel
        if pn.quantize:
            return pn._midi_to_y.get(round(midi_float), pn._plot_bottom)
        clamped = max(pn.min_midi, min(pn.max_midi, midi_float))
        return midi_to_y(clamped, pn.min_midi, pn.max_midi,
                         pn._plot_top, pn._plot_bottom)

    # ── paint ────────────────────────────────────────────────────────

    def paintEvent(self, event):
        self._recalc_midi_positions()
        p = QPainter(self)
        pn = self.panel

        w, h = self.width(), self.height()
        history = pn.note_history
        total = len(history)

        # ── viewport clipping (notes area only, right of scale) ──────
        visible_w = max(w - _SCALE_W, 100)
        scroll_x = pn._scroll_value

        # world-space range of notes we need to draw
        world_start = max(0, scroll_x - visible_w)      # one screen before
        world_end = scroll_x + 2 * visible_w             # one screen after

        start_idx = int(world_start / _NOTE_GAP)
        end_idx = int(world_end / _NOTE_GAP) + 1
        start_idx = max(0, start_idx)
        end_idx = min(total, end_idx)

        # Helper: convert note index → canvas x (right of scale column)
        def note_x(idx: int) -> int:
            return _SCALE_W + (idx * _NOTE_GAP - scroll_x)

        # ── scale labels (left column, never scrolls) ────────────────
        use_sharps = pn.notation == "Sharps"
        letter_list = NOTE_SHARP_LETTER if use_sharps else NOTE_FLAT_LETTER
        solfege_list = NOTE_SHARP_SOLFEGE if use_sharps else NOTE_FLAT_SOLFEGE

        scale_pen = QPen(QColor(COLOR_GRID_LINE), 1)
        scale_font = QFont("Helvetica", 9)
        p.setFont(scale_font)

        for midi in range(pn.min_midi, pn.max_midi + 1):
            y = pn._midi_to_y.get(midi)
            if y is None:
                continue
            y = int(y)
            note_idx = midi % 12
            label = f"{solfege_list[note_idx]} ({letter_list[note_idx]}{(midi // 12) - 1})"
            # Label only — no horizontal line through the text
            p.setPen(QColor(COLOR_GRID_LABEL))
            p.drawText(0, y - 9, _SCALE_W - 10, 18,
                       Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter, label)

        # ── note grid lines (always at least across visible width) ──
        thin_pen = QPen(QColor(COLOR_GRID_LINE), 1)
        # Rightmost x to draw grid lines to
        if start_idx < end_idx:
            gx_to = note_x(end_idx)
        else:
            gx_to = _SCALE_W + visible_w  # one screen of empty grid
        gx_from = max(_SCALE_W, note_x(start_idx))

        for midi in range(pn.min_midi, pn.max_midi + 1):
            y = pn._midi_to_y.get(midi)
            if y is None:
                continue
            y = int(y)
            p.setPen(thin_pen)
            p.drawLine(gx_from, y, gx_to, y)

        p.setPen(Qt.PenStyle.NoPen)

        # ── note blocks (visible range only) ─────────────────────
        for i in range(start_idx, end_idx):
                entry = history[i]
                if entry is None:
                    continue
                midi_f, cents = entry
                y = int(self._get_y(midi_f))
                nx = note_x(i)
                # Skip notes entirely off-screen to the left
                if nx + _NOTE_GAP < _SCALE_W:
                    continue
                cx = int(nx)
                color = cents_to_color(cents)

                p.setBrush(QColor(color))
                p.drawRect(cx, y - 4, _NOTE_GAP - 1, 8)

        p.end()


class HistoryPanel(QGroupBox):
    """Scrollable pitch-history view with a toolbar (Clear, Live)."""

    # ── signals ──────────────────────────────────────────────────
    clear_requested = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__("Pitch History", parent)
        self.setObjectName("HistoryPanel")

        # ── state ────────────────────────────────────────────────────
        self.note_history: list = []
        self.quantize: bool = False
        self.notation: str = DEFAULT_NOTATION
        self.min_midi: int = MIN_MIDI
        self.max_midi: int = MAX_MIDI
        self.auto_scroll: bool = True
        self._clear_callback = None
        self._scroll_value: int = 0
        self._midi_to_y: dict = {}
        self._plot_top: float = 10
        self._plot_bottom: float = 110
        self._plot_height: float = 100

        # ── layout ───────────────────────────────────────────────────
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(5, 8, 5, 5)

        # canvas
        self._notes_canvas = _HistoryCanvas(self, self)
        main_layout.addWidget(self._notes_canvas, stretch=1)

        # scrollbar
        self._scrollbar = QScrollBar(Qt.Orientation.Horizontal, self)
        self._scrollbar.valueChanged.connect(self._on_scroll)
        main_layout.addWidget(self._scrollbar)

        # toolbar
        toolbar = QWidget(self)
        tl = QHBoxLayout(toolbar)
        tl.setContentsMargins(0, 3, 0, 0)

        self._clear_btn = QPushButton("Clear")
        self._clear_btn.clicked.connect(self._on_clear)
        tl.addWidget(self._clear_btn)

        self._live_btn = QPushButton("◉ Live")
        self._live_btn.clicked.connect(self._on_live)
        tl.addWidget(self._live_btn)

        tl.addStretch()
        main_layout.addWidget(toolbar)

        self._update_scrollbar_range()

    # ── internal ─────────────────────────────────────────────────────

    def _update_scrollbar_range(self) -> None:
        total = len(self.note_history)
        visible_w = max(self._notes_canvas.width() - _SCALE_W, 100)
        content_w = max(total * _NOTE_GAP + 20, visible_w)
        max_val = max(0, content_w - visible_w)
        self._scrollbar.setRange(0, max_val)
        self._scrollbar.setPageStep(visible_w)
        self._scrollbar.setSingleStep(_NOTE_GAP * 2)
        if max_val > 0 and self.auto_scroll:
            self._scrollbar.setValue(max_val)

    def _on_scroll(self, value: int) -> None:
        self._scroll_value = value
        max_val = self._scrollbar.maximum()
        self.auto_scroll = (max_val == 0) or (value >= max_val)
        self._live_btn.setText("◉ Live" if self.auto_scroll else "○ Live")
        self._notes_canvas.update()

    def _on_clear(self) -> None:
        self.clear_requested.emit()
        if self._clear_callback:
            self._clear_callback()

    def _on_live(self) -> None:
        self.auto_scroll = True
        max_val = self._scrollbar.maximum()
        self._scrollbar.setValue(max_val)
        self._live_btn.setText("◉ Live")

    def wheelEvent(self, event):
        delta = event.angleDelta().y()
        self._scrollbar.setValue(self._scrollbar.value() - delta)
        event.accept()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._update_scrollbar_range()
        self._notes_canvas.update()

    # ── public API ───────────────────────────────────────────────────

    def set_clear_callback(self, callback) -> None:
        self._clear_callback = callback

    def set_history(self, history: list) -> None:
        self.note_history = history
        self.update_display()

    def set_notation(self, notation: str) -> None:
        self.notation = notation
        self._notes_canvas.update()

    def set_quantize(self, quantize: bool) -> None:
        self.quantize = quantize
        self._notes_canvas.update()

    def set_range(self, min_midi: int, max_midi: int) -> None:
        self.min_midi = min_midi
        self.max_midi = max_midi
        self._notes_canvas.update()

    def update_display(self) -> None:
        self._update_scrollbar_range()
        self._notes_canvas.update()