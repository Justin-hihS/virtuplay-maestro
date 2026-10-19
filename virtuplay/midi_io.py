"""Reading reference MIDI files and writing recorded performances."""

import mido
import pretty_midi

from .scoring import extract_pedal_events


def load_reference(path, bpm):
    """Load a reference MIDI file rescaled to ``bpm``.

    Returns ``(notes, control_changes, pedal_events)`` where notes are
    ``(pitch, start, end, velocity)``, control changes are
    ``(number, value, time)``, and all times are shifted so the first note
    starts at 0.
    """
    midi = pretty_midi.PrettyMIDI(str(path))
    _, tempos = midi.get_tempo_changes()
    tempo_ratio = tempos[0] / bpm  # assumes a single, constant tempo

    notes = [(n.pitch, n.start * tempo_ratio, n.end * tempo_ratio, n.velocity)
             for inst in midi.instruments for n in inst.notes]
    controls = [(c.number, c.value, c.time * tempo_ratio)
                for inst in midi.instruments for c in inst.control_changes]

    offset = min(start for _, start, _, _ in notes)
    notes = [(p, s - offset, e - offset, v) for p, s, e, v in notes]
    controls = [(num, val, t - offset) for num, val, t in controls]
    return notes, controls, extract_pedal_events(controls)


def events_to_midi(events, bpm):
    """Build a single-track MIDI file from recorded events.

    Each event is a dict with ``type`` ('note_on', 'note_off',
    'control_change' or 'other'), ``note``, ``velocity`` and ``timestamp``
    in seconds since recording started.
    """
    midi_file = mido.MidiFile()
    track = mido.MidiTrack()
    midi_file.tracks.append(track)
    track.append(mido.MetaMessage("set_tempo", tempo=mido.bpm2tempo(bpm), time=0))

    last_time = 0
    for event in sorted(events, key=lambda e: e["timestamp"]):
        ticks = int((event["timestamp"] - last_time) * midi_file.ticks_per_beat * (bpm / 60))
        if event["type"] == "note_on":
            track.append(mido.Message("note_on", note=event["note"], velocity=event["velocity"], time=ticks))
        elif event["type"] == "note_off":
            track.append(mido.Message("note_off", note=event["note"], velocity=0, time=ticks))
        elif event["type"] == "control_change":
            track.append(mido.Message("control_change", control=event["note"], value=event["velocity"], time=ticks))
        last_time = event["timestamp"]
    return midi_file
