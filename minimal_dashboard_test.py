#!/usr/bin/env python3
"""
Minimal test to isolate the exact dashboard error
"""

import sys
import os
import traceback
sys.path.append('.')
sys.path.append('dashboard')

# Test each component step by step
def test_step_by_step():
    try:
        print("Step 1: Import dashboard factory...")
        from dashboard.dashboard_factory import create_dashboard_app
        print("✅ Import successful")
        
        print("Step 2: Create app...")
        app = create_dashboard_app()
        print("✅ App creation successful")
        
        print("Step 3: Test request context...")
        with app.app_context():
            print("✅ App context works")
            
            print("Step 4: Test main route...")
            with app.test_request_context('/'):
                try:
                    from dashboard.dashboard_app import dashboard_bp
                    print("✅ Blueprint import works")
                    
                    # Try to trigger the dashboard view function directly
                    from dashboard.dashboard_app import dashboard
                    result = dashboard()
                    print("✅ Dashboard function executed successfully")
                    
                except Exception as e:
                    print(f"❌ Dashboard function failed: {e}")
                    traceback.print_exc()
                    
    except Exception as e:
        print(f"❌ Error at step: {e}")
        traceback.print_exc()

if __name__ == "__main__":
    test_step_by_step()
