#!/usr/bin/env python3
"""
Simple test to verify CSV creation works
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import save_participant_data, convert_dict_to_long_format
from pathlib import Path
import time

def test_csv_creation():
    print("🧪 Testing CSV creation directly...")
    
    # Test data in the format the app uses
    test_pid = f"direct_csv_test_{int(time.time())}"
    
    # Mock session responses structure
    mock_responses = {
        "face(1)": {
            "participant_id": test_pid,
            "timestamp": "2025-09-15T06:00:00.000000",
            "face_id": "face(1)",
            "prolific_pid": "",
            "left": {
                "trust_rating": "7",
                "emotion_rating": "3"
            },
            "right": {
                "trust_rating": "8", 
                "emotion_rating": "4"
            },
            "both": {
                "trust_rating": "6",
                "emotion_rating": "5",
                "masc_choice": "left",
                "fem_choice": "right"
            }
        }
    }
    
    print(f"Testing with participant ID: {test_pid}")
    
    # Test save_participant_data directly
    try:
        filepath = save_participant_data(test_pid, mock_responses)
        
        if filepath and Path(filepath).exists():
            print(f"✅ CSV file created: {filepath}")
            
            # Check content
            with open(filepath, 'r') as f:
                content = f.read()
                lines = content.strip().split('\n')
                print(f"✅ CSV has {len(lines)} lines (including header)")
                
                # Show first few lines
                for i, line in enumerate(lines[:5]):
                    print(f"  {i}: {line}")
                    
                return True
        else:
            print("❌ CSV file not created")
            return False
            
    except Exception as e:
        print(f"❌ Error creating CSV: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_csv_creation()
    if success:
        print("\n✅ CSV creation works correctly")
    else:
        print("\n❌ CSV creation failed")
