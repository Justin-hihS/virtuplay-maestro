"""Paths and default parameters shared across the app."""

from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
ASSETS_DIR = ROOT_DIR / "assets"
REFERENCE_DIR = ASSETS_DIR / "reference"
FEWSHOT_DIR = ASSETS_DIR / "fewshot"
OUTPUT_DIR = ROOT_DIR / "outputs"

LOGO_PATH = ASSETS_DIR / "logo.jpg"
GIF_PATH = ASSETS_DIR / "1126.gif"
DEFAULT_REFERENCE = REFERENCE_DIR / "3_t3.mid"

DEFAULT_BPM = 108
TICKS_PER_BEAT = 480
BEATS_PER_BAR = 4  # the scoring assumes 4/4 time

# Matching tolerances
TIME_TOLERANCE = 0.2  # seconds between student and reference onsets
VELOCITY_TOLERANCE = 20  # MIDI velocity units
PEDAL_START_TOLERANCE = 2  # seconds
PEDAL_DURATION_TOLERANCE = 0.2  # seconds

# 88-key piano range, A0 to C8
MIN_PITCH = 21
MAX_PITCH = 108

SUSTAIN_PEDAL_CC = 64

NOTE_COLORS = {
    "correct": (144, 238, 144),  # light green
    "incorrect": (255, 0, 0),  # red
    "too_hard": (255, 255, 0),  # yellow
    "too_light": (0, 255, 255),  # cyan
}

PITCH_CLASS_TO_SYLLABLE = {0: "Do", 2: "Re", 4: "Mi", 5: "Fa", 7: "So", 9: "La", 11: "Si"}
