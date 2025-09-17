#!/usr/bin/env python3
"""
Test the actual browser flow using requests to simulate a complete participant session
"""

import requests
import time
from pathlib import Path

BASE_URL = "http://localhost:3000"
TEST_PID = f"browser_test_{int(time.time())}"

def test_complete_flow():
    print(f"🧪 Testing complete browser flow with participant ID: {TEST_PID}")
    
    # Create a session to maintain cookies
    session = requests.Session()
    
    # Step 1: Start the study
    print("\n1. Starting the study...")
    start_data = {"pid": TEST_PID}
    start_response = session.post(f"{BASE_URL}/start", data=start_data, allow_redirects=False)
    
    if start_response.status_code == 302:  # Redirect to /task
        print("✅ Study start successful (redirected to task)")
    else:
        print(f"❌ Study start failed: {start_response.status_code}")
        return
    
    # Step 2: Get the first task page
    print("\n2. Getting first task page...")
    task_response = session.get(f"{BASE_URL}/task")
    
    if task_response.status_code == 200:
        print("✅ Task page loaded successfully")
        
        # Check if it shows "Face 1 of 35"
        if "Face 1 of" in task_response.text:
            print("✅ Study correctly starts at Face 1")
        else:
            print("❌ Study does not start at Face 1")
            # Look for face number in the response
            import re
            face_match = re.search(r'Face (\d+) of (\d+)', task_response.text)
            if face_match:
                print(f"   Found: Face {face_match.group(1)} of {face_match.group(2)}")
    else:
        print(f"❌ Task page failed: {task_response.status_code}")
        return
    
    # Step 3: Submit first form (toggle version)
    print("\n3. Submitting first form (toggle version)...")
    form_data = {
        'version': 'toggle',
        'trust_left': '7',
        'emotion_left': '3',
        'trust_right': '8',
        'emotion_right': '4',
        'masc_toggle': 'left',
        'fem_toggle': 'right'
    }
    
    submit_response = session.post(f"{BASE_URL}/task", data=form_data, allow_redirects=False)
    
    print(f"   Response status: {submit_response.status_code}")
    print(f"   Response headers: {dict(submit_response.headers)}")
    if submit_response.text:
        print(f"   Response preview: {submit_response.text[:200]}...")
    
    if submit_response.status_code in [200, 302]:
        print("✅ First form submission successful")
    else:
        print(f"❌ First form submission failed: {submit_response.status_code}")
        return
    
    # Step 4: Submit second form (full version)
    print("\n4. Getting second task page and submitting full version...")
    task_response2 = session.get(f"{BASE_URL}/task")
    
    if task_response2.status_code == 200:
        print("✅ Second task page loaded")
        
        # Submit full face form
        form_data2 = {
            'version': 'full',
            'trust_full': '6',
            'emotion_full': '5',
            'masc': 'right',
            'fem': 'left'
        }
        
        submit_response2 = session.post(f"{BASE_URL}/task", data=form_data2, allow_redirects=False)
        
        if submit_response2.status_code in [200, 302]:
            print("✅ Second form submission successful")
        else:
            print(f"❌ Second form submission failed: {submit_response2.status_code}")
            return
    
    # Step 5: Check CSV file creation
    print("\n5. Checking CSV file creation...")
    time.sleep(2)  # Give it time to save
    
    data_dir = Path("data/responses")
    csv_files = list(data_dir.glob(f"*{TEST_PID}*.csv"))
    
    if csv_files:
        print(f"✅ Found {len(csv_files)} CSV files for test participant")
        
        # Check the most recent file
        latest_file = max(csv_files, key=lambda f: f.stat().st_mtime)
        print(f"✅ Latest CSV file: {latest_file.name}")
        
        # Verify content
        with open(latest_file, 'r') as f:
            content = f.read()
            lines = content.strip().split('\n')
            
            print(f"✅ CSV has {len(lines)} lines (including header)")
            
            # Should have 10 data rows for one complete face
            data_rows = len(lines) - 1
            if data_rows == 10:
                print("✅ Correct number of data rows: 10 (one complete face)")
            else:
                print(f"⚠️ Expected 10 data rows, found: {data_rows}")
            
            # Check for version field
            if 'version' in lines[0]:
                print("✅ Version field present in CSV header")
                
                # Count versions
                versions = []
                for line in lines[1:]:  # Skip header
                    if line.strip():
                        parts = line.split(',')
                        if len(parts) >= 3:
                            versions.append(parts[2])  # version is 3rd column
                
                version_counts = {v: versions.count(v) for v in set(versions)}
                print(f"✅ Version distribution: {version_counts}")
                
                expected_versions = {'left', 'right', 'both'}
                found_versions = set(versions)
                if expected_versions.issubset(found_versions):
                    print("✅ All expected versions found")
                else:
                    missing = expected_versions - found_versions
                    print(f"❌ Missing versions: {missing}")
            else:
                print("❌ Version field missing from CSV header")
    else:
        print("❌ No CSV files found for test participant")
    
    print(f"\n🏁 Complete flow test finished for participant {TEST_PID}")

if __name__ == "__main__":
    test_complete_flow()
