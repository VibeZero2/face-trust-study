"""
Dashboard Factory 
This module creates and configures the dashboard blueprint with all its routes.
"""
from flask import Flask
from .dashboard_app import dashboard_bp

def create_dashboard_blueprint():
    """Create and configure the dashboard blueprint."""
    # Import and initialize data
    from .dashboard_app import initialize_data
    initialize_data()
    
    # Return the blueprint from dashboard_app
    return dashboard_bp

def create_dashboard_app():
    """Create a Flask app with the dashboard blueprint."""
    app = Flask(__name__)
    app.secret_key = 'dashboard-secret-key'
    
    # Register the dashboard blueprint
    blueprint = create_dashboard_blueprint()
    app.register_blueprint(blueprint, url_prefix='/dashboard')
    
    return app

if __name__ == '__main__':
    app = create_dashboard_app()
    app.run(host='0.0.0.0', port=3000, debug=True)
