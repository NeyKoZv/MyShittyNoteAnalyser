import tkinter as tk
from tkinter import ttk
from constants import (MIN_MIDI, MAX_MIDI, NOTE_SHARP_LETTER, NOTE_SHARP_SOLFEGE,
                       NOTE_FLAT_LETTER, NOTE_FLAT_SOLFEGE,
                       COLOR_BG_DARK, COLOR_BG_DARKER, COLOR_BG_CANVAS,
                       COLOR_BG_INPUT, COLOR_FG_PRIMARY, COLOR_BUTTON_ACTIVE,
                       COLOR_GRID_LINE, COLOR_GRID_LABEL,
                       COLOR_ACCENT_PERFECT, COLOR_ACCENT_NICE,
                       COLOR_ACCENT_GOOD, COLOR_ACCENT_BAD,
                       HISTORY_NOTE_GAP, HISTORY_SCALE_WIDTH,
                       DEFAULT_NOTATION)

# ── helpers ────────────────────────────────────────────────────────────────

_NOTE_GAP = HISTORY_NOTE_GAP
_SCALE_W = HISTORY_SCALE_WIDTH


class HistoryPanel(ttk.LabelFrame):
    """Scrollable pitch-history view with a toolbar (Clear, Live)."""

    def __init__(self, parent, **kwargs):
        super().__init__(parent, text="Pitch History", style='Custom.TLabelframe', **kwargs)
        self.note_history: list = []
        self.quantize: bool = True
        self.notation: str = DEFAULT_NOTATION
        self.min_midi: int = MIN_MIDI
        self.max_midi: int = MAX_MIDI
        self.auto_scroll: bool = True
        self._clear_callback = None

        # ── two canvases side-by-side ──
        canvas_row = tk.Frame(self, bg=COLOR_BG_DARK)
        canvas_row.pack(fill='both', expand=True, padx=5, pady=(5, 0))

        self.scale_canvas = tk.Canvas(canvas_row, width=_SCALE_W,
                                      bg=COLOR_BG_CANVAS, highlightthickness=0)
        self.scale_canvas.pack(side='left', fill='y')

        self.canvas = tk.Canvas(canvas_row, bg=COLOR_BG_CANVAS, highlightthickness=0)
        self.canvas.pack(side='left', fill='both', expand=True)

        # ── scrollbar ──
        scroll_frame = tk.Frame(self, bg=COLOR_BG_DARK)
        scroll_frame.pack(fill='x', padx=5, pady=(0, 0))
        self.scrollbar = ttk.Scrollbar(scroll_frame, orient='horizontal',
                                       command=self._on_scrollbar)
        self.scrollbar.pack(fill='x', expand=True)

        self.canvas.configure(xscrollcommand=self._sync_scrollbar)
        self.canvas.bind('<Configure>', self._on_canvas_resize)
        self.scale_canvas.bind('<Configure>', self._on_scale_resize)

        # ── toolbar ──
        toolbar = tk.Frame(self, bg=COLOR_BG_DARK)
        toolbar.pack(fill='x', padx=5, pady=(3, 5))

        self.clear_btn = ttk.Button(toolbar, text="Clear", command=self._on_clear)
        self.clear_btn.pack(side='left', padx=(0, 6))

        self.live_btn = ttk.Button(toolbar, text="◉ Live", command=self._on_live)
        self.live_btn.pack(side='left')

        # Detect manual scroll to disable auto-scroll
        self.canvas.bind('<ButtonPress-1>', self._on_canvas_click, add='+')
        self.canvas.bind('<MouseWheel>', self._on_mousewheel, add='+')

        # Internal
        self.block_ids: list[int] = []
        self._plot_top: int = 10
        self._plot_height: int = 100
        self._plot_bottom: int = 110
        self._scale_needs_redraw = True

        self._draw_scale()
        self.update_display()

    # ── viewport helpers ─────────────────────────────────────────────────

    def _get_visible_range(self):
        """Return (start_idx, end_idx) for visible range + one screen preload."""
        c = self.canvas
        visible_w = max(c.winfo_width(), 100)
        scroll_x = c.canvasx(0)

        draw_start = max(0, scroll_x - visible_w)           # one screen before
        draw_end = scroll_x + 2 * visible_w                  # one screen after

        start_idx = int(draw_start / _NOTE_GAP)
        end_idx = int(draw_end / _NOTE_GAP) + 1

        total = len(self.note_history)
        start_idx = max(0, start_idx)
        end_idx = min(total, end_idx)
        return start_idx, end_idx

    def _redraw_visible(self) -> None:
        """Redraw only the visible portion of the canvas + one screen preload."""
        c = self.canvas
        c.delete("block")
        self.block_ids.clear()

        history = self.note_history
        total = len(history)
        if total == 0:
            return

        h = c.winfo_height()
        if h < 10:
            h = 400

        start_idx, end_idx = self._get_visible_range()
        if start_idx >= end_idx:
            return

        # Draw grid lines only for the visible x-range
        draw_start_x = start_idx * _NOTE_GAP
        draw_end_x = end_idx * _NOTE_GAP

        for midi in range(self.min_midi, self.max_midi + 1):
            y = self._midi_to_y.get(midi)
            if y is None:
                continue
            c.create_line(draw_start_x, y, draw_end_x, y,
                          fill=COLOR_GRID_LINE, width=1, tags="block")

        # Draw note blocks only in the visible range
        for i in range(start_idx, end_idx):
            entry = history[i]
            if entry is None:
                continue
            midi_float, cents = entry
            y = self._get_y(midi_float)
            x = i * _NOTE_GAP
            color = self._get_color(cents)
            item = c.create_rectangle(x, y - 4, x + _NOTE_GAP - 1, y + 4,
                                      fill=color, outline='', tags="block")
            self.block_ids.append(item)

    # ── public API ────────────────────────────────────────────────────────

    def set_clear_callback(self, callback) -> None:
        """Register a callable that will clear history on the controller side."""
        self._clear_callback = callback

    def set_history(self, history: list) -> None:
        self.note_history = history
        self.update_display()

    def set_notation(self, notation: str) -> None:
        self.notation = notation
        self._scale_needs_redraw = True
        self._draw_scale()
        self.update_display()

    def set_quantize(self, quantize: bool) -> None:
        self.quantize = quantize
        self.update_display()

    def set_range(self, min_midi: int, max_midi: int) -> None:
        self.min_midi = min_midi
        self.max_midi = max_midi
        self._scale_needs_redraw = True
        self._draw_scale()
        self.update_display()

    # ── scale (fixed left column) ────────────────────────────────────────

    def _draw_scale(self) -> None:
        c = self.scale_canvas
        c.delete("all")
        h = c.winfo_height()
        if h < 10:
            h = 400
        top, bottom = 10, h - 10
        height = bottom - top

        self._plot_top = top
        self._plot_bottom = bottom
        self._plot_height = height

        self._midi_to_y = {}
        for midi in range(self.min_midi, self.max_midi + 1):
            frac = (midi - self.min_midi) / (self.max_midi - self.min_midi)
            self._midi_to_y[midi] = bottom - frac * height

        use_sharps = self.notation == "Sharps"
        letter_list = NOTE_SHARP_LETTER if use_sharps else NOTE_FLAT_LETTER
        solfege_list = NOTE_SHARP_SOLFEGE if use_sharps else NOTE_FLAT_SOLFEGE

        for midi in range(self.min_midi, self.max_midi + 1):
            y = self._midi_to_y[midi]
            c.create_line(0, y, _SCALE_W, y, fill=COLOR_GRID_LINE, width=1)
            note_idx = midi % 12
            label = f"{solfege_list[note_idx]} ({letter_list[note_idx]}{(midi // 12) - 1})"
            c.create_text(_SCALE_W - 4, y, text=label, fill=COLOR_GRID_LABEL,
                          font=("Helvetica", 9), anchor='e')

    def _on_scale_resize(self, event=None):
        if self._scale_needs_redraw or True:
            self._draw_scale()
            self._scale_needs_redraw = False

    # ── scrolling ─────────────────────────────────────────────────────────

    def _sync_scrollbar(self, first, last) -> None:
        self.scrollbar.set(first, last)
        # Update Live button state
        if hasattr(self, 'live_btn'):
            is_at_end = float(last) >= 0.999
            self.auto_scroll = is_at_end
            self.live_btn.configure(text="◉ Live" if is_at_end else "○ Live")

    def _on_scrollbar(self, *args) -> None:
        self.canvas.xview(*args)
        self.auto_scroll = False
        self._redraw_visible()

    def _on_canvas_click(self, event) -> None:
        self.auto_scroll = False

    def _on_mousewheel(self, event) -> None:
        # Windows: event.delta is multiple of 120
        self.canvas.xview_scroll(-int(event.delta / 30), 'units')
        self.auto_scroll = False
        self._redraw_visible()

    def _on_live(self) -> None:
        self.auto_scroll = True
        self.canvas.xview_moveto(1.0)
        self.live_btn.configure(text="◉ Live")

    # ── drawing ───────────────────────────────────────────────────────────

    def _on_canvas_resize(self, event=None):
        self.update_display()

    def update_display(self) -> None:
        if not hasattr(self, '_midi_to_y'):
            return

        c = self.canvas
        history = self.note_history
        total = len(history)

        if total == 0:
            c.delete("block")
            self.block_ids.clear()
            c.configure(scrollregion=(0, 0, 1, 1))
            return

        # Update scroll region (extra margin so last note isn't cut off)
        h = c.winfo_height()
        if h < 10:
            h = 400
        content_w = max(total * _NOTE_GAP + 20, c.winfo_width())
        c.configure(scrollregion=(0, 0, content_w, h))

        # Auto-scroll to end *before* drawing so we draw the right slice
        if self.auto_scroll:
            self.canvas.xview_moveto(1.0)

        # Only draw what's visible + one screen preload
        self._redraw_visible()

    # ── helpers ───────────────────────────────────────────────────────────

    def _get_y(self, midi_float: float) -> float:
        if self.quantize:
            return self._midi_to_y.get(round(midi_float), self._plot_bottom)
        midi_clamped = max(self.min_midi, min(self.max_midi, midi_float))
        frac = (midi_clamped - self.min_midi) / (self.max_midi - self.min_midi)
        return self._plot_bottom - frac * self._plot_height

    @staticmethod
    def _get_color(cents: float) -> str:
        a = abs(cents)
        if a < 5:
            return COLOR_ACCENT_PERFECT
        elif a < 20:
            return COLOR_ACCENT_NICE
        elif a < 50:
            return COLOR_ACCENT_GOOD
        return COLOR_ACCENT_BAD

    def _on_clear(self) -> None:
        if self._clear_callback:
            self._clear_callback()