#!/usr/bin/env python3
"""
Test direct POST submission to isolate the issue
"""

import requests
import time

BASE_URL = "http://localhost:3000"
TEST_PID = f"direct_test_{int(time.time())}"

def test_direct_post():
    print(f"🧪 Testing direct POST submission with participant ID: {TEST_PID}")
    
    # Step 1: Start session and get cookies
    print("\n1. Starting session...")
    session = requests.Session()
    
    # Start the study
    start_data = {"pid": TEST_PID}
    start_response = session.post(f"{BASE_URL}/start", data=start_data)
    print(f"Start response status: {start_response.status_code}")
    print(f"Cookies after start: {session.cookies}")
    
    # Step 2: Get task page to establish session
    print("\n2. Getting task page...")
    task_get = session.get(f"{BASE_URL}/task")
    print(f"Task GET status: {task_get.status_code}")
    
    if "Face 1 of" in task_get.text:
        print("✅ Session established - showing Face 1")
    else:
        print("❌ Session not established properly")
        return
    
    # Step 3: Submit form with detailed logging
    print("\n3. Submitting form with detailed logging...")
    
    form_data = {
        'version': 'toggle',
        'trust_left': '7',
        'emotion_left': '3',
        'trust_right': '8',
        'emotion_right': '4',
        'masc_toggle': 'left',
        'fem_toggle': 'right'
    }
    
    print(f"Form data: {form_data}")
    print(f"Cookies before POST: {session.cookies}")
    
    # Make POST request
    post_response = session.post(f"{BASE_URL}/task", data=form_data)
    
    print(f"POST response status: {post_response.status_code}")
    print(f"POST response headers: {dict(post_response.headers)}")
    
    # Check if response contains task page or redirect
    if "Face" in post_response.text and "of" in post_response.text:
        import re
        face_match = re.search(r'Face (\d+) of (\d+)', post_response.text)
        if face_match:
            print(f"Response shows: Face {face_match.group(1)} of {face_match.group(2)}")
    
    # Step 4: Check for CSV files
    print("\n4. Checking for CSV files...")
    time.sleep(1)
    
    from pathlib import Path
    data_dir = Path("data/responses")
    csv_files = list(data_dir.glob(f"*{TEST_PID}*.csv"))
    
    if csv_files:
        print(f"✅ Found CSV files: {[f.name for f in csv_files]}")
    else:
        print("❌ No CSV files found")
        
        # List all CSV files to see what exists
        all_csv = list(data_dir.glob("*.csv"))
        print(f"All CSV files in directory: {[f.name for f in all_csv]}")

if __name__ == "__main__":
    test_direct_post()
