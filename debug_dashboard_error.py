#!/usr/bin/env python3
"""
Debug script to capture the exact dashboard error with full stack trace
"""

import sys
import os
import traceback
sys.path.append('.')
sys.path.append('dashboard')

def debug_dashboard():
    try:
        print("🔍 Starting dashboard debug...")
        
        # Import dashboard components
        from dashboard.dashboard_factory import create_dashboard_app
        
        print("✅ Dashboard factory imported successfully")
        
        # Create the app
        app = create_dashboard_app()
        print("✅ Dashboard app created successfully")
        
        # Test the main dashboard route
        with app.test_client() as client:
            print("🔍 Testing main dashboard route...")
            response = client.get('/')
            
            print(f"Response status: {response.status_code}")
            
            if response.status_code != 200:
                print("❌ Dashboard route failed")
                print(f"Response data: {response.data.decode()}")
            else:
                print("✅ Dashboard route works!")
                
    except Exception as e:
        print(f"❌ ERROR: {e}")
        print("\n🔍 FULL STACK TRACE:")
        traceback.print_exc()
        
        # Try to get more specific error info
        print(f"\n🔍 Error type: {type(e)}")
        print(f"🔍 Error args: {e.args}")

if __name__ == "__main__":
    debug_dashboard()
