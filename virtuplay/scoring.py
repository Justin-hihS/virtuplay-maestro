"""Pure scoring functions that compare a student performance to a reference.

Notes are tuples ``(pitch, start, end, velocity)`` with times in seconds.
Nothing here depends on pygame, so it can be unit-tested directly.
"""

from .config import BEATS_PER_BAR


def find_matching_reference(pitch, start, ref_notes, tolerance):
    """Return the reference note with the same pitch whose onset is closest
    to ``start`` and within ``tolerance`` seconds, or None."""
    best, best_diff = None, float("inf")
    for ref in ref_notes:
        if ref[0] != pitch:
            continue
        diff = abs(start - ref[1])
        if diff < best_diff and diff <= tolerance:
            best, best_diff = ref, diff
    return best


def note_score(student_note, ref_note):
    """Score pitch, velocity and timing of one matched note, each in [0, 100]."""
    pitch_diff = abs(student_note[0] - ref_note[0])
    velocity_diff = abs(student_note[3] - ref_note[3])
    timing_diff = abs(student_note[1] - ref_note[1])
    return {
        "pitch": max(0, 100 - pitch_diff * 2),
        "velocity": max(0, 100 - velocity_diff * 2),  # -2 per velocity unit
        "timing": max(0, 100 - timing_diff * 200),  # -20 per 0.1 s
    }


def duration_score(student_note, ref_note):
    """Ratio of the shorter to the longer duration, scaled to [0, 100].

    Returns 0 when pitches differ or either duration is not positive.
    """
    if student_note[0] != ref_note[0]:
        return 0
    student_duration = student_note[2] - student_note[1]
    ref_duration = ref_note[2] - ref_note[1]
    if student_duration <= 0 or ref_duration <= 0:
        return 0
    return min(student_duration / ref_duration, ref_duration / student_duration) * 100


def bar_index(start, bpm, beats_per_bar=BEATS_PER_BAR):
    """Zero-based bar number of an onset at ``start`` seconds."""
    bar_duration = beats_per_bar * 60 / bpm
    return int(start // bar_duration)


def velocity_category(ref_velocity, velocity, tolerance):
    """Classify dynamics as 'correct', 'too_hard' or 'too_light'."""
    diff = ref_velocity - velocity
    if abs(diff) <= tolerance:
        return "correct"
    if diff < -tolerance:
        return "too_hard"
    return "too_light"


def match_pedal(start, end, ref_pedal_events, start_tolerance, duration_tolerance):
    """Return the first reference pedal press (start, end) that matches both the
    press time and the hold duration within tolerance, or None."""
    duration = end - start
    for ref_start, ref_end in ref_pedal_events:
        if (abs(start - ref_start) <= start_tolerance
                and abs(duration - (ref_end - ref_start)) <= duration_tolerance):
            return ref_start, ref_end
    return None


def extract_pedal_events(control_changes, pedal_cc=64):
    """Turn (number, value, time) control changes into (press, release) pairs."""
    events, pressed_at = [], None
    for number, value, time_ in control_changes:
        if number != pedal_cc:
            continue
        if value > 0:
            pressed_at = time_
        elif value == 0 and pressed_at is not None:
            events.append((pressed_at, time_))
            pressed_at = None
    return events


def summarize(overall_score, total_duration_score):
    """Average the accumulated per-note scores.

    ``overall_score`` holds running sums of pitch/velocity/timing, ``count``
    (matched notes) and ``note_count`` (all played notes). Pitch accuracy is
    averaged over every played note, so wrong notes lower it.
    """
    matched = overall_score["count"]
    played = overall_score["note_count"]
    pitch = overall_score["pitch"] / played if played > 0 else 0
    velocity = overall_score["velocity"] / matched if matched > 0 else 0
    timing = overall_score["timing"] / matched if matched > 0 else 0
    duration = total_duration_score / matched if matched > 0 else 0
    return {
        "pitch": pitch,
        "velocity": velocity,
        "timing": timing,
        "duration": duration,
        "overall": (pitch + velocity + timing + duration) / 4,
        "detail": (velocity + timing + duration) / 3,
    }


def feedback_message(overall_avg):
    if overall_avg >= 90:
        return "Excellent performance! Your playing was highly accurate with consistent note durations."
    if overall_avg >= 80:
        return "Great job! Your performance was very good with minor areas for improvement."
    if overall_avg >= 70:
        return "Good effort! Focus on maintaining consistent note lengths to match the reference."
    return "Keep practicing! Pay attention to timing and note durations to improve further."
