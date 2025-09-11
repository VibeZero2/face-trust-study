import os
import subprocess
import sys

# Change to the correct directory
os.chdir(r'C:\Users\Chris\CascadeProjects\facial-trust-study')

# Run git commands
try:
    subprocess.run(['git', 'add', '.'], check=True, shell=True)
    subprocess.run(['git', 'commit', '-m', 'FIX: Disable watchdog to resolve Render ModuleNotFoundError'], check=True, shell=True)
    subprocess.run(['git', 'push', 'origin', 'main'], check=True, shell=True)
    print("✅ SUCCESS: Watchdog fix pushed to GitHub!")
    print("🚀 Render will auto-deploy in ~5 minutes")
    print("📊 Dashboard: https://facial-trust-study.onrender.com/dashboard/")
except subprocess.CalledProcessError as e:
    print(f"❌ Git command failed: {e}")
except Exception as e:
    print(f"❌ Error: {e}")
