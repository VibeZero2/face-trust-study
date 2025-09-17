#!/usr/bin/env python3
"""
Test wide format conversion to verify it's actually wide (not duplicate long)
"""

import sys
sys.path.append('.')

from app import convert_dict_to_wide_template

# Mock complete face data with all 10 questions
test_responses = {
    "face(34)": {
        "participant_id": "200",
        "left": {
            "trust_rating": "8",
            "emotion_rating": "1"
        },
        "right": {
            "trust_rating": "9", 
            "emotion_rating": "1"
        },
        "both": {
            "trust_rating": "9",
            "emotion_rating": "7",
            "masculinity": "5",
            "femininity": "6", 
            "masc_choice": "left",
            "fem_choice": "right"
        }
    }
}

print("Testing WIDE format conversion...")
wide_rows = convert_dict_to_wide_template("200", test_responses)

print(f"Number of rows: {len(wide_rows)} (should be 1)")
print(f"Number of columns: {len(wide_rows[0]) if wide_rows else 0}")

if wide_rows:
    print("\nWide format row:")
    for key, value in wide_rows[0].items():
        print(f"  {key:>18}: {value}")
    
    # Check if it has the expected wide format structure
    expected_cols = ["pid", "face_id", "trust_left", "emotion_left", "trust_right", "emotion_right", 
                    "masc_choice", "fem_choice", "trust_rating", "emotion_rating", "masculinity_full", "femininity_full"]
    
    actual_cols = list(wide_rows[0].keys())
    print(f"\nExpected columns: {len(expected_cols)}")
    print(f"Actual columns: {len(actual_cols)}")
    
    if set(actual_cols) == set(expected_cols):
        print("✅ Wide format has correct column structure!")
    else:
        print("❌ Wide format column mismatch")
        print(f"Missing: {set(expected_cols) - set(actual_cols)}")
        print(f"Extra: {set(actual_cols) - set(expected_cols)}")
else:
    print("❌ No wide format rows generated")
