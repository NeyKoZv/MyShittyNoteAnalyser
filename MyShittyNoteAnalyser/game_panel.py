"""
Core game panel — displays the target note (text or staff), tracks hold
time, manages score/streak, and shows a summary overlay on round end.

Sub-widgets have been extracted to:
  - note_utils.py        (midi_to_note_text helper)
  - staff_canvas.py      (StaffCanvas)
  - hold_progress_bar.py (HoldProgressBar)
  - game_overlay.py      (GameOverlay)
"""
import random
import time

from PyQt6.QtWidgets import (QWidget, QLabel, QVBoxLayout)
from PyQt6.QtGui import QFont
from PyQt6.QtCore import Qt, pyqtSignal

from MyShittyNoteAnalyser.constants import (MIN_MIDI, MAX_MIDI)
from MyShittyNoteAnalyser.game_constants import (
    GAME_BG, GAME_NOTEHEAD,
    GAME_TARGET_TEXT, GAME_CORRECT, GAME_WRONG,
    GAME_FEEDBACK_BG, GAME_STATS,
    GAME_TOP_BAR_HEIGHT, GAME_FEEDBACK_HEIGHT,
    GAME_HOLD_BAR_HEIGHT, GAME_CURRENT_NOTE_HEIGHT,
    MATCH_TOLERANCE_CENTS, SCORE_PER_NOTE,
    HOLD_DURATION_DEFAULT,
)
from MyShittyNoteAnalyser.instrument_notation import (
    DEFAULT_CLEF,
    get_clef_for_instrument,
    get_written_range_for_instrument,
)
from MyShittyNoteAnalyser.note_utils import midi_to_note_text, cents_to_color
from MyShittyNoteAnalyser.hold_progress_bar import HoldProgressBar
from MyShittyNoteAnalyser.game_overlay import GameOverlay
from MyShittyNoteAnalyser.staff_canvas import StaffCanvas


# ------------------------------------------------------------------
# Main game panel
# ------------------------------------------------------------------

