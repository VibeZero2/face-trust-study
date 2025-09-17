#!/usr/bin/env python3
"""
Test complete face submission to verify all 10 questions are saved correctly
"""

import sys
sys.path.append('.')

from app import convert_dict_to_long_format

# Test data matching exact study structure
test_responses = {
    "face(6)": {
        "participant_id": "200",
        "left": {
            "trust_rating": "9",
            "emotion_rating": "1"
        },
        "right": {
            "trust_rating": "9", 
            "emotion_rating": "1"
        },
        "both": {
            "masc_choice": "left",
            "fem_choice": "right",
            "masculinity": "left",
            "femininity": "right",
            "trust_rating": "9",
            "emotion_rating": "1"
        }
    }
}

print("Testing complete face submission...")
long_rows = convert_dict_to_long_format("200", test_responses)

print(f"\nTotal rows: {len(long_rows)} (expected: 10)")
print("\nDetailed breakdown:")
print("PID | Face ID | Version | Question | Response")
print("-" * 50)

for row in long_rows:
    print(f"{row['pid']:>3} | {row['face_id']:>7} | {row['version']:>7} | {row['question']:>15} | {row['response']}")

# Verify expected structure
expected_questions = {
    'left': ['trust_rating', 'emotion_rating'],
    'right': ['trust_rating', 'emotion_rating'], 
    'both': ['masc_choice', 'fem_choice', 'masculinity', 'femininity', 'trust_rating', 'emotion_rating']
}

print(f"\n=== VALIDATION ===")
for version, expected in expected_questions.items():
    actual = [row['question'] for row in long_rows if row['version'] == version]
    print(f"{version:>5}: Expected {len(expected)}, Got {len(actual)} - {actual}")
    
if len(long_rows) == 10:
    print("\n✅ SUCCESS: All 10 questions saved correctly!")
else:
    print(f"\n❌ PROBLEM: Expected 10 rows, got {len(long_rows)}")
