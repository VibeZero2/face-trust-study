#!/usr/bin/env python3
import os
import sys
from pathlib import Path

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

try:
    from waitress import serve
    import app
    
    PORT = int(os.environ.get("PORT", 3000))
    
    print("🎯 Starting Facial Trust Study with Waitress WSGI Server")
    print(f"📍 URL: http://localhost:{PORT}")
    print("🔧 Using Waitress for better Windows compatibility")
    print("=" * 50)
    
    # Serve the Flask app using waitress
    serve(app.app, host="127.0.0.1", port=PORT)
    
except ImportError:
    print("❌ Waitress not installed. Installing...")
    os.system(f"{sys.executable} -m pip install waitress")
    print("✅ Waitress installed. Please run this script again.")
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
