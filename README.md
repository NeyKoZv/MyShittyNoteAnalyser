# MyShittyNoteAnalyser 🎵

Personal project — real-time pitch detector, tuner, and note-training game.  
Play a note into the mic and it shows you what it is, how accurate it is, and keeps a history.

Built with **PyQt6**, **aubio** (pitch detection), and **sounddevice** / **portaudio** (audio capture).  
Package management via **pixi** (conda + pip).

## Setup

```bash
# Install dependencies (creates the pixi environment automatically)
pixi install

# Run the app (either works)
pixi run python MyShittyNoteAnalyser\main.py

# Run tests
pixi run pytest tests/ 

# Run directly with pip (aubio optional)
pip install -e .
pip install aubio   # optional, enables aubio-based pitch detection
```

> Requires a working microphone. On first launch the OS microphone permission prompt will appear.

## What it does

- Picks up audio from your mic and detects the pitch in real time
- Shows the note on a vertical tuner strip and in a scrolling pitch history
- Color-codes accuracy: **Perfect** (±5¢) / **Nice** (±15¢) / **Good** (±25¢) / **Bad** (>25¢)
- Handles transposition for Bb, Eb, F instruments (clarinet, sax, trumpet, horn, etc.) with correct clef (treble/bass) and written-range mapping
- Choose sharps or flats notation; select instrument clef (treble, bass, or auto)
- Adjustable noise threshold, buffer size, MIDI range, and sample rate
- **Note training game** — practice sight-reading with letter or staff notation display, random or scale-based note sequences, hold-to-capture scoring with streaks
  - Game modes: **Random** (any note in range) or **Scale** (stepwise diatonic, configurable direction)
  - Display modes: **Letter (Solfege)** or **Staff Notation** with treble/bass clef
  - Configurable round length (5–50 or **Endless**) and hold duration (0.5–3.0s)
  - Round-end overlay shows score, best streak, accuracy, and notes played
- **Endless mode** — play indefinitely until you stop
- **Continue on silence** — optionally log silences (`---`) to the history instead of skipping them
- Pitch detection uses **aubio** when available, with an **autocorrelation + parabolic interpolation** fallback
- Aubio `pitch` objects are cached by `(block_size, sample_rate)` for efficiency
- Audio processing runs in a background thread with GUI coalescing for smooth UI updates
- Thread-safe note history (up to 100 000 entries) with live scrolling display

## State Machine

```
                    start_stream()
    IDLE ───────────────────────────▶ RMS_ONLY
                                         │
                          enable_full_analysis()
    RMS_ONLY ───────────────────────────▶ FULL_ANALYSIS
         ◀─────────────────────────────── disable_full_analysis()
                                              │
                                  start_game()
    FULL_ANALYSIS ───────────────────────────▶ GAME_ACTIVE
         ◀──────────────────────────────────── stop_game()
                                              │
    (any state) ──stop_stream()──▶ IDLE
```

| From | To |
|---|---|
| `IDLE` | `RMS_ONLY` |
| `RMS_ONLY` | `FULL_ANALYSIS`, `IDLE` |
| `FULL_ANALYSIS` | `RMS_ONLY`, `GAME_ACTIVE`, `IDLE` |
| `GAME_ACTIVE` | `FULL_ANALYSIS`, `IDLE` |

## Structure

```
MyShittyNoteAnalyser/
├── main.py                     entry point (~10 lines)
├── __init__.py                 package metadata (version 0.1.0)
├── gui.py                      main window, thin orchestrator
├── audio_stream_manager.py     audio capture, processing thread, GUI coalescing
├── panel_coordinator.py        cross-panel settings propagation & UI updates
├── game_coordinator.py         game lifecycle, view switching, state sync
├── app_state.py                state machine (IDLE → RMS_ONLY → FULL_ANALYSIS → GAME_ACTIVE)
│
├── settings_panel.py           tuner settings (instrument, notation, clef, MIDI range, audio)
├── tuner_panel.py              vertical tuner strip widget
├── history_panel.py            scrollable pitch history with scale labels
├── info_panel.py               bottom bar (note name, accuracy, cents meter, memory usage)
├── game_panel.py               game widget (target note, scoring, hold timer)
├── game_settings_panel.py      game settings (mode, display, clef, length, hold duration, audio)
├── audio_settings_widget.py    shared mic/threshold/buffer widget
│
├── staff_canvas.py             musical staff painting with clef (treble/bass) & notehead
├── hold_progress_bar.py        hold-duration progress bar for the game
├── game_overlay.py             round-end summary overlay (score, streak, accuracy, play again)
│
├── instrument_notation.py      instrument → clef / written range / default notation mapping
├── pitch_detector.py           pitch detection (aubio + autocorrelation fallback)
├── note_utils.py               MIDI ↔ note name / staff position helpers
├── constants.py                colors, MIDI ranges, instrument offsets, layout constants
├── game_constants.py           game-mode constants (tolerances, staff layout, colors)
├── theme.py                    global Qt stylesheet
│
└── resources/
    ├── trebleClef_v2.svg       treble (G) clef symbol
    └── bassClef_v2.svg         bass (F) clef symbol

tests/
├── test_pitch_detector.py      unit tests for frequency→MIDI, MIDI→note, staff-Y, ledger lines
└── test_app_state.py           state machine transition validation (15 tests)
```

## Dependencies

| Package | Required? | Notes |
|---|---|---|
| `numpy` | ✅ | Core array math |
| `PyQt6` | ✅ | GUI framework |
| `sounddevice` | ✅ | PortAudio binding (audio capture) |
| `aubio` | ❌ optional | Faster pitch detection; autocorrelation fallback if absent |
| `pytest` | ❌ dev | Testing |

## License

GPL-3.0 license — see [LICENSE](LICENSE).

---

*Vibes were coded 🎸*