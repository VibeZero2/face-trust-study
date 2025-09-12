#!/usr/bin/env python3
"""
WSGI application for unified deployment on Render
Serves both study program and dashboard from single Flask app
"""
import os
import sys
from pathlib import Path
from werkzeug.serving import run_simple

# Add current directory to Python path
current_dir = Path(__file__).resolve().parent
sys.path.insert(0, str(current_dir))

# Import the main application (which already has dashboard blueprint registered)
from app import app

# Use the single Flask app instead of DispatcherMiddleware
application = app

if __name__ == "__main__":
    # For local development
    print("🚀 Starting Unified Face Perception Study System...")
    print("=" * 60)
    print("🔬 Study Program: http://localhost:3000")
    print("📊 Dashboard: http://localhost:3000/dashboard")
    print("=" * 60)
    
    # Use Render's PORT if available, otherwise 3000
    port = int(os.environ.get('PORT', 3000))
    
    run_simple('0.0.0.0', port, application, 
               use_reloader=True, 
               use_debugger=True,
               threaded=True)
