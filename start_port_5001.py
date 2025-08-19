#!/usr/bin/env python3
"""
Start the facial trust study on port 5001
"""

import os
import sys

# Set the port environment variable
os.environ['PORT'] = '5001'

# Import and run the app
from app import app

if __name__ == "__main__":
    print("Starting facial trust study on port 5001...")
    app.run(host="0.0.0.0", port=5001, debug=False)
