import mido
import pretty_midi
import pytest

from virtuplay.config import REFERENCE_DIR
from virtuplay.midi_io import events_to_midi, load_reference


def test_reference_is_rescaled_and_starts_at_zero():
    path = REFERENCE_DIR / "3_t3.mid"
    notes, _, pedals = load_reference(path, bpm=108)
    assert min(start for _, start, _, _ in notes) == pytest.approx(0)
    assert all(end > start for _, start, end, _ in notes)
    assert all(release >= press for press, release in pedals)

    # halving the tempo doubles every time
    slow, _, _ = load_reference(path, bpm=54)
    assert max(n[2] for n in slow) == pytest.approx(2 * max(n[2] for n in notes))


def test_recorded_events_round_trip(tmp_path):
    events = [
        {"type": "note_on", "note": 60, "velocity": 90, "timestamp": 0.0},
        {"type": "control_change", "note": 64, "velocity": 127, "timestamp": 0.1},
        {"type": "note_off", "note": 60, "velocity": 0, "timestamp": 0.5},
        {"type": "note_on", "note": 64, "velocity": 70, "timestamp": 1.0},
        {"type": "note_off", "note": 64, "velocity": 0, "timestamp": 1.5},
    ]
    midi = events_to_midi(events, bpm=120)
    out = tmp_path / "take.mid"
    midi.save(out)

    notes = pretty_midi.PrettyMIDI(str(out)).instruments[0].notes
    assert [(n.pitch, n.velocity) for n in notes] == [(60, 90), (64, 70)]
    assert notes[0].start == pytest.approx(0.0, abs=0.01)
    assert notes[0].end == pytest.approx(0.5, abs=0.01)
    assert notes[1].start == pytest.approx(1.0, abs=0.01)
    assert any(m.type == "control_change" for m in mido.MidiFile(out).tracks[0])
