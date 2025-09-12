"""
Facial Trust Study - Main Application Launcher

This script initializes and runs the Facial Trust Study web application.
"""
import os
import sys
from pathlib import Path

def setup_environment():
    """Set up the Python environment and paths."""
    # Add project root to Python path
    project_root = str(Path(__file__).resolve().parent)
    if project_root not in sys.path:
        sys.path.insert(0, project_root)
    
    # Generate a proper Fernet key if not set
    from cryptography.fernet import Fernet
    default_fernet_key = Fernet.generate_key().decode()
    
    # Set environment variables
    os.environ.update({
        'FLASK_APP': 'app.py',
        'FLASK_ENV': 'development',
        'FLASK_DEBUG': '1',
        'FLASK_SECRET_KEY': os.getenv('FLASK_SECRET_KEY', 'dev-secret-key-change-in-production'),
        'DASHBOARD_SECRET_KEY': os.getenv('DASHBOARD_SECRET_KEY', 'dashboard-dev-secret-key'),
        'FERNET_KEY': os.getenv('FERNET_KEY', default_fernet_key)
    })
    
    # Create necessary directories
    data_dir = Path(project_root) / "data"
    responses_dir = data_dir / "responses"
    responses_dir.mkdir(parents=True, exist_ok=True)
    
    # Create images directory if it doesn't exist
    (Path(project_root) / "static" / "images").mkdir(parents=True, exist_ok=True)

def main():
    """Main entry point for the application."""
    try:
        setup_environment()
        
        print("\n🚀 Starting Facial Trust Study...")
        print("🌐 Application will be available at: http://localhost:3000")
        print("📊 Dashboard will be available at: http://localhost:3000/dashboard")
        print("🛑 Press Ctrl+C to stop the server\n")
        
        # Import and run the Flask app
        from app import app
        
        # Enable debug mode
        app.debug = True
        
        # Run the application
        app.run(host='0.0.0.0', port=3000, debug=True, use_reloader=True)
        
    except Exception as e:
        print(f"\n❌ Error starting the application: {str(e)}")
        print("\nPlease make sure all dependencies are installed by running:")
        print("pip install -r requirements.txt")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
