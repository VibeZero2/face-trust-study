#!/usr/bin/env python3
import os
os.environ['PORT'] = '5001'

print("Starting test...")
try:
    import app
    print("✅ App imported successfully")
    print(f"✅ Flask app object: {app.app}")
    print("✅ Starting on port 5001...")
    app.app.run(host='0.0.0.0', port=5001, debug=False)
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
