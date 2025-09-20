#!/usr/bin/env python3
"""Start the app in debug mode and log output to run_debug.log"""
import subprocess
import os
cwd = os.path.dirname(__file__)
cmd = ["python", "-u", "app.py"]
env = os.environ.copy()
env["FLASK_ENV"] = "development"
print('Starting app.py in debug mode (FLASK_ENV=development)')
with open('run_debug.log','wb') as out:
    p = subprocess.Popen(cmd, cwd=cwd, env=env, stdout=out, stderr=subprocess.STDOUT)
    print(f'Launched PID: {p.pid}, logging to run_debug.log')

