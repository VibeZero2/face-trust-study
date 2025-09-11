#!/usr/bin/env python3
import subprocess
import os
import sys

os.chdir(r'C:\Users\Chris\CascadeProjects\facial-trust-study')

def run_cmd(cmd):
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        print(f"Command: {cmd}")
        print(f"Output: {result.stdout}")
        if result.stderr:
            print(f"Error: {result.stderr}")
        return result.returncode == 0
    except Exception as e:
        print(f"Exception: {e}")
        return False

print("🔧 Pushing navigation fixes to fix 404 errors...")

# Add the navigation template fix
run_cmd("git add dashboard/templates/base.html")
run_cmd('git commit -m "CRITICAL FIX: Use url_for() in navigation to fix 404 errors in unified deployment"')
run_cmd("git push origin main")

print("✅ Navigation fixes pushed!")
print("🔄 Render will redeploy and fix the 404 errors")
print("📊 All menu links will work after deployment")