class GamePanel(QWidget):
    """Main game widget — orchestrates the note training game."""

    # ── signals ──────────────────────────────────────────────────
    back_to_tuner = pyqtSignal()
    play_again_requested = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("GamePanel")

        # ── state ────────────────────────────────────────────────
        self._game_active = False
        self._display_mode = "Letter (Solfege)"
        self._game_mode = "Random"
        self._scale_direction = "Ascending"
        self._game_length = "10 notes"
        self._hold_duration = HOLD_DURATION_DEFAULT
        self._use_sharps = False  # Flats by default (matches app default)
        self._notation = "Flats"
        self._clef = DEFAULT_CLEF
        self._instrument = "Concert (C)"
        self._min_midi = MIN_MIDI
        self._max_midi = MAX_MIDI

        self._target_midi = 60
        self._hold_timer = 0.0
        self._last_update_time = 0.0
        self._is_holding = False
        self._score = 0
        self._streak = 0
        self._best_streak = 0
        self._notes_attempted = 0
        self._notes_captured = 0
        self._total_notes = 0  # 0 = endless
        self._last_correct_midi: int | None = None
        self._current_midi: float | None = None
        self._current_cents: float | None = None

        # ── build UI ─────────────────────────────────────────────
        self._build_ui()

    # ── UI construction ───────────────────────────────────────────

    def _build_ui(self) -> None:
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(5, 5, 5, 5)
        main_layout.setSpacing(4)

        # 1. Top bar
        self._top_bar = QLabel("Score: 0   |   Streak: 0   |   0 / 0")
        self._top_bar.setFont(QFont("Helvetica", 12))
        self._top_bar.setFixedHeight(GAME_TOP_BAR_HEIGHT)
        self._top_bar.setStyleSheet(f"color: {GAME_STATS};")
        main_layout.addWidget(self._top_bar)

        # 2. Main display area (stacked: text label / staff canvas)
        self._display_stack = QWidget()
        ds_layout = QVBoxLayout(self._display_stack)
        ds_layout.setContentsMargins(0, 0, 0, 0)

        # Text mode label
        self._target_label = QLabel("Do (C4)")
        self._target_label.setFont(QFont("Helvetica", 48, QFont.Weight.Bold))
        self._target_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._target_label.setStyleSheet(f"color: {GAME_TARGET_TEXT}; "
                                          f"background-color: {GAME_BG};")
        ds_layout.addWidget(self._target_label)

        # Staff mode canvas
        self._staff_canvas = StaffCanvas(self._display_stack)
        ds_layout.addWidget(self._staff_canvas)

        self._update_display_mode_ui()
        main_layout.addWidget(self._display_stack, stretch=1)

        # 3. Hold progress bar
        self._hold_bar = HoldProgressBar(self)
        self._hold_bar.setFixedHeight(GAME_HOLD_BAR_HEIGHT + 24)
        main_layout.addWidget(self._hold_bar)

        # 4. Current detected note
        self._current_label = QLabel("Waiting for note...")
        self._current_label.setFont(QFont("Helvetica", 11))
        self._current_label.setFixedHeight(GAME_CURRENT_NOTE_HEIGHT)
        self._current_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._current_label.setStyleSheet(f"color: {GAME_STATS}; "
                                           f"background-color: {GAME_BG};")
        main_layout.addWidget(self._current_label)

        # 5. Feedback line
        self._feedback_label = QLabel("")
        self._feedback_label.setFont(QFont("Helvetica", 12, QFont.Weight.Bold))
        self._feedback_label.setFixedHeight(GAME_FEEDBACK_HEIGHT)
        self._feedback_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._feedback_label.setStyleSheet(
            f"color: {GAME_CORRECT}; background-color: {GAME_FEEDBACK_BG}; "
            f"border-radius: 4px;")
        main_layout.addWidget(self._feedback_label)

        # 6. Overlay (on top of everything)
        self._overlay = GameOverlay(self)
        self._overlay.play_again_callback = self._on_play_again
        self._overlay.back_callback = self._on_back_to_tuner

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if self._overlay is not None:
            self._overlay.setGeometry(self.rect())

    # ── display mode toggle ───────────────────────────────────────

    def _update_display_mode_ui(self) -> None:
        is_letter = self._display_mode == "Letter (Solfege)"
        self._target_label.setVisible(is_letter)
        self._staff_canvas.setVisible(not is_letter)

    # ── game lifecycle ────────────────────────────────────────────

    def start_game(self) -> None:
        self._game_active = True
        self._score = 0
        self._streak = 0
        self._best_streak = 0
        self._notes_attempted = 0
        self._notes_captured = 0
        self._hold_timer = 0.0
        self._last_update_time = time.perf_counter()
        self._is_holding = False
        self._last_correct_midi = None
        self._current_midi = None
        self._current_cents = None

        # Parse total notes from game length string
        length = self._game_length
        if length == "Endless":
            self._total_notes = 0
        else:
            try:
                self._total_notes = int(length.split()[0])
            except (ValueError, IndexError):
                self._total_notes = 10

        self._pick_next_target()
        self._update_top_bar()
        self._update_target_display()
        self._hold_bar.reset()
        self._current_label.setText("Waiting for note...")
        self._feedback_label.setText("")
        self._overlay.hide_overlay()

    def stop_game(self) -> None:
        self._game_active = False

    def is_active(self) -> bool:
        return self._game_active

    # ── note update (called from controller) ──────────────────────

    def update_game(self, midi_float: float | None,
                     cents: float | None) -> None:
        if not self._game_active:
            return
        if self._overlay.isVisible():
            return  # game paused on overlay

        now = time.perf_counter()
        dt = now - self._last_update_time
        self._last_update_time = now

        if midi_float is None:
            # Silence — reset hold
            self._hold_timer = 0.0
            self._is_holding = False
            self._hold_bar.set_fraction(0.0)
            self._current_midi = None
            self._current_cents = None
            self._current_label.setText("Silence...")
            return

        self._current_midi = midi_float
        self._current_cents = cents if cents is not None else 0.0

        # Update current note display
        midi_rounded = round(midi_float)
        solf, letter = midi_to_note_text(midi_rounded, self._use_sharps)
        c = self._current_cents
        col = cents_to_color(c)
        self._current_label.setText(
            f"<span style='color: {col};'>"
            f"Playing: {solf} ({letter})  {c:+.1f}¢</span>")

        # Check against target
        target = self._target_midi
        diff_cents = abs(midi_float - target) * 100.0

        if diff_cents <= MATCH_TOLERANCE_CENTS:
            # Holding correct note
            self._hold_timer += dt
            frac = min(1.0, self._hold_timer / self._hold_duration)
            self._hold_bar.set_fraction(frac)

            if not self._is_holding:
                self._is_holding = True
                self._feedback_label.setText(
                    f"<span style='color: {GAME_NOTEHEAD};'>Hold it...</span>")

            if self._hold_timer >= self._hold_duration:
                self._on_note_captured()
        else:
            # Wrong note — strict reset
            self._hold_timer = 0.0
            self._is_holding = False
            self._hold_bar.set_fraction(0.0)
            if midi_float is not None:
                wrong_midi = round(midi_float)
                if wrong_midi != target and diff_cents > MATCH_TOLERANCE_CENTS:
                    ws, wl = midi_to_note_text(wrong_midi, self._use_sharps)
                    self._feedback_label.setText(
                        f"<span style='color: {GAME_WRONG};'>"
                        f"Wrong note: {ws} ({wl})</span>")

    def _on_note_captured(self) -> None:
        self._score += SCORE_PER_NOTE
        self._streak += 1
        self._notes_captured += 1
        if self._streak > self._best_streak:
            self._best_streak = self._streak

        ts, tl = midi_to_note_text(self._target_midi, self._use_sharps)
        self._feedback_label.setText(
            f"<span style='color: {GAME_CORRECT};'>&#x2705; {ts} ({tl}) — Correct</span>")

        self._hold_timer = 0.0
        self._is_holding = False
        self._hold_bar.set_fraction(0.0)
        self._notes_attempted += 1
        self._last_correct_midi = self._target_midi

        # Check if round is over
        if self._total_notes > 0 and self._notes_captured >= self._total_notes:
            self._show_round_over()
            return

        self._pick_next_target()
        self._update_top_bar()
        self._update_target_display()

    def _pick_next_target(self) -> None:
        """Pick the next target note based on game mode and instrument range."""
        # Determine the available MIDI range for display
        # 1) User-custom range (if different from app defaults) takes priority
        if self._min_midi != MIN_MIDI or self._max_midi != MAX_MIDI:
            low = self._min_midi
            high = self._max_midi
        else:
            # 2) Use the instrument's written range
            low, high = get_written_range_for_instrument(self._instrument)

        available = list(range(low, high + 1))
        if not available:
            available = [60]

        if self._game_mode == "Random":
            self._target_midi = random.choice(available)
        else:
            # Scale mode
            direction = self._scale_direction
            if direction == "Random":
                direction = random.choice(["Ascending", "Descending"])

            if self._last_correct_midi is None:
                # Start from a reasonable position
                if direction == "Ascending":
                    self._last_correct_midi = low + 2
                else:
                    self._last_correct_midi = high - 2

            if direction == "Ascending":
                next_midi = self._last_correct_midi + 1
                if next_midi > high:
                    if self._total_notes == 0 or self._notes_captured < self._total_notes - 1:
                        # Wrap around
                        next_midi = low
                    else:
                        next_midi = high
            else:
                next_midi = self._last_correct_midi - 1
                if next_midi < low:
                    if self._total_notes == 0 or self._notes_captured < self._total_notes - 1:
                        next_midi = high
                    else:
                        next_midi = low

            self._target_midi = next_midi

    def _show_round_over(self) -> None:
        self._game_active = False
        self._overlay.show_summary(
            self._score, self._streak, self._best_streak,
            self._notes_captured, self._total_notes,
            is_endless=False)
        self._update_top_bar()

    def _on_play_again(self) -> None:
        self.play_again_requested.emit()
        self._overlay.hide_overlay()
        self.start_game()

    def _on_back_to_tuner(self) -> None:
        self._overlay.hide_overlay()
        self._game_active = False
        self.back_to_tuner.emit()

    # ── display updates ────────────────────────────────────────────

    def _update_top_bar(self) -> None:
        if self._total_notes > 0:
            progress = f"{self._notes_captured} / {self._total_notes}"
        else:
            progress = f"{self._notes_captured} ∞"
        self._top_bar.setText(
            f"Score: {self._score}  |  "
            f"Streak: {self._streak} (best: {self._best_streak})  |  "
            f"{progress}")

    def _update_target_display(self) -> None:
        solf, letter = midi_to_note_text(self._target_midi, self._use_sharps)
        self._target_label.setText(f"{solf} ({letter})")
        self._staff_canvas.set_target(self._target_midi)

    # ── setters for external configuration ─────────────────────────

    def set_display_mode(self, mode: str) -> None:
        self._display_mode = mode
        self._update_display_mode_ui()

    def set_game_mode(self, mode: str) -> None:
        self._game_mode = mode

    def set_scale_direction(self, direction: str) -> None:
        self._scale_direction = direction

    def set_game_length(self, length: str) -> None:
        self._game_length = length

    def set_hold_duration(self, duration: float) -> None:
        self._hold_duration = duration
        self._hold_bar.set_hold_duration(duration)

    def set_notation(self, notation: str) -> None:
        self._notation = notation
        self._use_sharps = (notation == "Sharps")
        if self._game_active:
            self._update_target_display()

    def set_instrument(self, instrument: str) -> None:
        self._instrument = instrument
        self._clef = get_clef_for_instrument(instrument)
        self._staff_canvas.set_clef(self._clef)

    def set_range(self, min_midi: int, max_midi: int) -> None:
        self._min_midi = min_midi
        self._max_midi = max_midi
        # If target is outside range, repick
        if self._target_midi < min_midi or self._target_midi > max_midi:
            self._pick_next_target()
            self._update_target_display()

    def set_clef(self, clef: str) -> None:
        self._clef = clef
        self._staff_canvas.set_clef(clef)
