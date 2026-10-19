import argparse

from .config import DEFAULT_BPM, DEFAULT_REFERENCE


def main():
    parser = argparse.ArgumentParser(description="VirtuPlay Maestro piano practice app")
    parser.add_argument("--reference", default=str(DEFAULT_REFERENCE), help="reference MIDI performance")
    parser.add_argument("--bpm", type=int, default=DEFAULT_BPM, help="practice tempo")
    args = parser.parse_args()

    from .app import DynamicMusicSheet

    DynamicMusicSheet(reference_path=args.reference, bpm=args.bpm).run()


if __name__ == "__main__":
    main()
