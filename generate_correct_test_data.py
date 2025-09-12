#!/usr/bin/env python3
"""
Generate correct test data for facial perception study.
Creates 60 test participants with 350 responses each (35 faces × 10 questions).
Total: 21,000 rows matching real study structure.
"""

import pandas as pd
import numpy as np
import random
from datetime import datetime, timedelta
import os

def generate_test_data():
    """Generate test data matching the real study structure."""
    
    # Set random seed for reproducibility
    np.random.seed(42)
    random.seed(42)
    
    # Study parameters
    NUM_PARTICIPANTS = 60
    NUM_FACES = 35
    QUESTIONS_PER_FACE = 10
    
    # Create data directory if it doesn't exist
    os.makedirs('data/responses', exist_ok=True)
    
    all_data = []
    
    print(f"Generating test data for {NUM_PARTICIPANTS} participants...")
    
    for participant_id in range(1, NUM_PARTICIPANTS + 1):
        participant_data = []
        pid = f"test_{participant_id:03d}"
        
        # Generate base timestamp for this participant
        base_time = datetime.now() - timedelta(days=random.randint(1, 30))
        
        for face_id in range(1, NUM_FACES + 1):
            # Generate timestamp for this face (spread over ~30 minutes)
            face_time = base_time + timedelta(minutes=random.randint(0, 30))
            
            # Generate 10 responses per face following 2-phase structure:
            # Phase 1: Half-face ratings (6 questions)
            # Phase 2: Full-face ratings (4 questions)
            
            row = {
                'pid': pid,
                'face_id': f'face_{face_id:02d}',  # face_01, face_02, etc.
                'version': 'full',  # Final rating after both phases
                'timestamp': face_time.isoformat(),
                'prolific_pid': f'TEST_{participant_id:03d}',
                'order_presented': face_id - 1,  # 0-indexed
                
                # Phase 1: Half-face ratings (6 questions)
                'trust_left': random.randint(1, 7),      # Trustworthiness (Left)
                'emotion_left': random.randint(1, 7),    # Emotion (Left)
                'trust_right': random.randint(1, 7),     # Trustworthiness (Right)
                'emotion_right': random.randint(1, 7),   # Emotion (Right)
                'masc_choice': random.choice(['left', 'right', 'neither', 'both']),  # Masculinity Comparison
                'fem_choice': random.choice(['left', 'right', 'neither', 'both']),   # Femininity Comparison
                
                # Phase 2: Full-face ratings (4 questions)
                'trust_rating': random.randint(1, 7),    # Trustworthiness (Full)
                'emotion_rating': random.randint(1, 7),  # Emotion (Full)
                'masculinity_full': random.randint(1, 7) if random.random() > 0.3 else None,  # Optional
                'femininity_full': random.randint(1, 7) if random.random() > 0.3 else None,   # Optional
                
                # Additional optional fields for future expansion
                'trust_q2': random.randint(1, 7) if random.random() > 0.3 else None,
                'trust_q3': random.randint(1, 7) if random.random() > 0.3 else None,
                'pers_q1': random.randint(1, 7) if random.random() > 0.3 else None,
                'pers_q2': random.randint(1, 7) if random.random() > 0.3 else None,
                'pers_q3': random.randint(1, 7) if random.random() > 0.3 else None,
                'pers_q4': random.randint(1, 7) if random.random() > 0.3 else None,
                'pers_q5': random.randint(1, 7) if random.random() > 0.3 else None,
            }
            
            participant_data.append(row)
            all_data.append(row)
        
        # Save individual participant file
        df_participant = pd.DataFrame(participant_data)
        filename = f'data/responses/test_{participant_id:03d}.csv'
        df_participant.to_csv(filename, index=False)
        
        if participant_id % 10 == 0:
            print(f"Generated {participant_id}/{NUM_PARTICIPANTS} participants...")
    
    # Create combined file
    df_all = pd.DataFrame(all_data)
    df_all.to_csv('data/responses/all_test_participant_data.csv', index=False)
    
    # Verification
    print(f"\n✅ Test data generation complete!")
    print(f"📊 Generated {NUM_PARTICIPANTS} participants")
    print(f"📊 Generated {NUM_FACES} faces per participant")
    print(f"📊 Generated {QUESTIONS_PER_FACE} questions per face (6 half-face + 4 full-face)")
    print(f"📊 Total rows: {len(all_data):,}")
    print(f"📊 Total responses: {len(all_data) * 10:,}")
    print(f"📁 Individual files: data/responses/test_001.csv to test_{NUM_PARTICIPANTS:03d}.csv")
    print(f"📁 Combined file: data/responses/all_test_participant_data.csv")
    
    # Verify structure
    print(f"\n🔍 Verification:")
    print(f"   Participants: {df_all['pid'].nunique()}")
    print(f"   Faces per participant: {df_all.groupby('pid')['face_id'].nunique().iloc[0]}")
    print(f"   Total unique faces: {df_all['face_id'].nunique()}")
    print(f"   Version distribution: {df_all['version'].value_counts().to_dict()}")
    print(f"   Phase 1 (half-face) fields: trust_left, emotion_left, trust_right, emotion_right, masc_choice, fem_choice")
    print(f"   Phase 2 (full-face) fields: trust_rating, emotion_rating, masculinity_full, femininity_full")
    
    return df_all

if __name__ == "__main__":
    generate_test_data()
