#!/usr/bin/env python3
import subprocess
import os

# Change to the correct directory
os.chdir(r'C:\Users\Chris\CascadeProjects\facial-trust-study')

def run_git_command(cmd):
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        print(f"Running: {cmd}")
        print(f"Output: {result.stdout}")
        if result.stderr:
            print(f"Error: {result.stderr}")
        return result.returncode == 0
    except Exception as e:
        print(f"Exception: {e}")
        return False

print("🔧 DEPLOYING NAVIGATION FIX...")

# Add the template file
run_git_command("git add dashboard/templates/base.html")

# Commit changes
run_git_command('git commit -m "HARDCODE NAVIGATION PATHS - FINAL FIX"')

# Push to GitHub
if run_git_command("git push origin main"):
    print("✅ NAVIGATION FIX DEPLOYED!")
    print("🔄 Render will deploy in ~3 minutes")
    print("📊 All menu links will work after deployment")
else:
    print("❌ Push failed")

print("Done.")
