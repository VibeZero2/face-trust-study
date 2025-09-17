#!/usr/bin/env python3
"""
Test script to validate CSV output format for psychology study.
This will simulate participant responses and check the CSV format.
"""

import sys
import os
from datetime import datetime

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import convert_dict_to_long_format

def create_test_responses():
    """Create test responses in the expected nested dictionary format."""
    test_responses = {
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
        },
        "face(2)": {
            "left": {
                "trust_rating": 5,
                "emotion_rating": 2
            },
            "right": {
                "trust_rating": 6,
                "emotion_rating": 4
            },
            "both": {
                "masc_choice": "left",
                "fem_choice": "right",
                "trust_q2": 7,
                "pers_q1": 3,
                "pers_q2": 5,
                "trust_rating": 6
            }
        }
    }
    return test_responses

def test_csv_conversion():
    """Test the CSV conversion function."""
    print("🧪 Testing CSV conversion function...")
    
    # Create test data
    participant_id = "200"
    test_responses = create_test_responses()
    
    print(f"📊 Input data structure:")
    for face_id, face_data in test_responses.items():
        print(f"  {face_id}:")
        for version, version_data in face_data.items():
            print(f"    {version}: {len(version_data)} questions")
    
    # Convert to long format
    long_responses = convert_dict_to_long_format(participant_id, test_responses)
    
    print(f"\n✅ Conversion Results:")
    print(f"   Total rows: {len(long_responses)}")
    print(f"   Expected: 20 rows (2 faces × 10 questions each)")
    
    # Check format
    if len(long_responses) > 0:
        print(f"\n📋 Sample CSV rows:")
        print("pid,face_id,version,question,response,timestamp")
        
        face1_rows = [row for row in long_responses if row['face_id'] == 'face(1)']
        face2_rows = [row for row in long_responses if row['face_id'] == 'face(2)']
        
        print(f"\n🎯 Face(1) - {len(face1_rows)} rows:")
        for row in face1_rows[:5]:  # Show first 5
            print(f"{row['pid']},{row['face_id']},{row['version']},{row['question']},{row['response']},{row['timestamp']}")
        if len(face1_rows) > 5:
            print("...")
            
        print(f"\n🎯 Face(2) - {len(face2_rows)} rows:")
        for row in face2_rows[:5]:  # Show first 5
            print(f"{row['pid']},{row['face_id']},{row['version']},{row['question']},{row['response']},{row['timestamp']}")
        if len(face2_rows) > 5:
            print("...")
    
    # Validate version field
    versions_found = set(row['version'] for row in long_responses)
    expected_versions = {'left', 'right', 'both'}
    
    print(f"\n🔍 Version Validation:")
    print(f"   Found versions: {versions_found}")
    print(f"   Expected versions: {expected_versions}")
    print(f"   ✅ All versions present: {expected_versions.issubset(versions_found)}")
    
    # Check for empty version fields
    empty_versions = [row for row in long_responses if not row['version'] or row['version'] == '']
    print(f"   ❌ Empty version fields: {len(empty_versions)}")
    
    if len(empty_versions) == 0:
        print("   ✅ NO EMPTY VERSION FIELDS - FIX SUCCESSFUL!")
    else:
        print("   ❌ STILL HAS EMPTY VERSION FIELDS - FIX FAILED!")
        
    return len(long_responses), len(empty_versions) == 0

if __name__ == "__main__":
    print("🚨 CRITICAL CSV FORMAT TEST - Study launches tomorrow!")
    print("=" * 60)
    
    total_rows, version_fix_success = test_csv_conversion()
    
    print("\n" + "=" * 60)
    print("📊 FINAL RESULTS:")
    print(f"   Total CSV rows generated: {total_rows}")
    print(f"   Version field fix successful: {'✅ YES' if version_fix_success else '❌ NO'}")
    
    if version_fix_success and total_rows == 20:
        print("\n🎉 SUCCESS! CSV format is correct for study launch!")
    else:
        print("\n🚨 FAILURE! CSV format still has issues!")
        
    print("=" * 60)
