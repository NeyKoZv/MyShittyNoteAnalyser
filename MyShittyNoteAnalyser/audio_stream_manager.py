"""
Audio stream manager — owns the sounddevice InputStream lifecycle,
background processing thread, GUI coalescing, and note history.

Extracted from gui.py as part of Phase 3 refactoring.
"""
import queue
import threading
import logging

import numpy as np
import sounddevice as sd
from collections import deque
from PyQt6.QtCore import QTimer, QObject, pyqtSignal

from MyShittyNoteAnalyser.constants import (INSTRUMENTS, NOTE_HISTORY_MAXLEN,
                                            DEFAULT_SAMPLE_RATE, DEFAULT_BLOCK_SIZE)
from MyShittyNoteAnalyser.pitch_detector import detect_pitch, freq_to_midi
from MyShittyNoteAnalyser.app_state import AppState, validate_transition

_logger = logging.getLogger(__name__)


class AudioStreamManager(QObject):
    """Manages audio capture, pitch detection, and GUI coalescing.

    Inherits from QObject and uses a pyqtSignal for cross-thread
    dispatch from the processing thread to the main event loop.

    The manager does NOT know about UI panels. It communicates results
    via callbacks set by the controller:

        manager.on_rms = fn(rms: float)
        manager.on_pitch = fn(midi: float | None, cents: float | None)
        manager.on_history_updated = fn(history: list, used: int)
        manager.on_error = fn(msg: str)
    """

    # Signal for cross-thread dispatch from daemon thread → main loop
    _update_ready = pyqtSignal()

    def __init__(self):
        super().__init__()
        self._update_ready.connect(self._perform_gui_update)
        # ── audio parameters ────────────────────────────────────
        self.sample_rate: int = DEFAULT_SAMPLE_RATE
        self.current_block_size: int = DEFAULT_BLOCK_SIZE

        # ── state ───────────────────────────────────────────────
        self.state: AppState = AppState.IDLE
        self.is_running: bool = False
        self._full_analysis: bool = False
        self.audio_queue: queue.Queue = queue.Queue()
        self.stream: sd.InputStream | None = None
        self.processing_thread: threading.Thread | None = None

        # ── pitch detection settings (updated externally) ──────
        self.noise_threshold: float = 0.02
        self.instrument_name: str = "Concert (C)"
        self.use_aubio: bool = True
        self.continue_on_silence: bool = False

        # Thread-safe note history
        self.note_history: deque = deque(maxlen=NOTE_HISTORY_MAXLEN)
        self._history_lock = threading.Lock()

        # GUI coalescing — lock protects update_pending + pending_* values
        # so that the audio thread and main thread never race on reads/writes.
        self._coalesce_lock = threading.Lock()
        self.update_pending: bool = False
        self.pending_midi: float | None = None
        self.pending_cents: float | None = None
        self.pending_rms: float | None = None

        # Device name → index lookup
        self._device_name_to_index: dict = {}

        # ── callbacks (set by controller) ───────────────────────
        self.on_rms = None              # fn(rms: float)
        self.on_pitch = None            # fn(midi: float | None, cents: float | None)
        self.on_history_updated = None  # fn(history: list, used: int)
        self.on_error = None            # fn(msg: str)

    # ── device management ───────────────────────────────────────

    def enumerate_devices(self) -> list[str]:
        """Return a list of clean input-device names and populate lookup."""
        devices = sd.query_devices()
        self._device_name_to_index.clear()
        clean_names = []
        for i, dev in enumerate(devices):
            if dev['max_input_channels'] > 0:
                name = dev['name']
                self._device_name_to_index[name] = i
                clean_names.append(name)
        return clean_names

    def get_device_index(self, selected_name: str | None = None) -> int:
        """Resolve a device name to an index. Falls back to system default."""
        if selected_name is not None:
            idx = self._device_name_to_index.get(selected_name)
            if idx is not None:
                return idx
        device = sd.default.device
        return device[0] if isinstance(device, tuple) else device

    def query_sample_rate(self, device_idx: int) -> int:
        """Get the default sample rate for a device."""
        try:
            dev_info = sd.query_devices(device_idx)
            return int(dev_info.get('default_samplerate', DEFAULT_SAMPLE_RATE))
        except Exception:
            return DEFAULT_SAMPLE_RATE

    # ── stream lifecycle ────────────────────────────────────────

    def start_stream(self, device_idx: int, block_size: int,
                     sample_rate: int) -> None:
        """Start RMS-only streaming (no pitch detection)."""
        if self.is_running:
            return

        validate_transition(self.state, AppState.RMS_ONLY)

        self.sample_rate = sample_rate
        self.current_block_size = block_size

        try:
            self.stream = sd.InputStream(
                device=device_idx,
                channels=1,
                samplerate=sample_rate,
                blocksize=block_size,
                callback=self._audio_callback,
            )
            self.stream.start()
            self.is_running = True
            self.state = AppState.RMS_ONLY
            self.processing_thread = threading.Thread(
                target=self._process_audio, daemon=True)
            self.processing_thread.start()
        except Exception as e:
            if self.on_error:
                self.on_error(str(e))
            raise

    def stop_stream(self) -> None:
        """Stop the audio stream and processing thread."""
        self.is_running = False
        self._full_analysis = False
        self.update_pending = False
        self.pending_midi = None
        self.pending_cents = None
        self.pending_rms = None
        self.state = AppState.IDLE

        if self.stream:
            try:
                self.stream.stop()
                self.stream.close()
            except Exception:
                pass
            self.stream = None

        # Drain queue
        while not self.audio_queue.empty():
            try:
                self.audio_queue.get_nowait()
            except queue.Empty:
                break

    def restart_stream(self, device_idx: int, block_size: int,
                       sample_rate: int) -> None:
        """Restart preserving the current _full_analysis state."""
        was_full = self._full_analysis
        self.stop_stream()
        self.start_stream(device_idx, block_size, sample_rate)
        if was_full:
            self.enable_full_analysis()

    def enable_full_analysis(self) -> None:
        """Enable pitch detection + history recording."""
        if self.state == AppState.FULL_ANALYSIS:
            return  # already active — idempotent
        validate_transition(self.state, AppState.FULL_ANALYSIS)
        self._full_analysis = True
        self.state = AppState.FULL_ANALYSIS

    def disable_full_analysis(self) -> None:
        """Disable pitch detection; stream keeps running RMS-only."""
        if self.state == AppState.RMS_ONLY:
            return  # already RMS-only — idempotent
        validate_transition(self.state, AppState.RMS_ONLY)
        self._full_analysis = False
        self.update_pending = False
        self.pending_midi = None
        self.pending_cents = None
        self.pending_rms = None
        self.state = AppState.RMS_ONLY

    @property
    def full_analysis_active(self) -> bool:
        return self._full_analysis

    # ── audio callback (called from PortAudio thread) ───────────

    def _audio_callback(self, indata, frames, time_info, status) -> None:
        if status:
            _logger.warning("Audio status: %s", status)
        self.audio_queue.put(indata.copy())

    # ── background processing thread ────────────────────────────

    def _process_audio(self) -> None:
        """Main processing loop: RMS → pitch detection → GUI coalescing."""
        while self.is_running:
            try:
                data = self.audio_queue.get(timeout=0.1)
            except queue.Empty:
                continue

            try:
                audio = data.flatten()
                rms = float(np.sqrt(np.mean(audio ** 2)))

                # Always report RMS
                self._schedule_gui_update(midi=None, rms=rms)

                if not self._full_analysis:
                    continue

                if rms < self.noise_threshold:
                    if self.continue_on_silence:
                        with self._history_lock:
                            self.note_history.append(None)
                        self._schedule_gui_update(midi=None, rms=rms)
                    continue

                freq = detect_pitch(audio, self.sample_rate,
                                    self.current_block_size,
                                    use_aubio=self.use_aubio)
                if freq is None or freq <= 0:
                    continue

                midi = freq_to_midi(freq)
                if midi is None:
                    continue

                offset = INSTRUMENTS.get(self.instrument_name, 0)
                midi_written = midi + offset
                midi_rounded = round(midi_written)
                cents = (midi_written - midi_rounded) * 100

                with self._history_lock:
                    self.note_history.append((midi_written, cents))

                self._schedule_gui_update(midi=midi_written, cents=cents,
                                           rms=rms)
            except Exception as e:
                # Don't let a single bad frame kill the thread
                _logger.error("Audio processing error: %s", e, exc_info=True)

    # ── GUI coalescing ──────────────────────────────────────────

    def _schedule_gui_update(self, midi: float | None = None,
                              cents: float | None = None,
                              rms: float | None = None) -> None:
        """Coalesce rapid updates into a single Qt event-loop tick.

        The coalescing block is guarded by a threading.Lock so that the
        check-and-set of update_pending + pending_* values is atomic
        across the audio and main threads.
        """
        with self._coalesce_lock:
            if self.update_pending:
                if midi is not None:
                    self.pending_midi = midi
                if cents is not None:
                    self.pending_cents = cents
                if rms is not None:
                    self.pending_rms = rms
                return
            self.pending_midi = midi
            self.pending_cents = cents
            self.pending_rms = rms
            self.update_pending = True
        self._update_ready.emit()  # cross-thread: queues on main event loop

    def _perform_gui_update(self) -> None:
        """Deliver coalesced data to the controller via callbacks."""
        with self._coalesce_lock:
            self.update_pending = False
            midi = self.pending_midi
            cents = self.pending_cents
            rms = self.pending_rms
            self.pending_midi = None
            self.pending_cents = None
            self.pending_rms = None

        # RMS callback
        if rms is not None and self.on_rms:
            self.on_rms(rms)

        # Pitch callback (midi + cents, or None for silence)
        if self.on_pitch:
            self.on_pitch(midi, cents)

        # History callback
        if self.on_history_updated:
            with self._history_lock:
                history_copy = list(self.note_history)
                used = len(self.note_history)
            self.on_history_updated(history_copy, used)

    # ── history management ──────────────────────────────────────

    def clear_history(self) -> None:
        with self._history_lock:
            self.note_history.clear()

    def get_history_copy(self) -> list:
        with self._history_lock:
            return list(self.note_history)
