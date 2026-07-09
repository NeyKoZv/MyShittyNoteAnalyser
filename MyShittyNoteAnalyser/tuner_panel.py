import tkinter as tk
from constants import (MIN_MIDI, MAX_MIDI, NOTE_SHARP_LETTER,
                       COLOR_BG_DARKER, COLOR_TUNER_TICK, COLOR_TUNER_LABEL,
                       COLOR_ACCENT_PERFECT,
                       TUNER_WIDTH, TUNER_HEIGHT, TUNER_MARGIN, TUNER_DOT_RADIUS)


class TunerPanel(tk.Frame):
    """Vertical slider showing the current note position against the selectable MIDI range."""

    def __init__(self, parent, **kwargs):
        super().__init__(parent, bg=COLOR_BG_DARKER, relief='sunken', bd=2, **kwargs)
        self.canvas = tk.Canvas(self, width=TUNER_WIDTH, height=TUNER_HEIGHT,
                                bg=COLOR_BG_DARKER, highlightthickness=0)
        self.canvas.pack(fill='both', expand=True)
        self.min_midi = MIN_MIDI
        self.max_midi = MAX_MIDI
        self.draw_scale()

    def set_range(self, min_midi: int, max_midi: int) -> None:
        """Update the visible MIDI range and redraw the scale."""
        self.min_midi = min_midi
        self.max_midi = max_midi
        self.draw_scale()

    def draw_scale(self):
        self.canvas.delete("all")
        w = self.canvas.winfo_width()
        h = self.canvas.winfo_height()
        if w < 10:
            w = TUNER_WIDTH
        if h < 10:
            h = TUNER_HEIGHT

        margin = TUNER_MARGIN
        plot_top = margin
        plot_bottom = h - margin
        plot_height = plot_bottom - plot_top

        self.tuner_plot_bottom = plot_bottom
        self.tuner_plot_height = plot_height

        if self.max_midi <= self.min_midi:
            return

        for midi in range(self.min_midi, self.max_midi + 1, 3):
            frac = (midi - self.min_midi) / (self.max_midi - self.min_midi)
            y = plot_bottom - frac * plot_height
            self.canvas.create_line(w-10, y, w, y, fill=COLOR_TUNER_TICK)
            note_idx = midi % 12
            letter = NOTE_SHARP_LETTER[note_idx]
            octave = (midi // 12) - 1
            self.canvas.create_text(w-12, y, text=f"{letter}{octave}", fill=COLOR_TUNER_LABEL,
                                    font=("Helvetica", 7), anchor='e')

        self.tuner_dot = self.canvas.create_oval(0, 0, 0, 0,
                                                  fill=COLOR_ACCENT_PERFECT, outline='')

    def update_tuner(self, midi_float):
        if midi_float is None:
            self.canvas.coords(self.tuner_dot, -10, -10, -10, -10)
            return
        w = self.canvas.winfo_width()
        if w < 10:
            w = 80
        midi_clamped = max(self.min_midi, min(self.max_midi, midi_float))
        frac = (midi_clamped - self.min_midi) / (self.max_midi - self.min_midi)
        y = self.tuner_plot_bottom - frac * self.tuner_plot_height
        r = TUNER_DOT_RADIUS
        self.canvas.coords(self.tuner_dot, w/2 - r, y - r, w/2 + r, y + r)
        self.canvas.tag_raise(self.tuner_dot)

    def on_resize(self, event):
        self.draw_scale()