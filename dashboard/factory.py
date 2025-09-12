from flask import Flask
from .dashboard_app import dashboard_bp

def create_dashboard_app():
    """Create and configure the dashboard Flask application."""
    app = Flask(__name__)
    
    # Configuration
    app.config.update(
        SECRET_KEY='dev-secret-key-change-in-production',
        DEBUG=True,
        TEMPLATES_AUTO_RELOAD=True
    )
    
    # Register blueprints
    app.register_blueprint(dashboard_bp, url_prefix='/dashboard')
    
    return app
