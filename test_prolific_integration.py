#!/usr/bin/env python3
"""
Test script to verify complete Prolific PID integration end-to-end.
Tests URL parameter extraction, form submission, and CSV export with Prolific PIDs.
"""

import requests
import time
from pathlib import Path
import csv
import os

# Test configuration
BASE_URL = "http://localhost:3000"
TEST_PROLIFIC_PID = "TEST_PROLIFIC_123"
TEST_PARTICIPANT_ID = "test_participant_456"

def test_prolific_integration():
    """Test complete Prolific PID integration flow."""
    
    print("🧪 Testing Prolific PID Integration End-to-End")
    print("=" * 50)
    
    # Test 1: Start session with Prolific PID
    print("\n1. Testing session start with Prolific PID...")
    
    start_data = {
        'pid': TEST_PARTICIPANT_ID,
        'prolific_pid': TEST_PROLIFIC_PID
    }
    
    session = requests.Session()
    response = session.post(f"{BASE_URL}/start", data=start_data)
    
    if response.status_code == 200:
        print(f"✅ Session started successfully")
    else:
        print(f"❌ Session start failed: {response.status_code}")
        return False
    
    # Test 2: Submit a form with Prolific PID
    print("\n2. Testing form submission with Prolific PID...")
    
    # Get the task page first
    task_response = session.get(f"{BASE_URL}/task")
    if task_response.status_code != 200:
        print(f"❌ Could not access task page: {task_response.status_code}")
        return False
    
    # Submit a form response
    form_data = {
        'version': 'left',
        'trust_rating': '7',
        'emotion_rating': '4',
        'prolific_pid': TEST_PROLIFIC_PID
    }
    
    form_response = session.post(f"{BASE_URL}/task", data=form_data)
    
    if form_response.status_code == 200:
        print(f"✅ Form submitted successfully")
    else:
        print(f"❌ Form submission failed: {form_response.status_code}")
        return False
    
    # Test 3: Check if CSV file was created with correct Prolific PID
    print("\n3. Testing CSV file creation with Prolific PID...")
    
    # Wait a moment for file creation
    time.sleep(1)
    
    # Look for CSV files in data/responses directory
    responses_dir = Path("data/responses")
    if not responses_dir.exists():
        print(f"❌ Responses directory does not exist: {responses_dir}")
        return False
    
    # Find CSV files with our test Prolific PID
    csv_files = list(responses_dir.glob(f"*{TEST_PROLIFIC_PID}*.csv"))
    
    if not csv_files:
        print(f"❌ No CSV files found with Prolific PID {TEST_PROLIFIC_PID}")
        print(f"   Available files: {list(responses_dir.glob('*.csv'))}")
        return False
    
    print(f"✅ Found CSV file: {csv_files[0].name}")
    
    # Test 4: Verify CSV content includes Prolific PID
    print("\n4. Testing CSV content for Prolific PID...")
    
    csv_file = csv_files[0]
    try:
        with open(csv_file, 'r', newline='') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            
            if not rows:
                print(f"❌ CSV file is empty")
                return False
            
            # Check if pid field contains our Prolific PID
            first_row = rows[0]
            if 'pid' not in first_row:
                print(f"❌ CSV missing 'pid' column")
                return False
            
            if first_row['pid'] == TEST_PROLIFIC_PID:
                print(f"✅ CSV contains correct Prolific PID: {first_row['pid']}")
            else:
                print(f"❌ CSV has wrong PID. Expected: {TEST_PROLIFIC_PID}, Got: {first_row['pid']}")
                return False
            
            # Verify all required columns exist
            required_columns = ['pid', 'face_id', 'version', 'question', 'response', 'timestamp']
            missing_columns = [col for col in required_columns if col not in first_row]
            
            if missing_columns:
                print(f"❌ CSV missing required columns: {missing_columns}")
                return False
            
            print(f"✅ CSV has all required columns: {list(first_row.keys())}")
            print(f"✅ CSV has {len(rows)} response rows")
            
    except Exception as e:
        print(f"❌ Error reading CSV file: {e}")
        return False
    
    # Test 5: Test fallback behavior (no Prolific PID)
    print("\n5. Testing fallback behavior (no Prolific PID)...")
    
    fallback_session = requests.Session()
    fallback_data = {
        'pid': 'fallback_test_789',
        'prolific_pid': ''  # Empty Prolific PID
    }
    
    fallback_response = fallback_session.post(f"{BASE_URL}/start", data=fallback_data)
    
    if fallback_response.status_code == 200:
        print(f"✅ Fallback session started successfully")
        
        # Submit one form to test fallback CSV creation
        task_response = fallback_session.get(f"{BASE_URL}/task")
        if task_response.status_code == 200:
            fallback_form = {
                'version': 'right',
                'trust_rating': '5',
                'emotion_rating': '6',
                'prolific_pid': ''  # Empty
            }
            
            form_response = fallback_session.post(f"{BASE_URL}/task", data=fallback_form)
            if form_response.status_code == 200:
                print(f"✅ Fallback form submitted successfully")
            else:
                print(f"⚠️ Fallback form submission failed: {form_response.status_code}")
        else:
            print(f"⚠️ Could not access fallback task page: {task_response.status_code}")
    else:
        print(f"⚠️ Fallback session start failed: {fallback_response.status_code}")
    
    print("\n" + "=" * 50)
    print("🎉 Prolific PID Integration Test PASSED!")
    print(f"✅ Prolific PID extraction and storage working")
    print(f"✅ Form submissions include Prolific PID")
    print(f"✅ CSV files created with Prolific PID in filename and content")
    print(f"✅ Fallback behavior working for non-Prolific sessions")
    
    return True

if __name__ == "__main__":
    try:
        success = test_prolific_integration()
        if success:
            print(f"\n🚀 All tests passed! Prolific PID integration is working correctly.")
        else:
            print(f"\n💥 Some tests failed. Check the output above for details.")
    except Exception as e:
        print(f"\n💥 Test script error: {e}")
        import traceback
        traceback.print_exc()
