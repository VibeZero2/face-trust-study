#!/usr/bin/env python3
"""
Production Data Generator for Facial Trust Study
Generates 60 participants × 35 faces × 10 questions = 21,000 total responses
Format: One row per response (not per face)
"""

import pandas as pd
import random
import os
from pathlib import Path

def generate_participant_responses(participant_id, num_faces=35):
    """
    Generate all responses for one participant viewing all 35 faces.
    Each face has 10 questions, so 350 total responses per participant.
    Format: One row per response
    """
    
    # Face IDs: face_01 to face_35
    face_ids = [f"face_{i:02d}" for i in range(1, num_faces + 1)]
    
    all_responses = []
    
    for face_id in face_ids:
        # Phase 1: Half-Face Ratings (6 responses)
        # Left half
        all_responses.append({
            'pid': participant_id,
            'face_id': face_id,
            'version': 'left',
            'question': 'trust',
            'response': random.randint(1, 9)
        })
        all_responses.append({
            'pid': participant_id,
            'face_id': face_id,
            'version': 'left',
            'question': 'emotion',
            'response': random.randint(1, 9)
        })
        
        # Right half
        all_responses.append({
            'pid': participant_id,
            'face_id': face_id,
            'version': 'right',
            'question': 'trust',
            'response': random.randint(1, 9)
        })
        all_responses.append({
            'pid': participant_id,
            'face_id': face_id,
            'version': 'right',
            'question': 'emotion',
            'response': random.randint(1, 9)
        })
        
        # Comparison questions (use 'both' version for full face comparisons)
        all_responses.append({
            'pid': participant_id,
            'face_id': face_id,
            'version': 'both',
            'question': 'masc_choice',
            'response': random.choice(['left', 'right', 'both', 'neither'])
        })
        all_responses.append({
            'pid': participant_id,
            'face_id': face_id,
            'version': 'both',
            'question': 'fem_choice',
            'response': random.choice(['left', 'right', 'both', 'neither'])
        })
        
        # Phase 2: Full-Face Ratings (4 responses)
        all_responses.append({
            'pid': participant_id,
            'face_id': face_id,
            'version': 'both',
            'question': 'trust',
            'response': random.randint(1, 9)
        })
        all_responses.append({
            'pid': participant_id,
            'face_id': face_id,
            'version': 'both',
            'question': 'emotion',
            'response': random.randint(1, 9)
        })
        all_responses.append({
            'pid': participant_id,
            'face_id': face_id,
            'version': 'both',
            'question': 'masculinity_full',
            'response': random.randint(1, 9)
        })
        all_responses.append({
            'pid': participant_id,
            'face_id': face_id,
            'version': 'both',
            'question': 'femininity_full',
            'response': random.randint(1, 9)
        })
    
    return all_responses

def generate_all_participants(num_participants=60, num_faces=35):
    """
    Generate data for all participants.
    """
    all_responses = []
    
    print(f"🎯 Generating data for {num_participants} participants...")
    print(f"   Each participant: {num_faces} faces × 10 questions = {num_faces * 10} responses")
    print(f"   Total expected: {num_participants} × {num_faces * 10} = {num_participants * num_faces * 10} responses")
    
    for i in range(1, num_participants + 1):
        participant_id = f"test_{i:03d}"
        participant_responses = generate_participant_responses(participant_id, num_faces)
        all_responses.extend(participant_responses)
        
        if i % 10 == 0:
            print(f"   Generated participant {i}/{num_participants} ({len(participant_responses)} responses)")
    
    return all_responses

def save_individual_csvs(data, output_dir="data/responses"):
    """
    Save each participant's data as a separate CSV file.
    """
    output_path = Path(output_dir)
    output_path.mkdir(exist_ok=True)
    
    # Group data by participant
    df = pd.DataFrame(data)
    participants = df['pid'].unique()
    
    print(f"💾 Saving {len(participants)} individual CSV files...")
    
    for participant_id in participants:
        participant_data = df[df['pid'] == participant_id]
        filename = f"{participant_id}.csv"
        filepath = output_path / filename
        
        # Save without index
        participant_data.to_csv(filepath, index=False)
        
        if int(participant_id.split('_')[1]) % 10 == 0:
            print(f"   Saved {filename} ({len(participant_data)} responses)")
    
    print(f"✅ All files saved to {output_dir}/")

def save_combined_csv(data, output_dir="data/responses"):
    """
    Save all data as one combined CSV file.
    """
    output_path = Path(output_dir)
    output_path.mkdir(exist_ok=True)
    
    df = pd.DataFrame(data)
    combined_file = output_path / "all_participants_combined.csv"
    df.to_csv(combined_file, index=False)
    
    print(f"📊 Combined file saved: {combined_file}")
    return combined_file

def verify_data_structure(data):
    """
    Verify the data structure matches expectations.
    """
    df = pd.DataFrame(data)
    
    print(f"\n🔍 Data Structure Verification:")
    print(f"   Total responses: {len(df)}")
    print(f"   Unique participants: {df['pid'].nunique()}")
    print(f"   Unique faces: {df['face_id'].nunique()}")
    print(f"   Unique versions: {df['version'].unique()}")
    print(f"   Unique questions: {df['question'].unique()}")
    
    # Check responses per participant
    responses_per_participant = df.groupby('pid').size()
    expected_responses = 35 * 10  # 35 faces × 10 questions
    print(f"   Responses per participant: {responses_per_participant.iloc[0]} (expected: {expected_responses})")
    
    # Check if all participants have the same number of responses
    if responses_per_participant.nunique() == 1:
        print(f"   ✅ All participants have consistent response counts")
    else:
        print(f"   ❌ Inconsistent response counts across participants")
    
    return df

def main():
    """
    Main function to generate all production data.
    """
    print("🚀 Starting Production Data Generation")
    print("=" * 60)
    
    # Configuration
    NUM_PARTICIPANTS = 60
    NUM_FACES = 35
    OUTPUT_DIR = "data/responses"
    
    # Generate all data
    all_data = generate_all_participants(NUM_PARTICIPANTS, NUM_FACES)
    
    # Verify data structure
    df = verify_data_structure(all_data)
    
    # Save individual CSV files
    save_individual_csvs(all_data, OUTPUT_DIR)
    
    # Save combined CSV
    save_combined_csv(all_data, OUTPUT_DIR)
    
    print(f"\n🎉 Production data generation complete!")
    print(f"   Files created: {NUM_PARTICIPANTS} individual + 1 combined")
    print(f"   Location: {OUTPUT_DIR}/")
    print(f"   Total responses: {len(all_data)}")
    print(f"   Ready for dashboard testing!")

if __name__ == "__main__":
    main()