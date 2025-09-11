#!/usr/bin/env python3
import os
import subprocess
import sys
from pathlib import Path

# Ensure we're in the right directory
correct_dir = Path(r'C:\Users\Chris\CascadeProjects\facial-trust-study')
os.chdir(correct_dir)

print(f"🔧 Working directory: {os.getcwd()}")
print("🚀 Force pushing watchdog fix to GitHub...")

def run_git_cmd(cmd):
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, cwd=correct_dir)
        print(f"Command: {cmd}")
        print(f"Return code: {result.returncode}")
        if result.stdout:
            print(f"Output: {result.stdout.strip()}")
        if result.stderr:
            print(f"Error: {result.stderr.strip()}")
        return result.returncode == 0
    except Exception as e:
        print(f"Exception: {e}")
        return False

# Check git status
print("\n=== GIT STATUS ===")
run_git_cmd("git status")

# Add the modified file
print("\n=== ADDING FILES ===")
run_git_cmd("git add dashboard/dashboard_app.py")
run_git_cmd("git add .")

# Commit
print("\n=== COMMITTING ===")
success = run_git_cmd('git commit -m "CRITICAL FIX: Disable watchdog imports to resolve Render ModuleNotFoundError"')

# Push
print("\n=== PUSHING TO GITHUB ===")
if run_git_cmd("git push origin main"):
    print("\n✅ SUCCESS! Watchdog fix pushed to GitHub!")
    print("🔄 Render will auto-deploy in ~5 minutes")
    print("📊 Dashboard: https://facial-trust-study.onrender.com/dashboard/")
else:
    print("\n❌ Push failed. Check git status manually.")

print(f"\nFinal working directory: {os.getcwd()}")
