#!/usr/bin/env python3
"""
Debug script to test session initialization and verify Face 1 start behavior
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import create_participant_run, FACE_FILES
import random

def test_session_creation():
    print("🧪 Testing session creation and face ordering...")
    
    # Test multiple session creations to verify consistency
    for i in range(3):
        print(f"\n--- Test {i+1} ---")
        
        # Set a fixed seed for reproducible testing
        random.seed(42 + i)
        
        # Mock session object
        class MockSession:
            def __init__(self):
                self.data = {}
                
            def clear(self):
                self.data.clear()
                print("🔄 Session cleared")
                
            def __setitem__(self, key, value):
                self.data[key] = value
                
            def __getitem__(self, key):
                return self.data[key]
                
            def get(self, key, default=None):
                return self.data.get(key, default)
        
        # Create mock session
        session = MockSession()
        
        # Monkey patch the global session for testing
        import app
        original_session = app.session
        app.session = session
        
        try:
            # Test participant creation
            test_pid = f"test_participant_{i+1}"
            create_participant_run(test_pid)
            
            print(f"✅ Created participant: {test_pid}")
            print(f"📊 Session index: {session['index']}")
            print(f"📊 Sequence length: {len(session['sequence'])}")
            print(f"📊 Face order length: {len(session['face_order'])}")
            print(f"📊 Total FACE_FILES: {len(FACE_FILES)}")
            
            # Check first face
            if session['sequence']:
                first_face = session['sequence'][0]
                print(f"🎯 First face ID: {first_face['face_id']}")
                print(f"🎯 First face order: {first_face['order']}")
                
            # Verify index starts at 0
            if session['index'] == 0:
                print("✅ Session index correctly starts at 0")
            else:
                print(f"❌ Session index starts at {session['index']} instead of 0")
                
        finally:
            # Restore original session
            app.session = original_session

def test_face_calculation():
    print("\n🧪 Testing face number calculation...")
    
    # Test the face calculation logic
    for index in range(10):  # Test first 10 indices
        face_index = index // 2
        image_index = index % 2
        progress = face_index + 1
        
        print(f"Index {index}: Face {progress}, Image {image_index}")
        
        if index == 0:
            if progress == 1:
                print("✅ Index 0 correctly shows Face 1")
            else:
                print(f"❌ Index 0 shows Face {progress} instead of Face 1")

if __name__ == "__main__":
    test_session_creation()
    test_face_calculation()
