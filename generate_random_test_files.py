"""Generate random long-format test CSV files for the dashboard."""
import argparse
import csv
import random
from datetime import datetime
from pathlib import Path

DATA_DIR = Path('data') / 'responses'

LEFT_RIGHT_QUESTIONS = ['trust_rating', 'emotion_rating']
FULL_FACE_NUMERIC = ['trust_rating', 'emotion_rating', 'masculinity_full', 'femininity_full']
CHOICE_QUESTIONS = ['masc_choice', 'fem_choice']
CHOICE_OPTIONS = ['left', 'right', 'neither']


def generate_participant(index: int, seed: int = None) -> Path:
    rng = random.Random(seed)
    participant_id = f"TEST_R{index:03d}"
    timestamp = datetime.utcnow().isoformat()
    suffix = participant_id.replace('TEST_', '')
    filename = DATA_DIR / f"TEST_{suffix}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.csv"
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    with filename.open('w', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(['pid', 'face_id', 'version', 'question', 'response', 'timestamp'])

        for face_num in range(1, 36):
            face_id = f"face ({face_num})"

            for version in ['left', 'right']:
                for question in LEFT_RIGHT_QUESTIONS:
                    if question == 'trust_rating':
                        response = rng.randint(1, 7)
                    else:  # emotion rating
                        response = rng.randint(1, 9)
                    writer.writerow([participant_id, face_id, version, question, response, timestamp])

            # full face block
            for question in FULL_FACE_NUMERIC:
                if question in ['trust_rating']:
                    response = rng.randint(1, 7)
                elif question in ['emotion_rating']:
                    response = rng.randint(1, 9)
                else:  # masculinity/femininity
                    response = rng.randint(1, 7)
                writer.writerow([participant_id, face_id, 'both', question, response, timestamp])

            for question in CHOICE_QUESTIONS:
                response = rng.choice(CHOICE_OPTIONS)
                writer.writerow([participant_id, face_id, 'both', question, response, timestamp])

    return filename


def main():
    parser = argparse.ArgumentParser(description='Generate random long-format test CSV files for the dashboard.')
    parser.add_argument('--count', type=int, default=10, help='Number of test participants to generate.')
    parser.add_argument('--seed', type=int, default=None, help='Random seed for reproducibility.')
    args = parser.parse_args()

    base_seed = args.seed if args.seed is not None else random.randrange(1_000_000)
    created_files = []
    for i in range(1, args.count + 1):
        created_files.append(generate_participant(i, seed=base_seed + i))

    print(f'Generated {len(created_files)} test files in {DATA_DIR.resolve()}')


if __name__ == '__main__':
    main()
