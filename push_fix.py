#!/usr/bin/env python3
"""
Simple script to push the watchdog fix to GitHub
"""
import subprocess
import sys

def run_command(cmd):
    """Run a command and return the result"""
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        print(f"Running: {cmd}")
        if result.stdout:
            print(f"Output: {result.stdout}")
        if result.stderr:
            print(f"Error: {result.stderr}")
        return result.returncode == 0
    except Exception as e:
        print(f"Exception running {cmd}: {e}")
        return False

def main():
    """Push the watchdog fix"""
    print("🚀 Pushing watchdog fix to GitHub...")
    
    # Add all files
    if not run_command("git add ."):
        print("❌ Failed to add files")
        return
    
    # Commit changes
    if not run_command('git commit -m "FIX: Make watchdog import optional for Render deployment"'):
        print("❌ Failed to commit (might be no changes)")
    
    # Push to GitHub
    if not run_command("git push origin main"):
        print("❌ Failed to push to GitHub")
        return
    
    print("✅ Watchdog fix pushed successfully!")
    print("🔄 Render should redeploy automatically in 5-10 minutes")
    print("📊 Dashboard will be available at: https://facial-trust-study.onrender.com/dashboard/")

if __name__ == "__main__":
    main()
