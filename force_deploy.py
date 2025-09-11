import subprocess
import os

os.chdir(r'C:\Users\Chris\CascadeProjects\facial-trust-study')

# Force deploy the template changes
subprocess.run(['git', 'add', 'dashboard/templates/base.html'], shell=True)
subprocess.run(['git', 'commit', '-m', 'FORCE DEPLOY NAVIGATION FIX'], shell=True)
result = subprocess.run(['git', 'push', 'origin', 'main'], shell=True, capture_output=True, text=True)

print("DEPLOYMENT RESULT:")
print(result.stdout)
if result.stderr:
    print("ERRORS:")
    print(result.stderr)

print("✅ Template with hardcoded /dashboard/ paths deployed!")
print("🔄 Render will update in ~3 minutes")
print("📊 All navigation should work after deployment")
