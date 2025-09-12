"""
Dashboard routes for the Facial Trust Study
"""
from flask import Blueprint, render_template, request, jsonify, redirect, url_for, session, flash, send_file
from functools import wraps
import os
import json
import pandas as pd
from pathlib import Path
from datetime import datetime
import tempfile
import zipfile
import io
from .analysis.cleaning import DataCleaner
from .analysis.stats import StatisticalAnalyzer
from .analysis.filters import DataFilter
from . import config

# Create a blueprint for dashboard routes
dashboard_bp = Blueprint('dashboard', __name__,
                       template_folder='templates',
                       static_folder='static')

# Initialize data processing components
data_cleaner = None
statistical_analyzer = None
data_filter = None
last_data_refresh = None
data_files_hash = None

# Dashboard settings
show_incomplete_in_production = True

# Import and register all routes from dashboard_app
from .dashboard_app import *

# Update all route decorators to use the blueprint
# This is a simplified example - in a real implementation, you'd move the route functions here
# and update their decorators to use @dashboard_bp.route()

def is_data_available():
    """Check if data is available and initialized."""
    return data_cleaner is not None and statistical_analyzer is not None

# Example of how to convert a route:
@dashboard_bp.route('/')
def dashboard():
    """Main dashboard page."""
    if 'user_id' not in session:
        return redirect(url_for('dashboard.login'))
    
    # Rest of the dashboard function...
    return render_template('dashboard.html', 
                         show_incomplete=show_incomplete_in_production)

# Add other routes here...

# This would be repeated for all routes in dashboard_app.py
# In a production environment, you'd want to properly refactor the routes into this file
