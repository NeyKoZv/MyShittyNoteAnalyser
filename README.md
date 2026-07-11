# MyShittyNoteAnalyser 🎵

Personal project — real-time pitch detector and tuner.  
Plays a note into the mic and it shows you what it is, how accurate it is, and keeps a history.

## Setup

```bash
conda env create -f env.yaml
conda activate MyShittyNoteAnalyser
python MyShittyNoteAnalyser\main.py
```

## What it does

- Picks up audio from your mic and detects the pitch
- Shows the note on a tuner strip and in a scrolling history
- Color-codes accuracy: Perfect / Nice / Good / Bad
- Handles transposition for Bb, Eb, F instruments (clarinet, sax, trumpet, horn)
- Choose sharps or flats notation

## Structure

```
MyShittyNoteAnalyser/
├── constants.py         colors, MIDI ranges, instrument offsets
├── gui.py               main controller
├── history_panel.py     scrollable note history
├── info_panel.py        bottom bar (note, accuracy, meter, memory)
├── main.py              entry point
├── pitch_detector.py    pitch detection (aubio + autocorrelation)
├── settings_panel.py    settings panel
└── tuner_panel.py       vertical tuner
```

## License

GPL-3.0 license 

## Vibes were coded