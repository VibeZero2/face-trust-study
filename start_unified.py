#!/usr/bin/env python3
"""
Unified startup script for both study program and dashboard
Runs both applications simultaneously on different ports
"""
import os
import sys
import threading
import time
from pathlib import Path

def start_study_program():
    """Start the study program on port 3000"""
    print("🔬 Starting Study Program on port 3000...")
    os.system("python app.py")

def start_dashboard():
    """Start the dashboard on port 8080"""
    print("📊 Starting Dashboard on port 8080...")
    # Change to dashboard directory
    os.chdir("dashboard")
    os.system("python dashboard_app.py")

def main():
    """Main function to start both applications"""
    print("🚀 Starting Unified Face Perception Study System...")
    print("=" * 60)
    print("🔬 Study Program will run on: http://localhost:3000")
    print("📊 Dashboard will run on: http://localhost:8080")
    print("=" * 60)
    
    # Start study program in a separate thread
    study_thread = threading.Thread(target=start_study_program, daemon=True)
    study_thread.start()
    
    # Wait a moment for study program to start
    time.sleep(2)
    
    # Start dashboard in main thread
    start_dashboard()

if __name__ == "__main__":
    main()
