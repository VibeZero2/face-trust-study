"""
Dashboard package initialization.
This file makes the dashboard directory a Python package.
"""
from .dashboard_factory import create_dashboard_blueprint

# For backward compatibility
dashboard_blueprint = create_dashboard_blueprint()

__all__ = ['dashboard_blueprint', 'create_dashboard_blueprint']
