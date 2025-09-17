#!/usr/bin/env python3
"""
Test if we now get all 10 rows per face after fixing the masculinity/femininity skip
"""

import sys
sys.path.append('.')

from app import convert_dict_to_long_format

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

print("Testing CSV conversion with all 10 questions...")
long_rows = convert_dict_to_long_format("200", test_responses)

print(f"Total rows generated: {len(long_rows)}")
print("\nRows breakdown:")
for i, row in enumerate(long_rows, 1):
    print(f"{i:2d}. {row['version']:>5} | {row['question']:>15} | {row['response']}")

if len(long_rows) == 10:
    print("\n✅ SUCCESS: Got all 10 rows!")
else:
    print(f"\n❌ PROBLEM: Expected 10 rows, got {len(long_rows)}")
