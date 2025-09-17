"""
Test Data Generator for Facial Trust Study

This script generates realistic test data for the facial trust study with the following structure:
- 60 test participants (test_001 to test_060)
- 35 face images (face_01 to face_35)
- Each participant rates each face in two phases:
  Phase 1: Half-face ratings (6 questions)
  Phase 2: Full-face ratings (4 questions)
"""

import os
import random
import pandas as pd
from pathlib import Path
from datetime import datetime, timedelta

# Configuration - EXACTLY 60 participants as per IRB protocol
NUM_PARTICIPANTS = 60
NUM_FACES = 35
OUTPUT_DIR = Path("data/responses")

# Ensure output directory exists
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Response options
MASCULINITY_CHOICES = ["Left", "Right", "Both Equally", "Neither"]
FEMININITY_CHOICES = ["Left", "Right", "Both Equally", "Neither"]
LIKERT_SCALE = list(range(1, 10))  # 1-9 scale

def generate_participant_data(participant_id, num_faces):
    """Generate test data for a single participant in long format."""
    data = []
    
    # Generate start time for this participant (spread over several days)
    start_time = datetime.now() - timedelta(hours=random.randint(1, 48))
    
    for face_num in range(1, num_faces + 1):
        face_id = f"face_{face_num:02d}"
        
        # Generate base timestamp for this face
        face_timestamp = start_time + timedelta(seconds=random.randint(30, 120))
        
        # Generate 10 rows per face (exactly as specified)
        questions = [
            # LEFT responses (2 questions)
            {'version': 'left', 'question': 'trust_rating', 'response': random.randint(1, 9)},
            {'version': 'left', 'question': 'emotion_rating', 'response': random.randint(1, 9)},
            
            # RIGHT responses (2 questions)
            {'version': 'right', 'question': 'trust_rating', 'response': random.randint(1, 9)},
            {'version': 'right', 'question': 'emotion_rating', 'response': random.randint(1, 9)},
            
            # BOTH responses (6 questions)
            {'version': 'both', 'question': 'trust_rating', 'response': random.randint(1, 9)},
            {'version': 'both', 'question': 'emotion_rating', 'response': random.randint(1, 9)},
            {'version': 'both', 'question': 'masc_choice', 'response': random.choice(['left', 'right'])},
            {'version': 'both', 'question': 'fem_choice', 'response': random.choice(['left', 'right', 'neither'])},
            {'version': 'both', 'question': 'masculinity', 'response': random.choice(['left', 'right'])},
            {'version': 'both', 'question': 'femininity', 'response': random.choice(['left', 'right'])}
        ]
        
        # Create 10 rows for this face
        for i, q in enumerate(questions):
            # Add slight time variation between questions (1-5 seconds)
            question_timestamp = face_timestamp + timedelta(seconds=i)
            
            data.append({
                'pid': participant_id,
                'face_id': face_id,
                'version': q['version'],
                'question': q['question'],
                'response': q['response'],
                'timestamp': question_timestamp.isoformat()
            })
        
        # Increment time for next face
        start_time = face_timestamp + timedelta(seconds=random.randint(30, 120))
    
    return pd.DataFrame(data)

def generate_all_data():
    """Generate test data for all participants and save to files."""
    all_data = []
    
    # Generate data for each participant
    for i in range(1, NUM_PARTICIPANTS + 1):
        participant_id = f"test_{i:03d}"
        print(f"Generating data for {participant_id}...")
        
        # Generate individual participant data
        df_participant = generate_participant_data(participant_id, NUM_FACES)
        
        # Save individual participant file with correct naming
        output_file = OUTPUT_DIR / f"{participant_id}.csv"
        df_participant.to_csv(output_file, index=False)
        
        # Add to combined dataset
        all_data.append(df_participant)
    
    # Combine all participant data
    if all_data:
        df_all = pd.concat(all_data, ignore_index=True)
        combined_file = OUTPUT_DIR / "test_participants_combined.csv"
        df_all.to_csv(combined_file, index=False)
        print(f"\nGenerated data for {NUM_PARTICIPANTS} participants with {NUM_FACES} faces each.")
        print(f"Individual files saved to: {OUTPUT_DIR}/test_*.csv")
        print(f"Combined data saved to: {combined_file}")
    else:
        print("No data was generated.")

if __name__ == "__main__":
    generate_all_data()
