#!/usr/bin/env python3
"""
Generate test submission with proper 10-row long format
"""

import pandas as pd
import time
from pathlib import Path

def generate_test_submission(pid='TEST', face_id='face(1)'):
    """Generate a complete test submission with all 10 questions"""
    timestamp = time.strftime('%Y%m%d_%H%M%S')
    
    data = [
        [pid, face_id, 'left',  'trust_rating',   9, timestamp],
        [pid, face_id, 'left',  'emotion_rating', 1, timestamp],
        [pid, face_id, 'right', 'trust_rating',   9, timestamp],
        [pid, face_id, 'right', 'emotion_rating', 1, timestamp],
        [pid, face_id, 'both',  'masc_choice',    'left', timestamp],
        [pid, face_id, 'both',  'fem_choice',     'right', timestamp],
        [pid, face_id, 'both',  'masculinity',    'left', timestamp],
        [pid, face_id, 'both',  'femininity',     'right', timestamp],
        [pid, face_id, 'both',  'trust_rating',   9, timestamp],
        [pid, face_id, 'both',  'emotion_rating', 1, timestamp],
    ]
    
    df = pd.DataFrame(data, columns=['pid', 'face_id', 'version', 'question', 'response', 'timestamp'])
    
    # Ensure data/responses directory exists
    Path('data/responses').mkdir(parents=True, exist_ok=True)
    
    filepath = f'data/responses/{pid}_{timestamp}.csv'
    df.to_csv(filepath, index=False)
    
    print(f"Generated test submission: {filepath}")
    print(f"Rows: {len(df)}")
    print(df.to_string(index=False))
    
    return filepath

if __name__ == "__main__":
    # Generate test data
    generate_test_submission('TEST_001', 'face(1)')
    generate_test_submission('TEST_002', 'face(2)')
