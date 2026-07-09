import tkinter as tk
from tkinter import ttk
from constants import (COLOR_BG_DARKER, COLOR_BG_CANVAS,
                       COLOR_BG_METER, COLOR_FG_PRIMARY,
                       COLOR_FG_SECONDARY, COLOR_METER_TICK,
                       COLOR_METER_CENTER,
                       METER_WIDTH, METER_HEIGHT)

class InfoPanel(tk.Frame):
    """Bottom bar showing the detected note name, accuracy, and a cents deviation meter."""

    def __init__(self, parent, **kwargs):
        super().__init__(parent, bg=COLOR_BG_DARKER, **kwargs)
        self._build_widgets()

    def _build_widgets(self):
        # Note & accuracy label (large text, color changes with accuracy)
        self.acc_label = tk.Label(self, text="", font=("Helvetica", 18),
                                  bg=COLOR_BG_DARKER, fg=COLOR_FG_PRIMARY)
        self.acc_label.pack(side='left', padx=10)

        # Deviation detail
        self.detail_label = tk.Label(self, text="", font=("Helvetica", 12),
                                     bg=COLOR_BG_DARKER, fg=COLOR_FG_SECONDARY)
        self.detail_label.pack(side='left', padx=10)

        # Cents deviation meter (range: -50 to +50 cents)
        meter_frame = tk.Frame(self, bg=COLOR_BG_DARKER)
        meter_frame.pack(side='left', padx=20)
        self.cents_canvas = tk.Canvas(meter_frame, width=METER_WIDTH, height=METER_HEIGHT,
                                      bg=COLOR_BG_METER, highlightthickness=1,
                                      highlightcolor=COLOR_FG_PRIMARY)
        self.cents_canvas.pack()
        # Tick marks at -50, -25, 0, +25, +50 cents
        for x in (0, 37, 75, 112, 150):
            self.cents_canvas.create_line(x, 0, x, 4, fill=COLOR_METER_TICK)
        self.cents_canvas.create_line(75, 0, 75, 15, fill=COLOR_METER_CENTER, width=2)
        self.indicator = self.cents_canvas.create_rectangle(70, 2, 80, 13, fill='green')

        # Memory usage indicator (bottom-right)
        self.memory_label = tk.Label(self, text="", font=("Helvetica", 9),
                                     bg=COLOR_BG_DARKER, fg=COLOR_FG_SECONDARY)
        self.memory_label.pack(side='right', padx=10)

    def set_memory_usage(self, used: int, total: int) -> None:
        """Update the memory usage indicator with used/total note count."""
        pct = (used / total) * 100 if total > 0 else 0
        self.memory_label.config(text=f"{pct:.0f}% used ({used:,} / {total:,})")

    def update_info(self, solfege, letter, acc_text, color, cents):
        self.acc_label.config(text=f"{solfege} ({letter})  {acc_text}", fg=color)
        self.detail_label.config(text=f"Deviation: {cents:+.1f} cents")
        # Cents meter
        x = 75 + (cents / 50) * 75
        x = max(0, min(150, x))
        self.cents_canvas.coords(self.indicator, x-5, 2, x+5, 13)
        self.cents_canvas.itemconfig(self.indicator, fill=color)