"""
Configuration for Face Viewer Dashboard
"""
import os
from pathlib import Path

# Base directory
BASE_DIR = Path(__file__).resolve().parent

# Data directory configuration
# Dashboard reads from its own data directory which contains both test and production files
DATA_DIR = BASE_DIR / "data" / "responses"

# Study program data directory (for reference)
STUDY_PROGRAM_DATA_DIR = BASE_DIR.parent / "facial-trust-study" / "data" / "responses"

# Ensure data directory exists
DATA_DIR.mkdir(parents=True, exist_ok=True)

# Dashboard configuration
DASHBOARD_CONFIG = {
    'host': '0.0.0.0',
    'port': 5000,
    'debug': True,
    'secret_key': os.getenv('DASHBOARD_SECRET_KEY', 'dev-secret-key-change-in-production'),
    'live_monitoring': True,  # Enable live file monitoring
    'auto_refresh_interval': 30,  # seconds
}

# Study program configuration
STUDY_PROGRAM_CONFIG = {
    'host': '0.0.0.0',
    'port': 5001,  # Different port to avoid conflicts
    'debug': False,
    'data_dir': str(STUDY_PROGRAM_DATA_DIR),
}

# Data processing configuration
DATA_CONFIG = {
    'test_mode': True,  # Set to True to include test files
    'file_patterns': [
        'participant_*.csv',  # Old format files
        '*_2025*.csv',        # Study program timestamped files
        'PROLIFIC_*.csv',     # Prolific files
        'test789*.csv',       # Test files
    ],
    'exclude_patterns': [
        'test_participant*.csv',  # Exclude test files in production
    ]
}

# Authentication configuration
AUTH_CONFIG = {
    'users_file': BASE_DIR / 'users.json',
    'session_timeout': 3600,  # 1 hour
}

# Logging configuration
LOGGING_CONFIG = {
    'level': 'INFO',
    'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    'file': BASE_DIR / 'logs' / 'dashboard.log',
}

# Create logs directory
LOGGING_CONFIG['file'].parent.mkdir(exist_ok=True)
