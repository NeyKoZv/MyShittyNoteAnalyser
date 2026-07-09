import tkinter as tk
from tkinter import ttk
from constants import (MIN_MIDI, MAX_MIDI, INSTRUMENTS,
                       DEFAULT_SAMPLE_RATE, DEFAULT_BLOCK_SIZE,
                       BUFFER_OPTIONS, NOISE_THRESHOLD_DEFAULT,
                       NOISE_THRESHOLD_MIN, NOISE_THRESHOLD_MAX,
                       NOTATION_OPTIONS, DEFAULT_NOTATION, DEFAULT_INSTRUMENT,
                       COLOR_BG_DARK, COLOR_BG_INPUT, COLOR_FG_PRIMARY)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_label(parent: ttk.LabelFrame | tk.Frame, text: str, **kwargs) -> ttk.Label:
    """Create a styled label consistent with the dark theme."""
    return ttk.Label(parent, text=text, foreground=COLOR_FG_PRIMARY,
                     background=COLOR_BG_DARK, **kwargs)


def _style_popdown_on_open(cb: ttk.Combobox) -> None:
    """Set the postcommand so the dropdown listbox gets styled dark each time it opens."""
    cb_name = str(cb)
    cb.configure(postcommand=lambda: cb.tk.eval(
        f'::ConfigureComboboxPopdown {cb_name}'
    ))


# ---------------------------------------------------------------------------
# SettingsPanel
# ---------------------------------------------------------------------------

