"""
Launcher script for the Facial Trust Study application.
This script ensures proper Python path setup before launching the application.
"""
import os
import sys
from pathlib import Path

# Add the project root to the Python path
project_root = str(Path(__file__).resolve().parent)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Add the dashboard directory to the Python path
dashboard_dir = str(Path(__file__).resolve().parent / 'dashboard')
if dashboard_dir not in sys.path:
    sys.path.insert(0, dashboard_dir)

# Now import and run the app
from app import app

if __name__ == '__main__':
    print("\n🚀 Starting Facial Trust Study...")
    print(f"🌐 Access the application at: http://localhost:3000")
    print(f"📊 Access the dashboard at: http://localhost:3000/dashboard")
    print("🛑 Press Ctrl+C to stop the server\n")
    
    # Run the application
    app.run(host='0.0.0.0', port=3000, debug=True)
