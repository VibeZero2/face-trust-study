#!/usr/bin/env python3
"""
Test CSV creation during form submission by simulating the complete process
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import create_participant_run, save_participant_data, convert_dict_to_long_format
from pathlib import Path
import json
from datetime import datetime

def test_csv_creation_flow():
    print("🧪 Testing complete CSV creation flow...")
    
    # Test participant ID
    test_pid = f"csv_test_{int(datetime.now().timestamp())}"
    print(f"Testing with participant ID: {test_pid}")
    
    # Step 1: Create mock session data like the app would
    print("\n1. Creating mock session responses...")
    
    # Simulate responses for one face (10 questions total)
    # The convert_dict_to_long_format function expects only version data (left, right, both)
    mock_responses = {
        "face(1)": {
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
                "fem_choice": "right",
                "masculinity": "left",
                "femininity": "right"
            }
        }
    }
    
    print(f"✅ Created mock responses for {len(mock_responses)} faces")
    
    # Step 2: Test convert_dict_to_long_format function
    print("\n2. Testing convert_dict_to_long_format...")
    
    try:
        long_responses = convert_dict_to_long_format(test_pid, mock_responses)
        print(f"✅ Conversion successful: {len(long_responses)} rows created")
        
        # Verify the structure
        if long_responses:
            first_row = long_responses[0]
            required_keys = ["pid", "face_id", "version", "question", "response", "timestamp"]
            missing_keys = [key for key in required_keys if key not in first_row]
            
            if not missing_keys:
                print("✅ All required CSV columns present")
            else:
                print(f"❌ Missing CSV columns: {missing_keys}")
                
            # Check version field specifically
            versions_found = set(row["version"] for row in long_responses)
            expected_versions = {"left", "right", "both"}
            if expected_versions.issubset(versions_found):
                print("✅ All expected versions found: left, right, both")
            else:
                print(f"❌ Missing versions. Found: {versions_found}, Expected: {expected_versions}")
                
        else:
            print("❌ No rows created from conversion")
            
    except Exception as e:
        print(f"❌ Conversion failed: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # Step 3: Test save_participant_data function
    print("\n3. Testing save_participant_data...")
    
    try:
        filepath = save_participant_data(test_pid, mock_responses)
        
        if filepath and Path(filepath).exists():
            print(f"✅ CSV file created successfully: {filepath}")
            
            # Verify file content
            with open(filepath, 'r') as f:
                content = f.read()
                lines = content.strip().split('\n')
                
                print(f"✅ CSV file has {len(lines)} lines (including header)")
                
                # Check header
                if lines and "pid,face_id,version,question,response,timestamp" in lines[0]:
                    print("✅ CSV header is correct")
                else:
                    print(f"❌ CSV header incorrect. Found: {lines[0] if lines else 'No header'}")
                
                # Count data rows (should be 10 for one complete face)
                data_rows = len(lines) - 1  # Subtract header
                if data_rows == 10:
                    print(f"✅ Correct number of data rows: {data_rows}")
                else:
                    print(f"❌ Expected 10 data rows, found: {data_rows}")
                
                # Show sample rows
                print("\nSample CSV content:")
                for i, line in enumerate(lines[:5]):  # Show first 5 lines
                    print(f"  {i}: {line}")
                    
        else:
            print("❌ CSV file was not created")
            
    except Exception as e:
        print(f"❌ CSV save failed: {e}")
        import traceback
        traceback.print_exc()
    
    # Step 4: Check data directory
    print("\n4. Checking data directory...")
    
    data_dir = Path("data/responses")
    if data_dir.exists():
        csv_files = list(data_dir.glob("*.csv"))
        print(f"✅ Found {len(csv_files)} CSV files in data/responses/")
        
        # Show recent files
        recent_files = [f for f in csv_files if test_pid in f.name]
        if recent_files:
            print(f"✅ Found {len(recent_files)} files for test participant")
            for f in recent_files:
                print(f"  - {f.name}")
        else:
            print("❌ No files found for test participant")
    else:
        print("❌ data/responses directory does not exist")

if __name__ == "__main__":
    test_csv_creation_flow()