class SettingsPanel(ttk.LabelFrame):
    """Left-hand panel grouping all user-configurable settings into sections."""

    def __init__(self, parent: ttk.Frame | tk.Frame, **kwargs) -> None:
        super().__init__(parent, text="Settings", style='Custom.TLabelframe')
        self.parent = parent
        self.sample_rate: int = DEFAULT_SAMPLE_RATE

        # Callbacks set by the controller (NoteAnalyzerApp)
        self.toggle_callback = None
        self.buffer_callback = None
        self.device_callback = None
        self.notation_callback = None
        self.quantize_callback = None
        self.min_max_callback = None

        self._build_ui()

    # ------------------------------------------------------------------
    # UI construction
    # ------------------------------------------------------------------

    def _build_ui(self) -> None:
        """Build the complete settings layout from top to bottom."""
        container = tk.Frame(self, bg=COLOR_BG_DARK)
        container.pack(fill='x', padx=5, pady=5)

        row = 0
        row = self._add_audio_section(container, row)
        row = self._add_display_section(container, row)
        row = self._add_analysis_section(container, row)
        self._add_start_button(container, row)

        self.build_buffer_options()

    # -- Sections -------------------------------------------------------

    def _add_audio_section(self, parent: tk.Frame, start_row: int) -> int:
        """Microphone, noise threshold, buffer size."""
        r = start_row

        # --- section header ---
        _make_label(parent, "─ AUDIO ─", font=("Helvetica", 8, "bold")).grid(
            row=r, column=0, columnspan=3, sticky='w', padx=5, pady=(6, 0))
        r += 1

        # Microphone
        _make_label(parent, "Microphone:").grid(row=r, column=0, sticky='w', padx=5, pady=2)
        self.device_var = tk.StringVar()
        self.device_cb = ttk.Combobox(parent, textvariable=self.device_var, state='readonly')
        self.device_cb.grid(row=r, column=1, columnspan=2, padx=5, pady=2, sticky='w')
        self.device_cb.bind('<<ComboboxSelected>>', self._on_device_selected)
        _style_popdown_on_open(self.device_cb)
        r += 1

        # Noise threshold
        _make_label(parent, "Noise threshold:").grid(row=r, column=0, sticky='w', padx=5, pady=2)
        thr_frame = tk.Frame(parent, bg=COLOR_BG_DARK)
        thr_frame.grid(row=r, column=1, columnspan=2, padx=5, pady=2, sticky='w')
        self.threshold_var = tk.DoubleVar(value=NOISE_THRESHOLD_DEFAULT)
        threshold_scale = ttk.Scale(thr_frame, from_=NOISE_THRESHOLD_MIN, to=NOISE_THRESHOLD_MAX, orient='horizontal',
                                    variable=self.threshold_var, length=120,
                                    command=self._update_threshold_label)
        threshold_scale.pack(side='left')
        self.threshold_label = ttk.Label(thr_frame, text="0.010", foreground=COLOR_FG_PRIMARY,
                                         background=COLOR_BG_DARK, width=6)
        self.threshold_label.pack(side='left', padx=(6, 0))
        r += 1

        # Buffer size
        _make_label(parent, "Buffer size:").grid(row=r, column=0, sticky='w', padx=5, pady=2)
        self.buffer_var = tk.StringVar()
        self.buffer_cb = ttk.Combobox(parent, textvariable=self.buffer_var,
                                       state='readonly', width=24)
        self.buffer_cb.grid(row=r, column=1, columnspan=2, padx=5, pady=2, sticky='w')
        self.buffer_cb.bind('<<ComboboxSelected>>', self._on_buffer_selected)
        _style_popdown_on_open(self.buffer_cb)
        r += 1

        return r

    def _add_display_section(self, parent: tk.Frame, start_row: int) -> int:
        """Instrument transposition, notation, quantize toggle."""
        r = start_row

        _make_label(parent, "─ DISPLAY ─", font=("Helvetica", 8, "bold")).grid(
            row=r, column=0, columnspan=3, sticky='w', padx=5, pady=(6, 0))
        r += 1

        # Instrument
        _make_label(parent, "Instrument:").grid(row=r, column=0, sticky='w', padx=5, pady=2)
        self.instrument_var = tk.StringVar(value=DEFAULT_INSTRUMENT)
        instr_cb = ttk.Combobox(parent, textvariable=self.instrument_var,
                                values=list(INSTRUMENTS.keys()), state='readonly')
        instr_cb.grid(row=r, column=1, columnspan=2, padx=5, pady=2, sticky='w')
        _style_popdown_on_open(instr_cb)
        r += 1

        # Notation
        _make_label(parent, "Notation:").grid(row=r, column=0, sticky='w', padx=5, pady=2)
        self.notation_var = tk.StringVar(value=DEFAULT_NOTATION)
        notation_cb = ttk.Combobox(parent, textvariable=self.notation_var,
                                   values=NOTATION_OPTIONS, state='readonly')
        notation_cb.grid(row=r, column=1, columnspan=2, padx=5, pady=2, sticky='w')
        notation_cb.bind('<<ComboboxSelected>>', self._on_notation_selected)
        _style_popdown_on_open(notation_cb)
        r += 1

        # Quantize notes
        self.quantize_var = tk.BooleanVar(value=True)
        self.quantize_var.trace_add('write', self._on_quantize_changed)
        quantize_cb = ttk.Checkbutton(parent, text="Quantize to nearest semitone",
                                      variable=self.quantize_var, style='TCheckbutton')
        quantize_cb.grid(row=r, column=0, columnspan=3, sticky='w', padx=5, pady=2)
        r += 1

        # MIDI range
        range_frame = tk.Frame(parent, bg=COLOR_BG_DARK)
        range_frame.grid(row=r, column=0, columnspan=3, sticky='ew', padx=5, pady=(4, 0))
        _make_label(range_frame, "Range:").pack(side='left')
        self.min_midi_var = tk.IntVar(value=MIN_MIDI)
        self.max_midi_var = tk.IntVar(value=MAX_MIDI)
        self.min_spin = ttk.Spinbox(range_frame, from_=0, to=127, width=4,
                                    textvariable=self.min_midi_var)
        self.min_spin.pack(side='left', padx=(4, 2))
        ttk.Label(range_frame, text="to", foreground=COLOR_FG_PRIMARY,
                  background=COLOR_BG_DARK).pack(side='left')
        self.max_spin = ttk.Spinbox(range_frame, from_=0, to=127, width=4,
                                    textvariable=self.max_midi_var)
        self.max_spin.pack(side='left', padx=(2, 4))
        self.min_midi_var.trace_add('write', self._on_min_max_changed)
        self.max_midi_var.trace_add('write', self._on_min_max_changed)
        r += 1

        return r

    def _add_analysis_section(self, parent: tk.Frame, start_row: int) -> int:
        """Behaviour toggles: continue on silence, aubio."""
        r = start_row

        _make_label(parent, "─ ANALYSIS ─", font=("Helvetica", 8, "bold")).grid(
            row=r, column=0, columnspan=3, sticky='w', padx=5, pady=(6, 0))
        r += 1

        # Continue on silence
        self.continue_var = tk.BooleanVar(value=False)
        continue_cb = ttk.Checkbutton(parent, text="Continue on silence",
                                      variable=self.continue_var, style='TCheckbutton')
        continue_cb.grid(row=r, column=0, columnspan=3, sticky='w', padx=5, pady=2)
        r += 1

        # Use aubio
        self.use_aubio_var = tk.BooleanVar(value=True)
        aubio_cb = ttk.Checkbutton(parent, text="Use aubio (faster detection)",
                                   variable=self.use_aubio_var, style='TCheckbutton')
        aubio_cb.grid(row=r, column=0, columnspan=3, sticky='w', padx=5, pady=2)
        r += 1

        return r

    def _add_start_button(self, parent: tk.Frame, row: int) -> None:
        """Start/Stop toggle button spanning the full width."""
        self.start_btn = ttk.Button(parent, text="▶  Start")
        self.start_btn.grid(row=row, column=0, columnspan=3, pady=(12, 4), ipadx=10)

    # ------------------------------------------------------------------
    # Event handlers
    # ------------------------------------------------------------------

    def _update_threshold_label(self, value: str) -> None:
        """Keep the numeric label next to the slider in sync."""
        self.threshold_label.config(text=f"{float(value):.3f}")

    def _on_device_selected(self, event) -> None:
        """Microphone dropdown changed → notify controller to refresh sample rate."""
        if self.device_callback:
            self.device_callback()

    def _on_buffer_selected(self, event) -> None:
        """Buffer-size dropdown changed → notify controller to restart the stream."""
        selected = self.buffer_var.get()
        try:
            buffer_val = int(selected.split()[0])
            if self.buffer_callback:
                self.buffer_callback(buffer_val)
        except (ValueError, IndexError):
            pass

    def _on_notation_selected(self, event) -> None:
        """Notation dropdown changed → notify controller to redraw the scale."""
        if self.notation_callback:
            self.notation_callback()

    def _on_quantize_changed(self, *_args) -> None:
        """Quantize checkbox toggled → notify controller to redraw history."""
        if self.quantize_callback:
            self.quantize_callback()

    def _on_min_max_changed(self, *_args) -> None:
        """MIDI range spinboxes changed → notify controller to redraw scales."""
        if self.min_max_callback:
            self.min_max_callback()

    # ------------------------------------------------------------------
    # Public API  (called by NoteAnalyzerApp)
    # ------------------------------------------------------------------

    def set_sample_rate(self, sr: int) -> None:
        """Update the displayed sample rate and rebuild buffer dropdown choices."""
        self.sample_rate = sr
        current = self.buffer_var.get()
        self.build_buffer_options()
        # Restore previous selection if still valid, else fallback to 2048
        if current in self.buffer_cb['values']:
            self.buffer_var.set(current)
        else:
            default_display = f"2048  (min {sr / 2048:.0f} Hz)"
            if default_display in self.buffer_cb['values']:
                self.buffer_var.set(default_display)
            elif self.buffer_cb['values']:
                self.buffer_var.set(self.buffer_cb['values'][0])

    def build_buffer_options(self) -> None:
        """Fill the buffer-size combobox with entries like '2048  (min 21 Hz)'."""
        sr = self.sample_rate
        buffer_values = BUFFER_OPTIONS
        self.buffer_to_display = {}
        self.display_to_buffer = {}
        display_options = []
        for b in buffer_values:
            low_freq = sr / b
            display_str = f"{b}  (min {low_freq:.0f} Hz)"
            display_options.append(display_str)
            self.buffer_to_display[b] = display_str
            self.display_to_buffer[display_str] = b

        self.buffer_cb['values'] = display_options
        # Auto-select 2048 if nothing sensible is already chosen
        if not self.buffer_var.get() or self.buffer_var.get() not in display_options:
            default_str = f"2048  (min {sr / 2048:.0f} Hz)"
            if default_str in display_options:
                self.buffer_var.set(default_str)
            elif display_options:
                self.buffer_var.set(display_options[0])

    def populate_devices(self, device_list: list[str]) -> None:
        """Fill the microphone combobox with available input devices."""
        if device_list:
            self.device_cb['values'] = device_list
            self.device_var.set(device_list[0])
        else:
            self.device_var.set("No input device found")

    # -- Callback setters -----------------------------------------------

    def set_start_stop_callback(self, callback) -> None:
        self.toggle_callback = callback
        self.start_btn.config(command=callback)

    def set_buffer_callback(self, callback) -> None:
        self.buffer_callback = callback

    def set_device_callback(self, callback) -> None:
        self.device_callback = callback

    def set_notation_callback(self, callback) -> None:
        self.notation_callback = callback

    def set_quantize_callback(self, callback) -> None:
        self.quantize_callback = callback

    def set_min_max_callback(self, callback) -> None:
        self.min_max_callback = callback

    # -- Setting accessors ----------------------------------------------

    def get_device(self) -> str:
        return self.device_var.get()

    def get_instrument(self) -> str:
        return self.instrument_var.get()

    def get_notation(self) -> str:
        return self.notation_var.get()

    def get_threshold(self) -> float:
        return self.threshold_var.get()

    def get_buffer_size(self) -> int:
        selected = self.buffer_var.get()
        try:
            return int(selected.split()[0])
        except (ValueError, IndexError):
            return DEFAULT_BLOCK_SIZE

    def get_quantize(self) -> bool:
        return self.quantize_var.get()

    def get_min_midi(self) -> int:
        return self.min_midi_var.get()

    def get_max_midi(self) -> int:
        return self.max_midi_var.get()

    def get_continue(self) -> bool:
        return self.continue_var.get()

    def get_use_aubio(self) -> bool:
        return self.use_aubio_var.get()

    def get_use_aubio(self) -> bool:
        return self.use_aubio_var.get()