"""
Generate a single test participant with complete dataset for format comparison.
Creates one participant (test_001) with all 35 faces and 10 questions per face.
"""

import os
import random
import pandas as pd
from pathlib import Path
from datetime import datetime, timedelta

# Configuration
OUTPUT_DIR = Path("data/responses")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Response options
MASCULINITY_CHOICES = ["Left", "Right", "Both Equally", "Neither"]
FEMININITY_CHOICES = ["Left", "Right", "Both Equally", "Neither"]
LIKERT_SCALE = list(range(1, 10))  # 1-9 scale

def generate_single_participant():
    """Generate test data for one complete participant."""
    data = []
    participant_id = "test_001"
    
    # Generate start time
    start_time = datetime.now() - timedelta(days=random.randint(1, 7))
    
    for face_num in range(1, 36):  # 35 faces
        face_id = f"face_{face_num:02d}"
        timestamp = start_time + timedelta(minutes=random.randint(1, 15))
        
        # Phase 1: Half-face ratings (6 questions)
        trust_left = random.choice(LIKERT_SCALE)
        emotion_left = random.choice(LIKERT_SCALE)
        trust_right = random.choice(LIKERT_SCALE)
        emotion_right = random.choice(LIKERT_SCALE)
        masc_choice = random.choice(MASCULINITY_CHOICES)
        fem_choice = random.choice(FEMININITY_CHOICES)
        
        # Phase 2: Full-face ratings (4 questions)
        trust_rating = random.choice(LIKERT_SCALE)
        emotion_rating = random.choice(LIKERT_SCALE)
        masculinity_full = random.choice(LIKERT_SCALE)
        femininity_full = random.choice(LIKERT_SCALE)
        
        data.append({
            'pid': participant_id,
            'face_id': face_id,
            'timestamp': timestamp.isoformat(),
            # Phase 1: Half-face ratings
            'trust_left': trust_left,
            'emotion_left': emotion_left,
            'trust_right': trust_right,
            'emotion_right': emotion_right,
            'masc_choice': masc_choice,
            'fem_choice': fem_choice,
            # Phase 2: Full-face ratings
            'trust_rating': trust_rating,
            'emotion_rating': emotion_rating,
            'masculinity_full': masculinity_full,
            'femininity_full': femininity_full,
            # Additional required fields for dashboard compatibility
            'response_time': random.randint(2000, 8000),  # milliseconds
            'version': random.choice(['A', 'B']),
            'include_in_primary': True,
            'session_complete': True
        })
        
        # Increment time for next face
        start_time = timestamp + timedelta(seconds=random.randint(30, 120))
    
    return pd.DataFrame(data)

def main():
    """Generate and save single test participant data."""
    print("Generating single test participant data...")
    
    # Generate data
    df = generate_single_participant()
    
    # Save to file
    output_file = OUTPUT_DIR / "single_test_participant.csv"
    df.to_csv(output_file, index=False)
    
    print(f"Generated data for 1 participant with {len(df)} rows (35 faces × 10 questions)")
    print(f"Saved to: {output_file}")
    
    # Display first few rows for format verification
    print("\nFirst 5 rows:")
    print(df.head().to_string())
    
    print(f"\nColumns: {list(df.columns)}")
    print(f"Total rows: {len(df)}")

if __name__ == "__main__":
    main()
