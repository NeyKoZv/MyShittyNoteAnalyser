# MyShittyNoteAnalyser 🎵

Personal project — real-time pitch detector, tuner, and note-training game.  
Play a note into the mic and it shows you what it is, how accurate it is, and keeps a history.

Built with **PyQt6**, **aubio** (pitch detection), and **sounddevice** / **portaudio** (audio capture).  
Package management via **pixi**.

## Setup

```bash
# Install dependencies (creates the pixi environment automatically)
pixi install

# Run the app
pixi run python MyShittyNoteAnalyser\main.py

# Run tests
pixi run python -m pytest tests/
```

> Requires a working microphone.

## What it does

- Picks up audio from your mic and detects the pitch in real time
- Shows the note on a vertical tuner strip and in a scrolling pitch history
- Color-codes accuracy: **Perfect** / **Nice** / **Good** / **Bad**
- Handles transposition for Bb, Eb, F instruments (clarinet, sax, trumpet, horn, etc.)
- Choose sharps or flats notation
- Adjustable noise threshold, buffer size, and MIDI range
- **Note training game** — practice sight-reading with letter or staff notation display, random or scale-based note sequences, hold-to-capture scoring with streaks

## Structure

```
MyShittyNoteAnalyser/
├── main.py                     entry point (~20 lines)
├── gui.py                      main window, thin orchestrator (~200 lines)
├── audio_stream_manager.py     audio capture, processing thread, GUI coalescing
├── panel_coordinator.py        cross-panel settings propagation & UI updates
├── game_coordinator.py         game lifecycle, view switching, state sync
├── app_state.py                state machine (IDLE → RMS_ONLY → FULL_ANALYSIS → GAME_ACTIVE)
│
├── settings_panel.py           tuner settings (instrument, notation, MIDI range, audio)
├── tuner_panel.py              vertical tuner strip widget
├── history_panel.py            scrollable pitch history with scale labels
├── info_panel.py               bottom bar (note name, accuracy, cents meter, memory)
├── game_panel.py               game widget (target note, scoring, hold timer)
├── game_settings_panel.py      game settings (mode, display, length, hold duration)
├── audio_settings_widget.py    shared mic/threshold/buffer widget
│
├── staff_canvas.py             musical staff painting with clef & notehead
├── hold_progress_bar.py        hold-duration progress bar for the game
├── game_overlay.py             round-end summary overlay
│
├── pitch_detector.py           pitch detection (aubio + autocorrelation fallback)
├── note_utils.py               MIDI ↔ note name / staff position helpers
├── constants.py                colors, MIDI ranges, instrument offsets, layout
├── game_constants.py           game-mode constants (tolerances, staff layout, colors)
├── theme.py                    global Qt stylesheet
│
└── resources/
    ├── clef_treble.svg         treble (G) clef symbol
    ├── clef_bass.svg           bass (F) clef symbol
    ├── trebleClef_v2.svg       alternate treble clef
    └── bassClef_v2.svg         alternate bass clef

tests/
├── test_pitch_detector.py      unit tests for pitch/MIDI/note/staff functions
└── test_app_state.py           state machine transition validation tests
```

## License

GPL-3.0 license

## Vibes were coded 🎸