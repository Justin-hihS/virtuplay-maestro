"""Live and post-performance evaluation built on the pure functions in scoring.py."""

import time

from . import scoring
from .emotion.trajectory import draw_ar_vl_path, mido_to_pretty_midi, split_midi_by_bars
from .feedback import generate_comment
from .midi_io import load_reference


class EvaluationMixin:
    def load_reference_midi(self, reference_path):
        try:
            notes, controls, self.ref_pedal_events = load_reference(reference_path, self.BPM)
            return notes, controls
        except Exception as e:
            print(f"Error loading reference MIDI: {e}")
            self.ref_pedal_events = []
            return [], []

    def get_ref_midi_end_time(self):
        try:
            return max(end for _, _, end, _ in self.ref_notes)
        except Exception as e:
            print(f"Error loading reference MIDI: {e}")
            return -1

    def calculate_duration_score(self, student_note, ref_note):
        if student_note[0] == ref_note[0]:
            # calculate_overall_duartion pairs these with matched notes in order
            self.ref_duration_list.append(ref_note[2] - ref_note[1])
        return scoring.duration_score(student_note, ref_note)

    def update_scores(self, note_score, bar_number):
        for aspect in ("pitch", "velocity", "timing"):
            self.bar_scores[bar_number][aspect] += note_score[aspect]
            self.bar_scores[bar_number]["count"] += 1
            self.overall_score[aspect] += note_score[aspect]
        self.overall_score["count"] += 1

    def update_duration_scores(self, duration_score, bar_number):
        self.bar_scores[bar_number].setdefault("duration", 0)
        self.overall_score.setdefault("duration", 0)
        self.bar_scores[bar_number]["duration"] += duration_score
        self.overall_score["duration"] += duration_score

    def compare_and_visualize(self, student_note, tolerance=0.1, velocity_tolerance=20):
        """Match a newly played note, update combo and scores, and queue it for drawing."""
        pitch, start_time, end_time, velocity = student_note
        ref = scoring.find_matching_reference(pitch, start_time, self.ref_notes, tolerance)

        if ref:
            color = self.colors["correct"]
            self.current_combo += 1
            self.max_combo = max(self.max_combo, self.current_combo)
            self.combo_last_increase_time = time.time()
            self.note_list.append((pitch, start_time, end_time, True, color, velocity))

            bar_number = scoring.bar_index(start_time, self.BPM)
            self.update_scores(scoring.note_score(student_note, ref), bar_number)
            self.update_duration_scores(self.calculate_duration_score(student_note, ref), bar_number)
        else:
            color = self.colors["incorrect"]
            self.note_list.append((pitch, start_time, end_time, False, color, velocity))
            self.current_combo = 0
            self.combo_last_increase_time = None

        self.overall_score["note_count"] += 1
        return color

    def compare_pedal_and_visulaize(self, student_control, tolerance=0.1):
        start, end = student_control
        match = scoring.match_pedal(start, end, self.ref_pedal_events,
                                    self.pedal_start_tolerance, self.pedal_duration_tolerance)
        color = self.colors["correct"] if match else self.colors["incorrect"]
        self.pedal_list.append((start, end, match is not None, color))

    def report_compare_with_tolerance(self, tolerance=0.1, velocity_tolerance=20):
        """Recolor every played note for the report using the given tolerances."""
        recolored = []
        for pitch, start, end, _, _, velocity in self.note_list:
            ref = scoring.find_matching_reference(pitch, start, self.ref_notes, tolerance)
            if ref:
                category = scoring.velocity_category(ref[3], velocity, velocity_tolerance)
                recolored.append((pitch, start, end, True, self.colors[category], velocity))
            else:
                recolored.append((pitch, start, end, False, self.colors["incorrect"], velocity))
        self.note_list = recolored

    def calculate_overall_duartion(self):
        correct_notes = [n for n in self.note_list if n[3]]
        total = 0
        for (_, start, end, _, _, _), ref_duration in zip(correct_notes, self.ref_duration_list):
            student_duration = end - start
            if student_duration <= 0 or ref_duration <= 0:
                return 0
            total += min(student_duration / ref_duration, ref_duration / student_duration) * 100
        return total

    def get_duration_statistics(self):
        if not self.note_list:
            return None
        total, analyzed = 0, 0
        for note in self.note_list:
            ref = next((r for r in self.ref_notes
                        if abs(note[1] - r[1]) < self.time_tolerance and note[0] == r[0]), None)
            if ref:
                score = self.calculate_duration_score((note[0], note[1], note[2], note[5]), ref)
                if score > 0:
                    total += score
                    analyzed += 1
        return {
            "average_duration_score": total / analyzed if analyzed > 0 else 0,
            "total_notes_analyzed": analyzed,
            "total_notes_played": len(self.note_list),
        }

    def generate_performance_report(self):
        s = scoring.summarize(self.overall_score, self.calculate_overall_duartion())
        report = "Performance Metrics\n\n"
        report += f"Note Accuracy: {s['pitch']:.2f}%\n\n"
        report += f"Detail Scores (Sentiment Analysis): {s['detail']:.2f} / 100\n"
        report += f"  - Velocity Control: {s['velocity']:.2f} / 100\n"
        report += f"  - Timing Precision: {s['timing']:.2f} / 100\n"
        report += f"  - Duration Accuracy: {s['duration']:.2f} / 100\n\n"
        stats = self.get_duration_statistics()
        if stats:
            report += (f"Notes Analyzed (Velocity, Timing, Duration): "
                       f"{stats['total_notes_analyzed']}/{stats['total_notes_played']}\n\n")
        report += scoring.feedback_message(s["overall"])
        self.performance_report = report
        print("Performance Report Generated:")
        print(report)

    def generate_overall_comment(self):
        try:
            comment = generate_comment(self.reference_path, self.student_midi_file)
        except Exception as e:
            print(f"AI comment failed: {e}")
            comment = None
        self.overall_comment = comment or ""
        if comment:
            words = comment.split()
            formatted = "\n".join(" ".join(words[i:i + 10]) for i in range(0, len(words), 10))
            self.performance_report += f"\n\n\nAI Comments\n\n{formatted}"
            print(formatted)
        self.performance_report += "\n\n\nColor Representation"

    def generate_ar_vl_path(self):
        return draw_ar_vl_path(split_midi_by_bars(str(self.reference_path)),
                               split_midi_by_bars(mido_to_pretty_midi(self.student_midi_file)))
