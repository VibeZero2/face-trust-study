#!/usr/bin/env python3
import subprocess
import os

# Change to correct directory
os.chdir(r'C:\Users\Chris\CascadeProjects\facial-trust-study')

def run_cmd(cmd):
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, cwd=os.getcwd())
        print(f"Command: {cmd}")
        print(f"Return code: {result.returncode}")
        if result.stdout:
            print(f"Output: {result.stdout}")
        if result.stderr:
            print(f"Error: {result.stderr}")
        return result.returncode == 0
    except Exception as e:
        print(f"Exception: {e}")
        return False

print("🔧 Fixing navigation issues...")
print(f"Working directory: {os.getcwd()}")

# Add and commit changes
run_cmd("git add dashboard/templates/base.html")
run_cmd('git commit -m "FIX: Update menu navigation links and fix Overview routing"')
run_cmd("git push origin main")

print("✅ Navigation fixes pushed to GitHub!")
print("🔄 Render will auto-deploy in ~5 minutes")
print("📊 Dashboard: https://facial-trust-study.onrender.com/dashboard/")
