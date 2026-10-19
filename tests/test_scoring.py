import pytest

from virtuplay import scoring

REF = [(60, 0.0, 0.5, 80), (62, 0.5, 1.0, 80), (60, 1.0, 2.0, 100)]


def test_match_picks_closest_onset_with_same_pitch():
    assert scoring.find_matching_reference(60, 0.95, REF, tolerance=0.2) == (60, 1.0, 2.0, 100)
    assert scoring.find_matching_reference(60, 0.05, REF, tolerance=0.2) == (60, 0.0, 0.5, 80)


def test_match_rejects_wrong_pitch_or_late_onset():
    assert scoring.find_matching_reference(61, 0.0, REF, tolerance=0.2) is None
    assert scoring.find_matching_reference(62, 0.8, REF, tolerance=0.2) is None


def test_note_score_penalties():
    s = scoring.note_score((60, 0.1, 0.4, 70), (60, 0.0, 0.5, 80))
    assert s["pitch"] == 100
    assert s["velocity"] == 80  # 10 units * 2
    assert s["timing"] == pytest.approx(80)  # 0.1 s * 200


def test_note_score_clamps_at_zero():
    s = scoring.note_score((60, 2.0, 2.5, 0), (60, 0.0, 0.5, 127))
    assert s["velocity"] == 0 and s["timing"] == 0


def test_duration_score_is_symmetric_ratio():
    assert scoring.duration_score((60, 0, 1.0, 80), (60, 0, 0.5, 80)) == pytest.approx(50)
    assert scoring.duration_score((60, 0, 0.5, 80), (60, 0, 1.0, 80)) == pytest.approx(50)
    assert scoring.duration_score((61, 0, 0.5, 80), (60, 0, 0.5, 80)) == 0
    assert scoring.duration_score((60, 0, 0, 80), (60, 0, 0.5, 80)) == 0


@pytest.mark.parametrize("start,expected", [(0.0, 0), (2.21, 0), (2.23, 1), (4.5, 2)])
def test_bar_index_at_108_bpm(start, expected):
    # one 4/4 bar at 108 BPM lasts 240 / 108 = 2.22 s
    assert scoring.bar_index(start, 108) == expected


@pytest.mark.parametrize("ref,played,expected", [
    (80, 90, "correct"), (80, 101, "too_hard"), (80, 59, "too_light"), (80, 100, "correct"),
])
def test_velocity_category(ref, played, expected):
    assert scoring.velocity_category(ref, played, tolerance=20) == expected


def test_pedal_events_and_matching():
    controls = [(64, 127, 0.0), (1, 50, 0.2), (64, 0, 1.0), (64, 100, 2.0), (64, 0, 2.5)]
    events = scoring.extract_pedal_events(controls)
    assert events == [(0.0, 1.0), (2.0, 2.5)]
    assert scoring.match_pedal(0.5, 1.6, events, start_tolerance=2, duration_tolerance=0.2) == (0.0, 1.0)
    assert scoring.match_pedal(0.0, 2.0, events, start_tolerance=2, duration_tolerance=0.2) is None


def test_summarize_averages_pitch_over_all_played_notes():
    overall = {"pitch": 200, "velocity": 180, "timing": 160, "count": 2, "note_count": 4}
    s = scoring.summarize(overall, total_duration_score=150)
    assert s["pitch"] == 50
    assert s["velocity"] == 90 and s["timing"] == 80 and s["duration"] == 75
    assert s["overall"] == pytest.approx((50 + 90 + 80 + 75) / 4)


def test_summarize_handles_empty_performance():
    s = scoring.summarize({"pitch": 0, "velocity": 0, "timing": 0, "count": 0, "note_count": 0}, 0)
    assert s["overall"] == 0
