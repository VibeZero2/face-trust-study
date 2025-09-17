#!/usr/bin/env python3
"""
Start dashboard on port 3000
"""

import sys
import os
sys.path.append('.')
sys.path.append('dashboard')

from dashboard.dashboard_factory import create_dashboard_app

if __name__ == "__main__":
    app = create_dashboard_app()
    print("Starting dashboard on port 3000...")
    print("Access at: http://localhost:3000/dashboard/")
    app.run(host='0.0.0.0', port=3000, debug=True)
