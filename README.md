# MyShittyNoteAnalyser 🎵

Personal project — real-time pitch detector and tuner.  
Plays a note into the mic and it shows you what it is, how accurate it is, and keeps a history.

Built with **PyQt6**, **aubio** (pitch detection), and **sounddevice** / **portaudio** (audio capture).  
Package management via **pixi**.

## Setup

```bash
# Install dependencies (creates the pixi environment automatically)
pixi install

# Run the app
pixi run python MyShittyNoteAnalyser\main.py
```

> Requires a working microphone.

## What it does

- Picks up audio from your mic and detects the pitch in real time
- Shows the note on a vertical tuner strip and in a scrolling history
- Color-codes accuracy: **Perfect** / **Nice** / **Good** / **Bad**
- Handles transposition for Bb, Eb, F instruments (clarinet, sax, trumpet, horn)
- Choose sharps or flats notation
- Adjustable volume threshold and memory buffer

## Structure

```
MyShittyNoteAnalyser/
├── constants.py         colors, MIDI ranges, instrument offsets
├── gui.py               main controller / window layout
├── history_panel.py     scrollable note history widget
├── info_panel.py        bottom bar (note name, accuracy, meter, memory)
├── main.py              entry point
├── pitch_detector.py    pitch detection (aubio + autocorrelation fallback)
├── settings_panel.py    instrument, notation, threshold settings
└── tuner_panel.py       vertical tuner strip widget
```

## License

GPL-3.0 license

## Vibes were coded 🎸