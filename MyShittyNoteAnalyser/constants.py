# Note names (sharps and flats)
NOTE_SHARP_LETTER = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
NOTE_SHARP_SOLFEGE = ['Do', 'Do#', 'Ré', 'Ré#', 'Mi', 'Fa', 'Fa#', 'Sol', 'Sol#', 'La', 'La#', 'Si']

NOTE_FLAT_LETTER = ['C', 'Db', 'D', 'Eb', 'E', 'F', 'Gb', 'G', 'Ab', 'A', 'Bb', 'B']
NOTE_FLAT_SOLFEGE = ['Do', 'Réb', 'Ré', 'Mib', 'Mi', 'Fa', 'Solb', 'Sol', 'Lab', 'La', 'Sib', 'Si']

# Notation choices
NOTATION_OPTIONS = ["Sharps", "Flats"]
DEFAULT_NOTATION = "Flats"
DEFAULT_INSTRUMENT = "Concert (C)"

# Instrument transpositions
INSTRUMENTS = {
    "Concert (C)": 0,
    "Bb Clarinet": 2,
    "A Clarinet": 3,
    "Eb Clarinet": -3,
    "Bb Trumpet": 2,
    "Alto Sax (Eb)": 9,
    "Tenor Sax (Bb)": 14,
    "French Horn (F)": 7,
    "Guitar": 0,
    "Bass Guitar": 0,
}

# Fixed MIDI range (C2–B5)
MIN_MIDI = 48
MAX_MIDI = 74

# History
NOTE_HISTORY_MAXLEN = 100000

# Audio defaults
DEFAULT_SAMPLE_RATE = 44100
DEFAULT_BLOCK_SIZE = 2048
BUFFER_OPTIONS = [128, 256, 512, 1024, 2048, 4096]

# Threshold
NOISE_THRESHOLD_DEFAULT = 0.02
NOISE_THRESHOLD_MIN = 0.0
NOISE_THRESHOLD_MAX = 0.05

# Layout
APP_GEOMETRY = "950x700"
TUNER_WIDTH = 80
TUNER_HEIGHT = 200
TUNER_MARGIN = 15
TUNER_DOT_RADIUS = 6
HISTORY_NOTE_GAP = 10
HISTORY_SCALE_WIDTH = 90
METER_WIDTH = 150
METER_HEIGHT = 15

# Color palette — shared across all panels
# Backgrounds
COLOR_BG_DARK = '#2b2b2b'
COLOR_BG_DARKER = '#1e1e1e'
COLOR_BG_INPUT = '#3c3c3c'
COLOR_BG_CANVAS = '#1e1e1e'
COLOR_BG_METER = '#333333'

# Foregrounds
COLOR_FG_PRIMARY = 'white'
COLOR_FG_SECONDARY = '#aaaaaa'
COLOR_FG_LABEL = '#cccccc'
COLOR_FG_ACTIVE = 'white'
COLOR_FG_SELECTED = 'white'

# Grid and scale
COLOR_GRID_LINE = '#333333'
COLOR_GRID_LABEL = '#cccccc'
COLOR_TUNER_TICK = '#666666'
COLOR_TUNER_LABEL = '#aaaaaa'
COLOR_METER_TICK = 'gray'
COLOR_METER_CENTER = 'white'

# Accuracy accent colors
COLOR_ACCENT_PERFECT = '#00ff88'
COLOR_ACCENT_NICE = '#44aaff'
COLOR_ACCENT_GOOD = '#ffaa00'
COLOR_ACCENT_BAD = '#ff5555'

# Misc
COLOR_ERROR = 'red'
COLOR_BUTTON_ACTIVE = '#4a4a4a'