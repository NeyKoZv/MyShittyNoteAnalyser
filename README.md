# MyShittyNoteAnalyser 🎵

Real-time pitch detector and tuner.  
Play a note into the mic — it shows you what note you're playing, how accurate it is, and keeps a scrolling history.

Built with **PyQt6**, **aubio** (optional, faster pitch detection), **sounddevice** / **portaudio** (audio capture), and **numpy** (autocorrelation fallback).  
Package management via **pixi** (conda + pip).

## Setup

```bash
# Pixi (recommended) — creates the environment automatically
pixi install

# Or with plain pip / venv
pip install -e .

# Run the app
pixi run python MyShittyNoteAnalyser\main.py   # from a pixi environment
python MyShittyNoteAnalyser\main.py            # from an activated venv

# Run tests
pixi run pytest tests/
```

> Requires a working microphone. On first launch the OS microphone permission prompt will appear.

## What it does

- Picks up audio from your mic and detects the pitch in real time
- Shows the live note on a vertical scale with a scrolling pitch history
- Color-codes accuracy: **Perfect** (±5¢) / **Nice** (±20¢) / **Good** (±50¢) / **Bad** (≥50¢)
- Handles transposition for transposing instruments (Bb clarinet, Eb clarinet, A clarinet, Bb trumpet, alto/tenor sax, French horn, etc.)
- Choose sharps or flats notation — auto-suggested per instrument, overridable at any time
- Optional quantize-to-semitone snapping for the history display
- Adjustable noise threshold, buffer size, MIDI range, sample rate, and microphone selection
- Live RMS level meter with a visual noise-threshold marker
- Built-in **metronome** with a live beat indicator:
  - BPM control (type a value, or click-and-drag to scrub — drag up/right speeds up, down/left slows down)
  - Selectable time signature (4/4, 3/4, 2/4, 5/4, 6/8, 7/8) that controls how many beats are shown
  - Visual representation of the current beat inside the measure (accented downbeat on beat 1)
  - Click sounds are synthesized on the fly (no audio files needed); a 🔊 toggle can mute the sound while keeping the visual
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
    (any state) ──stop_stream()──▶ IDLE
```

| From | To |
|---|---|
| `IDLE` | `RMS_ONLY` |
| `RMS_ONLY` | `FULL_ANALYSIS`, `IDLE` |
| `FULL_ANALYSIS` | `RMS_ONLY`, `IDLE` |

## Structure

```
MyShittyNoteAnalyser/
├── main.py                     entry point
├── __init__.py                 package metadata (version 0.1.0)
├── gui.py                      main window, thin orchestrator
├── audio_stream_manager.py     audio capture, processing thread, GUI coalescing
├── panel_coordinator.py        cross-panel settings propagation & UI updates
├── app_state.py                state machine (IDLE → RMS_ONLY → FULL_ANALYSIS)
│
├── settings_panel.py           tuner settings (instrument, notation, MIDI range, audio)
├── audio_settings_widget.py    shared mic / noise threshold + RMS / buffer widget
├── range_slider.py             dual-handle MIDI range slider
├── metronome_widget.py         self-contained metronome + live beat indicator
├── history_panel.py            scrollable pitch history with scale labels & live note
│
├── instrument_notation.py      instrument → default notation (sharps/flats) mapping
├── pitch_detector.py           pitch detection (aubio + autocorrelation fallback)
├── note_utils.py               MIDI ↔ note name / staff position / accuracy helpers
├── constants.py                colors, MIDI ranges, instrument offsets, layout constants
└── theme.py                    global Qt stylesheet

tests/
├── test_pitch_detector.py      unit tests for frequency→MIDI, MIDI→note, staff-Y, ledger lines
└── test_app_state.py           state machine transition validation
```

## Dependencies

| Package | Type | Notes |
|---|---|---|
| `numpy` | ✅ runtime | Core array math |
| `PyQt6` | ✅ runtime | GUI framework |
| `sounddevice` | ✅ runtime | PortAudio binding (audio capture) |
| `partitura`, `musescore`, `beautifulsoup4`, `lilypond` | ✅ runtime | Declared in `pyproject.toml` |
| `aubio` | ❌ optional | Faster pitch detection; autocorrelation fallback if absent |
| `pytest` | ❌ dev | Testing |
| `portaudio`, `selenium`, `cairosvg`, `tqdm`, `requests` | ❌ pixi | Installed by the pixi environment |

## License

GPL-3.0 license — see [LICENSE](LICENSE).

---

*Vibes were coded 🎸*