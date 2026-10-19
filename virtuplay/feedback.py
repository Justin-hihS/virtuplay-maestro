"""Few-shot LLM feedback comparing a student performance to the reference.

The API key is read from the OPENAI_API_KEY environment variable. Without
it, the app still runs and the report omits the AI comment.
"""

import os

import mido

from .config import FEWSHOT_DIR

DEFAULT_MODEL = "gpt-4o-mini"

# (student file, expected feedback) pairs played against fewshot/2_t2.mid
FEWSHOT_EXAMPLES = [
    ("2_s1.mid",
     "The first half of the reference piece features crescendos and decrescendos, conveying strong "
     "emotion. However, the student maintained a constant velocity throughout. The tempo and pedals "
     "are accurate, but the student's note durations are slightly shorter."),
    ("2_s2.mid",
     "The student's articulation is highly inaccurate; each note should be played legato rather than "
     "staccato. Although the velocity, tempo, and pedal usage are accurate, the articulation "
     "undermines the emotional expression."),
    ("2_s3.mid",
     "The student played too hastily, resulting in poor tempo control. However, the notes, pedal "
     "usage, and velocity are accurate. The student should focus on practicing steady tempo control "
     "first."),
]


def midi_to_text(midi):
    """Serialize the first track of a MIDI file (path or mido.MidiFile) as text."""
    if not isinstance(midi, mido.MidiFile):
        midi = mido.MidiFile(str(midi))
    return str(midi.tracks[0])


def build_system_prompt():
    parts = [
        "You are a piano tutor. You'll receive two MIDI files, one as a reference performance and the "
        "other as the student's performance. Compare how the student played against the reference in "
        "at most three sentences.",
        f"Here are three examples.\nReference: {midi_to_text(FEWSHOT_DIR / '2_t2.mid')}",
    ]
    for i, (student_file, answer) in enumerate(FEWSHOT_EXAMPLES, 1):
        parts.append(f"Student{i}: {midi_to_text(FEWSHOT_DIR / student_file)}\n"
                     f"For Reference and Student{i}, you should output: \"{answer}\"")
    return "\n\n".join(parts)


def generate_comment(reference, student, model=DEFAULT_MODEL):
    """Return the tutor's comment, or None if no API key is configured."""
    if not os.environ.get("OPENAI_API_KEY"):
        print("OPENAI_API_KEY not set; skipping AI comment.")
        return None
    from openai import OpenAI

    client = OpenAI()
    response = client.chat.completions.create(
        model=model,
        temperature=0.7,
        messages=[
            {"role": "system", "content": build_system_prompt()},
            {"role": "user", "content": f"Reference:{midi_to_text(reference)}\n Student:{midi_to_text(student)}"},
        ],
    )
    return response.choices[0].message.content
