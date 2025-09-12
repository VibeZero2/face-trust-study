"""
Dashboard Factory
This module creates and configures the dashboard blueprint with all its routes.
"""
from .dashboard_app import dashboard_bp

def create_dashboard_blueprint():
    """Create and configure the dashboard blueprint."""
    # Import and initialize data
    from .dashboard_app import initialize_data
    initialize_data()
    
    # Return the blueprint from dashboard_app
    return dashboard_bp
