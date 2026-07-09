import tkinter as tk
from tkinter import ttk
import sounddevice as sd
import threading
import queue
import re
import numpy as np
from collections import deque
from constants import (INSTRUMENTS, NOTE_SHARP_LETTER, NOTE_SHARP_SOLFEGE,
                       NOTE_FLAT_LETTER, NOTE_FLAT_SOLFEGE,
                       COLOR_BG_DARK, COLOR_BG_INPUT, COLOR_BG_DARKER,
                       COLOR_FG_PRIMARY, COLOR_BUTTON_ACTIVE,
                       COLOR_ACCENT_PERFECT, COLOR_ACCENT_NICE,
                       COLOR_ACCENT_GOOD, COLOR_ACCENT_BAD, COLOR_ERROR,
                       NOTE_HISTORY_MAXLEN, DEFAULT_SAMPLE_RATE,
                       DEFAULT_BLOCK_SIZE, APP_GEOMETRY,
                       DEFAULT_NOTATION)
from pitch_detector import detect_pitch, freq_to_midi
from settings_panel import SettingsPanel
from tuner_panel import TunerPanel
from history_panel import HistoryPanel
from info_panel import InfoPanel


class NoteAnalyzerApp:
    """Main application controller — wires audio capture to the UI panels."""

    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("Note Analyzer")
        self.root.geometry(APP_GEOMETRY)
        self.root.configure(bg=COLOR_BG_DARK)

        # Audio parameters
        self.sample_rate: int = DEFAULT_SAMPLE_RATE
        self.current_block_size: int = DEFAULT_BLOCK_SIZE

        # State
        self.is_running: bool = False
        self.audio_queue: queue.Queue = queue.Queue()
        self.stream: sd.InputStream | None = None

        # Thread-safe note history
        self.note_history: deque = deque(maxlen=NOTE_HISTORY_MAXLEN)
        self._history_lock = threading.Lock()

        # GUI coalescing – avoid flooding the main thread with redraws
        self.update_pending: bool = False
        self.pending_midi: float | None = None

        self._setup_styles()

        self._create_panels()
        self._populate_devices()

        # Wire up callbacks
        self.settings_panel.set_start_stop_callback(self.toggle_analysis)
        self.settings_panel.set_buffer_callback(self._on_buffer_changed)
        self.settings_panel.set_device_callback(self._on_device_changed)
        self.settings_panel.set_notation_callback(self._on_notation_changed)
        self.settings_panel.set_quantize_callback(self._on_quantize_changed)
        self.settings_panel.set_min_max_callback(self._on_min_max_changed)

        self.current_block_size = self.settings_panel.get_buffer_size()

    # ------------------------------------------------------------------
    # Theming
    # ------------------------------------------------------------------

    def _setup_styles(self) -> None:
        """Configure ttk styles for the dark theme used across all panels."""
        style = ttk.Style()
        style.theme_use('clam')
        style.configure('Custom.TLabelframe', background=COLOR_BG_DARK,
                        foreground=COLOR_FG_PRIMARY, borderwidth=2)
        style.configure('Custom.TLabelframe.Label', foreground=COLOR_FG_PRIMARY,
                        background=COLOR_BG_DARK)
        style.configure('TCombobox',
                        fieldbackground=COLOR_BG_INPUT,
                        background=COLOR_BG_DARK,
                        foreground=COLOR_FG_PRIMARY,
                        arrowcolor=COLOR_FG_PRIMARY)
        style.map('TCombobox',
                  fieldbackground=[('readonly', COLOR_BG_INPUT)],
                  foreground=[('readonly', COLOR_FG_PRIMARY)])
        # Register a tcl helper to style the combobox popdown listbox
        style.tk.eval("""
            proc ::ConfigureComboboxPopdown {cb} {
                if {[info exists ttk::combobox::${cb}(popdown)]} {
                    set pop $ttk::combobox::${cb}(popdown)
                    catch {
                        $pop.f.l configure -background #2b2b2b -foreground white \
                                           -selectbackground #555555 -selectforeground white
                    }
                }
            }
        """)
        style.configure('TButton', background=COLOR_BG_INPUT,
                        foreground=COLOR_FG_PRIMARY)
        style.map('TButton', background=[('active', COLOR_BUTTON_ACTIVE)])
        style.configure('TCheckbutton', foreground=COLOR_FG_PRIMARY,
                        background=COLOR_BG_DARK)
        style.map('TCheckbutton',
                  background=[('active', COLOR_BG_INPUT), ('selected', COLOR_BG_DARK)],
                  foreground=[('active', COLOR_FG_PRIMARY), ('selected', COLOR_FG_PRIMARY)])

    def _create_panels(self) -> None:
        """Build the three-panel layout: settings, tuner, history, and info bar."""
        top_frame = tk.Frame(self.root, bg=COLOR_BG_DARK)
        top_frame.pack(fill='x', padx=10, pady=5)

        self.settings_panel = SettingsPanel(top_frame)
        self.settings_panel.grid(row=0, column=0, sticky='nsew')

        self.tuner_panel = TunerPanel(top_frame)
        self.tuner_panel.grid(row=0, column=1, sticky='ns', padx=10, pady=5)

        top_frame.columnconfigure(0, weight=1)
        top_frame.columnconfigure(1, weight=0)

        self.history_panel = HistoryPanel(self.root)
        self.history_panel.pack(fill='both', expand=True, padx=10, pady=5)

        self.info_panel = InfoPanel(self.root)
        self.info_panel.pack(fill='x', padx=10, pady=5)

        self.tuner_panel.bind('<Configure>', lambda e: self.tuner_panel.on_resize(e))
        self.history_panel.set_clear_callback(self._on_clear_history)

    def _populate_devices(self) -> None:
        """Query system audio inputs and populate the microphone combobox."""
        devices = sd.query_devices()
        input_devices = []
        for i, dev in enumerate(devices):
            if dev['max_input_channels'] > 0:
                input_devices.append(f"{dev['name']} (index {i})")
        self.settings_panel.populate_devices(input_devices)
        self._on_device_changed()

    def _get_device_index(self):
        """Extract the numeric device index from the settings combobox."""
        selected = self.settings_panel.get_device()
        match = re.search(r'\(index (\d+)\)', selected)
        if match:
            return int(match.group(1))
        device = sd.default.device
        return device[0] if isinstance(device, tuple) else device

    def _on_device_changed(self):
        """React to a microphone change — refresh sample rate & restart if active."""
        device_idx = self._get_device_index()
        try:
            dev_info = sd.query_devices(device_idx)
            sr = dev_info.get('default_samplerate', DEFAULT_SAMPLE_RATE)
        except Exception:
            sr = self.sample_rate  # fallback to current value
        self.sample_rate = int(sr)
        self.settings_panel.set_sample_rate(self.sample_rate)
        if self.is_running:
            self.stop_analysis()
            self.start_analysis()

    def _on_buffer_changed(self, new_block_size: int) -> None:
        """React to a buffer-size change — update & restart if active."""
        self.current_block_size = int(new_block_size)
        if self.is_running:
            self.stop_analysis()
            self.start_analysis()

    def _on_notation_changed(self) -> None:
        """Redraw the history and tuner scales immediately when notation changes."""
        notation = self.settings_panel.get_notation()
        self.history_panel.set_notation(notation)

    def _on_quantize_changed(self) -> None:
        """Refresh the history display immediately when quantize toggles."""
        self.history_panel.set_quantize(self.settings_panel.get_quantize())

    def _on_min_max_changed(self) -> None:
        """Refresh both panels when the MIDI range changes."""
        min_midi = self.settings_panel.get_min_midi()
        max_midi = self.settings_panel.get_max_midi()
        self.tuner_panel.set_range(min_midi, max_midi)
        self.history_panel.set_range(min_midi, max_midi)

    def toggle_analysis(self) -> None:
        """Start or stop the audio analysis pipeline."""
        if self.is_running:
            self.stop_analysis()
        else:
            self.start_analysis()

    def start_analysis(self) -> None:
        """Open an audio input stream and launch the processing thread."""
        device_idx = self._get_device_index()
        block_size = self.current_block_size
        sr = self.sample_rate

        try:
            self.stream = sd.InputStream(
                device=device_idx,
                channels=1,
                samplerate=sr,
                blocksize=block_size,
                callback=self.audio_callback
            )
            self.stream.start()
            self.is_running = True
            self.settings_panel.start_btn.config(text="⏹  Stop")
            self.processing_thread = threading.Thread(target=self.process_audio, daemon=True)
            self.processing_thread.start()
        except Exception as e:
            self.info_panel.acc_label.config(text=f"ERROR: {e}", fg=COLOR_ERROR)

    def stop_analysis(self) -> None:
        """Close the audio stream, stop the processing thread, and flush the queue."""
        self.is_running = False
        self.update_pending = False
        self.pending_midi = None
        if self.stream:
            self.stream.stop()
            self.stream.close()
            self.stream = None
        self.settings_panel.start_btn.config(text="▶  Start")
        while not self.audio_queue.empty():
            try:
                self.audio_queue.get_nowait()
            except queue.Empty:
                break

    def audio_callback(self, indata, frames, time_info, status) -> None:
        """Called by sounddevice on a background thread for each audio block."""
        if status:
            print("Audio status:", status)
        self.audio_queue.put(indata.copy())

    def process_audio(self) -> None:
        """Worker thread loop: pull audio from the queue, detect pitch, update state."""
        while self.is_running:
            try:
                data = self.audio_queue.get(timeout=0.1)
            except queue.Empty:
                continue
            audio = data.flatten()

            rms = np.sqrt(np.mean(audio**2))
            threshold = self.settings_panel.get_threshold()
            if rms < threshold:
                if self.settings_panel.get_continue():
                    with self._history_lock:
                        self.note_history.append(None)
                    self.schedule_gui_update(midi=None)
                continue

            use_aubio = self.settings_panel.get_use_aubio()
            freq = detect_pitch(audio, self.sample_rate, self.current_block_size, use_aubio=use_aubio)
            if freq is not None and freq > 0:
                midi = freq_to_midi(freq)
                if midi is None:
                    continue
                instr = self.settings_panel.get_instrument()
                offset = INSTRUMENTS.get(instr, 0)
                midi_written = midi + offset
                midi_rounded = round(midi_written)
                cents = (midi_written - midi_rounded) * 100

                with self._history_lock:
                    self.note_history.append((midi_written, cents))

                note_idx = midi_rounded % 12
                notation = self.settings_panel.get_notation()
                if notation == DEFAULT_NOTATION:
                    letter = NOTE_SHARP_LETTER[note_idx]
                    solfege = NOTE_SHARP_SOLFEGE[note_idx]
                else:
                    letter = NOTE_FLAT_LETTER[note_idx]
                    solfege = NOTE_FLAT_SOLFEGE[note_idx]

                self.root.after(0, self._update_info, solfege, letter, cents)
                self.schedule_gui_update(midi=midi_written)

    def schedule_gui_update(self, midi: float | None = None) -> None:
        """Coalesce tuner + history redraws so the main thread isn't flooded."""
        if self.update_pending:
            if midi is not None:
                self.pending_midi = midi
            return
        self.pending_midi = midi
        self.update_pending = True
        self.root.after_idle(self._perform_gui_update)

    def _perform_gui_update(self) -> None:
        """Batch-redraw the tuner and history when the main thread is idle."""
        self.update_pending = False
        midi_to_use = self.pending_midi
        self.pending_midi = None

        if midi_to_use is not None:
            self._update_tuner(midi_to_use)
        else:
            self._update_tuner(None)

        self._update_history()

    def _update_info(self, solfege: str, letter: str, cents: float) -> None:
        """Derive accuracy label/color from the cents deviation and push to the info panel."""
        abs_cents = abs(cents)
        if abs_cents < 5:
            acc = "Perfect"
            color = COLOR_ACCENT_PERFECT
        elif abs_cents < 20:
            acc = "Nice"
            color = COLOR_ACCENT_NICE
        elif abs_cents < 50:
            acc = "Good"
            color = COLOR_ACCENT_GOOD
        else:
            acc = "Bad"
            color = COLOR_ACCENT_BAD
        self.info_panel.update_info(solfege, letter, acc, color, cents)

    def _update_tuner(self, midi_float: float | None) -> None:
        """Forward the current MIDI value to the tuner panel."""
        self.tuner_panel.update_tuner(midi_float)

    def _on_clear_history(self) -> None:
        """Clear all note history and refresh the display."""
        with self._history_lock:
            self.note_history.clear()
        self._update_history()

    def _update_history(self) -> None:
        """Copy the latest note history to the history panel."""
        with self._history_lock:
            history_copy = list(self.note_history)
            used = len(self.note_history)
        self.history_panel.set_history(history_copy)
        self.info_panel.set_memory_usage(used, NOTE_HISTORY_MAXLEN)
        quantize = self.settings_panel.get_quantize()
        notation = self.settings_panel.get_notation()
        if not hasattr(self.history_panel, 'notation') or self.history_panel.notation != notation:
            self.history_panel.set_notation(notation)
        if self.history_panel.quantize != quantize:
            self.history_panel.set_quantize(quantize)

    def on_closing(self) -> None:
        """Clean shutdown — stop analysis and destroy the window."""
        self.stop_analysis()
        self.root.destroy()