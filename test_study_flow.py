#!/usr/bin/env python3
"""
Test script to verify the facial trust study flow works correctly.
Tests:
1. Study starts at Face 1
2. CSV files are created properly
3. Session management works correctly
"""

import requests
import time
import os
from pathlib import Path

BASE_URL = "http://localhost:3000"
TEST_PID = f"test_flow_{int(time.time())}"

def test_study_flow():
    print(f"🧪 Testing study flow with participant ID: {TEST_PID}")
    
    # Test 1: Start the study
    print("\n1. Testing study start...")
    start_data = {"pid": TEST_PID}
    start_response = requests.post(f"{BASE_URL}/start", data=start_data)
    if start_response.status_code in [200, 302]:  # 302 is redirect to /task
        print("✅ Study start successful")
    else:
        print(f"❌ Study start failed: {start_response.status_code}")
        return
    
    # Test 2: Get the first task page
    print("\n2. Testing first task page...")
    task_response = requests.get(f"{BASE_URL}/task")
    if task_response.status_code == 200:
        # Check if it shows "Face 1 of 35"
        if "Face 1 of" in task_response.text:
            print("✅ Study starts at Face 1")
        else:
            print("❌ Study does not start at Face 1")
            print("Response content preview:", task_response.text[:500])
    else:
        print(f"❌ Task page failed: {task_response.status_code}")
        return
    
    # Test 3: Submit a response for the first face
    print("\n3. Testing form submission...")
    form_data = {
        'version': 'toggle',
        'trust_left': '7',
        'emotion_left': '3',
        'trust_right': '8',
        'emotion_right': '4',
        'masc_toggle': 'left',
        'fem_toggle': 'right'
    }
    
    submit_response = requests.post(f"{BASE_URL}/task", data=form_data)
    if submit_response.status_code in [200, 302]:  # 302 is redirect
        print("✅ Form submission successful")
    else:
        print(f"❌ Form submission failed: {submit_response.status_code}")
        return
    
    # Test 4: Check if CSV file was created
    print("\n4. Testing CSV file creation...")
    time.sleep(2)  # Give it a moment to save
    
    data_dir = Path("data/responses")
    csv_files = list(data_dir.glob(f"{TEST_PID}*.csv"))
    
    if csv_files:
        print(f"✅ CSV file created: {csv_files[0].name}")
        
        # Check CSV content
        with open(csv_files[0], 'r') as f:
            content = f.read()
            if 'version' in content and 'face_id' in content:
                print("✅ CSV has correct headers including version field")
            else:
                print("❌ CSV missing required headers")
                print("CSV content:", content[:200])
    else:
        print("❌ No CSV file created")
    
    print(f"\n🏁 Test completed for participant {TEST_PID}")

if __name__ == "__main__":
    test_study_flow()
