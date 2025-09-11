#!/usr/bin/env python3
"""
WSGI application for unified deployment on Render
Serves both study program and dashboard from single process
"""
import os
import sys
from pathlib import Path
from werkzeug.middleware.dispatcher import DispatcherMiddleware
from werkzeug.serving import run_simple

# Add current directory to Python path
current_dir = Path(__file__).resolve().parent
sys.path.insert(0, str(current_dir))
sys.path.insert(0, str(current_dir / 'dashboard'))

# Import both applications
from app import app as study_app
from dashboard.dashboard_app import app as dashboard_app

# Create the combined WSGI application
# Study program on main domain, dashboard on /dashboard path
application = DispatcherMiddleware(study_app, {
    '/dashboard': dashboard_app
})

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
