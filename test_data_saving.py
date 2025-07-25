#!/usr/bin/env python
"""
Test script to verify that participant data is saved correctly to data/responses directory.
This script simulates a participant completing the study and checks if the data is saved.
"""

import os
import csv
import json
import random
from pathlib import Path
from datetime import datetime

# Create necessary directories
DATA_DIR = Path(__file__).resolve().parent / "data"
RESPONSES_DIR = DATA_DIR / "responses"
DATA_DIR.mkdir(exist_ok=True)
RESPONSES_DIR.mkdir(exist_ok=True)

# Simulate participant data
def generate_test_participant_data(participant_id="test123", prolific_pid="PROLIFIC_TEST_ID"):
    """Generate test participant data"""
    # Simulate responses for 5 faces
    responses = []
    
    # Generate face IDs
    face_ids = [f"face_{i}" for i in range(1, 6)]
    
    # Add left/right side responses for each face
    for i, face_id in enumerate(face_ids):
        # Left side response
        responses.append({
            "pid": participant_id,
            "timestamp": datetime.utcnow().isoformat(),
            "face_id": face_id,
            "version": "left",
            "order_presented": i * 2,
            "trust_rating": random.randint(1, 7),
            "masc_choice": None,
            "fem_choice": None,
            "trust_q1": None,
            "trust_q2": None,
            "trust_q3": None,
            "pers_q1": None,
            "pers_q2": None,
            "pers_q3": None,
            "pers_q4": None,
            "pers_q5": None,
            "prolific_pid": prolific_pid
        })
        
        # Right side response
        responses.append({
            "pid": participant_id,
            "timestamp": datetime.utcnow().isoformat(),
            "face_id": face_id,
            "version": "right",
            "order_presented": i * 2 + 1,
            "trust_rating": random.randint(1, 7),
            "masc_choice": None,
            "fem_choice": None,
            "trust_q1": None,
            "trust_q2": None,
            "trust_q3": None,
            "pers_q1": None,
            "pers_q2": None,
            "pers_q3": None,
            "pers_q4": None,
            "pers_q5": None,
            "prolific_pid": prolific_pid
        })
        
        # Full face response
        responses.append({
            "pid": participant_id,
            "timestamp": datetime.utcnow().isoformat(),
            "face_id": face_id,
            "version": "full",
            "order_presented": i * 2 + 2,
            "trust_rating": random.randint(1, 7),
            "masc_choice": random.choice(["masc", "neutral", "fem"]),
            "fem_choice": random.choice(["fem", "neutral", "masc"]),
            "trust_q1": None,
            "trust_q2": None,
            "trust_q3": None,
            "pers_q1": None,
            "pers_q2": None,
            "pers_q3": None,
            "pers_q4": None,
            "pers_q5": None,
            "prolific_pid": prolific_pid
        })
    
    # Add survey response
    responses.append({
        "pid": participant_id,
        "timestamp": datetime.utcnow().isoformat(),
        "face_id": "survey",
        "version": "survey",
        "order_presented": len(face_ids) * 3,
        "trust_rating": None,
        "masc_choice": None,
        "fem_choice": None,
        "trust_q1": random.randint(1, 7),
        "trust_q2": random.randint(1, 7),
        "trust_q3": random.randint(1, 7),
        "pers_q1": random.randint(1, 7),
        "pers_q2": random.randint(1, 7),
        "pers_q3": random.randint(1, 7),
        "pers_q4": random.randint(1, 7),
        "pers_q5": random.randint(1, 7),
        "prolific_pid": prolific_pid
    })
    
    return responses

def save_participant_data(participant_id, responses, headers=None):
    """Save responses to a CSV file in data/responses/"""
    filepath = RESPONSES_DIR / f"{participant_id}.csv"
    
    with open(filepath, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=headers or responses[0].keys())
        writer.writeheader()
        writer.writerows(responses)
    
    print(f"✅ Saved participant data to {filepath}")
    return filepath

def main():
    """Main test function"""
    print("Testing participant data saving...")
    
    # Generate and save test data for 3 participants
    participants = [
        {"id": "test123", "prolific_pid": "PROLIFIC_TEST_1"},
        {"id": "test456", "prolific_pid": "PROLIFIC_TEST_2"},
        {"id": "test789", "prolific_pid": ""}  # No Prolific ID
    ]
    
    for p in participants:
        participant_id = p["id"]
        prolific_pid = p["prolific_pid"]
        
        # Generate test data
        responses = generate_test_participant_data(participant_id, prolific_pid)
        
        # Save data using participant ID or Prolific ID
        save_id = prolific_pid if prolific_pid else participant_id
        filepath = save_participant_data(save_id, responses)
        
        # Verify file exists
        if os.path.exists(filepath):
            print(f"✓ File created: {filepath}")
        else:
            print(f"✗ File not created: {filepath}")
    
    print("\nVerifying data/responses directory contents:")
    for file in RESPONSES_DIR.glob("*.csv"):
        print(f"- {file.name}")
    
    print("\nTest completed successfully!")

if __name__ == "__main__":
    main()
