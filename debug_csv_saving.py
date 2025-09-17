#!/usr/bin/env python3
"""
Debug script to test CSV saving functionality directly.
This will simulate what happens when a participant completes a face.
"""

import sys
import os
from datetime import datetime
from pathlib import Path

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import save_participant_data, convert_dict_to_long_format

def create_test_session_responses():
    """Create test session responses in the nested dictionary format."""
    session_responses = {
        "face(1)": {
            "left": {
                "trust_rating": 7,
                "emotion_rating": 1
            },
            "right": {
                "trust_rating": 9,
                "emotion_rating": 3
            },
            "both": {
                "masc_choice": "right",
                "fem_choice": "left", 
                "trust_q2": 9,
                "pers_q1": 1,
                "pers_q2": 3,
                "trust_rating": 8
            }
        }
    }
    return session_responses

def test_csv_saving():
    """Test the CSV saving functionality."""
    print("🧪 Testing CSV saving functionality...")
    
    # Create test data
    participant_id = "test_debug_200"
    session_responses = create_test_session_responses()
    
    print(f"📊 Input session responses:")
    for face_id, face_data in session_responses.items():
        print(f"  {face_id}:")
        for version, version_data in face_data.items():
            print(f"    {version}: {version_data}")
    
    # Test save_participant_data function directly
    print(f"\n🔍 Testing save_participant_data function...")
    
    try:
        filepath = save_participant_data(participant_id, session_responses)
        
        if filepath:
            print(f"✅ SUCCESS: CSV file saved to {filepath}")
            
            # Check if file actually exists
            if Path(filepath).exists():
                print(f"✅ File exists on disk")
                
                # Read and display contents
                with open(filepath, 'r') as f:
                    content = f.read()
                    print(f"📄 File contents:")
                    print(content[:500] + "..." if len(content) > 500 else content)
            else:
                print(f"❌ File does not exist on disk!")
        else:
            print(f"❌ FAILED: save_participant_data returned None")
            
    except Exception as e:
        print(f"❌ ERROR: {e}")
        import traceback
        traceback.print_exc()

def check_responses_directory():
    """Check the responses directory."""
    responses_dir = Path("data/responses")
    print(f"\n📁 Checking responses directory: {responses_dir.absolute()}")
    
    if responses_dir.exists():
        print(f"✅ Directory exists")
        files = list(responses_dir.glob("*.csv"))
        print(f"📄 CSV files found: {len(files)}")
        for file in files:
            print(f"  - {file.name} ({file.stat().st_size} bytes)")
    else:
        print(f"❌ Directory does not exist")

if __name__ == "__main__":
    print("🚨 CSV SAVING DEBUG TEST")
    print("=" * 50)
    
    check_responses_directory()
    test_csv_saving()
    check_responses_directory()
    
    print("=" * 50)
    print("🏁 Debug test complete")
