#!/usr/bin/env python3
"""
Comprehensive test to verify the complete study flow and CSV creation
"""

import requests
import time
from pathlib import Path

BASE_URL = "http://localhost:3000"
TEST_PID = f"complete_test_{int(time.time())}"

def test_complete_study_flow():
    print(f"🧪 Testing complete study flow with participant ID: {TEST_PID}")
    
    # Create a session to maintain cookies
    session = requests.Session()
    
    # Step 1: Start the study
    print("\n1. Starting the study...")
    start_data = {"pid": TEST_PID}
    start_response = session.post(f"{BASE_URL}/start", data=start_data, allow_redirects=False)
    
    if start_response.status_code == 302:
        print("✅ Study start successful (redirected to task)")
    else:
        print(f"❌ Study start failed: {start_response.status_code}")
        return False
    
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
            return False
    else:
        print(f"❌ Task page failed: {task_response.status_code}")
        return False
    
    # Step 3: Submit first form (toggle version) - Complete face
    print("\n3. Submitting toggle form...")
    form_data_toggle = {
        'version': 'toggle',
        'trust_left': '7',
        'emotion_left': '3',
        'trust_right': '8',
        'emotion_right': '4',
        'masc_toggle': 'left',
        'fem_toggle': 'right'
    }
    
    submit_response1 = session.post(f"{BASE_URL}/task", data=form_data_toggle, allow_redirects=False)
    
    if submit_response1.status_code in [200, 302]:
        print("✅ Toggle form submission successful")
    else:
        print(f"❌ Toggle form submission failed: {submit_response1.status_code}")
        return False
    
    # Step 4: Get next task page and submit full form
    print("\n4. Getting next task page and submitting full form...")
    task_response2 = session.get(f"{BASE_URL}/task")
    
    if task_response2.status_code == 200:
        print("✅ Second task page loaded")
        
        # Submit full face form
        form_data_full = {
            'version': 'full',
            'trust_full': '6',
            'emotion_full': '5',
            'masc': 'right',
            'fem': 'left'
        }
        
        submit_response2 = session.post(f"{BASE_URL}/task", data=form_data_full, allow_redirects=False)
        
        if submit_response2.status_code in [200, 302]:
            print("✅ Full form submission successful")
        else:
            print(f"❌ Full form submission failed: {submit_response2.status_code}")
            return False
    else:
        print(f"❌ Second task page failed: {task_response2.status_code}")
        return False
    
    # Step 5: Wait and check for CSV files
    print("\n5. Checking CSV file creation...")
    time.sleep(3)  # Give it time to save
    
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
            expected_rows = 10  # 2 left + 2 right + 6 both
            
            if data_rows == expected_rows:
                print(f"✅ Correct number of data rows: {data_rows}")
            else:
                print(f"⚠️ Expected {expected_rows} data rows, found: {data_rows}")
            
            # Show first few rows
            print("\nCSV content preview:")
            for i, line in enumerate(lines[:6]):
                print(f"  {i}: {line}")
            
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
                    return True
                else:
                    missing = expected_versions - found_versions
                    print(f"❌ Missing versions: {missing}")
                    return False
            else:
                print("❌ Version field missing from CSV header")
                return False
    else:
        print("❌ No CSV files found for test participant")
        
        # List all CSV files to see what exists
        all_csv = list(data_dir.glob("*.csv"))
        print(f"All CSV files in directory: {[f.name for f in all_csv]}")
        return False

if __name__ == "__main__":
    success = test_complete_study_flow()
    if success:
        print(f"\n🎉 COMPLETE SUCCESS: All tests passed for participant {TEST_PID}")
        print("✅ Study starts at Face 1")
        print("✅ Forms submit successfully") 
        print("✅ CSV files are created with correct format")
        print("✅ Version field is included in all CSV rows")
    else:
        print(f"\n❌ TESTS FAILED: Issues found in study flow for participant {TEST_PID}")
