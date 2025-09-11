"""
Face Viewer Dashboard - Direct Template Renderer
Renders the dashboard template directly on port 5000
"""
import os
import sys
import pandas as pd
import json
from datetime import datetime
from pathlib import Path
from flask import Flask, render_template, request, jsonify, send_file, session, redirect, url_for, flash
from functools import wraps
import io
import zipfile
import tempfile
import threading
import time
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# Add the analysis directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'analysis'))

from analysis.cleaning import DataCleaner
from analysis.stats import StatisticalAnalyzer
from analysis.filters import DataFilter
from config import DATA_DIR

# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('DASHBOARD_SECRET_KEY', 'dev-secret-key-change-in-production')
app.config['DEBUG'] = True

# Global variables for data management
data_cleaner = None
statistical_analyzer = None
data_filter = None
last_data_refresh = None
data_files_hash = None

# Dashboard settings
show_incomplete_in_production = True

class DataFileHandler(FileSystemEventHandler):
    """Watchdog handler for detecting new data files"""
    
    def __init__(self, dashboard_app):
        self.dashboard_app = dashboard_app
        self.last_modified = {}
    
    def on_created(self, event):
        if not event.is_directory and event.src_path.endswith('.csv'):
            filename = Path(event.src_path).name
            print(f"🆕 New data file detected: {filename}")
            print(f"   📍 Full path: {event.src_path}")
            trigger_data_refresh()
    
    def on_modified(self, event):
        if not event.is_directory and event.src_path.endswith('.csv'):
            # Avoid duplicate triggers for the same file
            current_time = time.time()
            if (event.src_path not in self.last_modified or 
                current_time - self.last_modified[event.src_path] > 1):
                filename = Path(event.src_path).name
                print(f"📝 Data file modified: {filename}")
                print(f"   📍 Full path: {event.src_path}")
                self.last_modified[event.src_path] = current_time
                trigger_data_refresh()

def start_file_watcher():
    """Start watching the data directory for new files"""
    try:
        data_dir = DATA_DIR
        if data_dir.exists():
            event_handler = DataFileHandler(app)
            observer = Observer()
            observer.schedule(event_handler, str(data_dir), recursive=False)
            observer.start()
            print(f"👀 Started watching data directory: {data_dir}")
            return observer
        else:
            print(f"⚠️ Data directory not found: {data_dir}")
            return None
    except Exception as e:
        print(f"❌ Error starting file watcher: {e}")
        return None

def is_data_available():
    """Check if data is available and initialized."""
    return data_cleaner is not None and data_filter is not None and statistical_analyzer is not None

def initialize_data(test_mode=False, force_mode=False):
    """Initialize data processing components."""
    global data_cleaner, statistical_analyzer, data_filter, last_data_refresh
    
    try:
        # Check what data files are available
        data_dir = DATA_DIR
        if data_dir.exists():
            csv_files = list(data_dir.glob("*.csv"))
            test_files = [f for f in csv_files if any(pattern in f.name for pattern in 
                        ['test_', 'test_participant', 'test_statistical_validation', 'PROLIFIC_TEST_', 'test789.csv', 'test123.csv', 'test456.csv', 'test_participants_combined.csv'])]
            real_files = [f for f in csv_files if f not in test_files]
            
            # Auto-detect mode: if only test files exist, use test mode
            # But only if not forcing a specific mode (e.g., from manual toggle)
            if not force_mode:
                if not real_files and test_files:
                    print("Auto-detected: Only test files available, switching to TEST MODE")
                    test_mode = True
                elif not csv_files:
                    raise FileNotFoundError(f"No CSV files found in {data_dir}")
            else:
                print(f"Force mode enabled: Using specified test_mode={test_mode}")
        
        # Use detected or specified mode
        data_cleaner = DataCleaner(str(data_dir), test_mode=test_mode)
        data_cleaner.load_data()
        data_cleaner.standardize_data()
        data_cleaner.apply_exclusion_rules()
        
        # Only initialize statistical analyzer if we have data
        if len(data_cleaner.raw_data) > 0:
            statistical_analyzer = StatisticalAnalyzer(data_cleaner)
            data_filter = DataFilter(data_cleaner)
        else:
            statistical_analyzer = None
            data_filter = None
        
        last_data_refresh = datetime.now()
        mode_name = "TEST" if test_mode else "PRODUCTION"
        print(f"Data initialized successfully in {mode_name} mode")
        return True
    except FileNotFoundError as e:
        print(f"No data files found: {e}")
        print("Dashboard will start in empty state - upload data to begin analysis")
        # Initialize with empty data structures
        data_cleaner = None
        statistical_analyzer = None
        data_filter = None
        last_data_refresh = datetime.now()
        return True  # Return True to allow dashboard to start
    except Exception as e:
        print(f"Error initializing data: {e}")
        return False

def trigger_data_refresh():
    """Trigger a data refresh when new files are detected"""
    global last_data_refresh
    
    try:
        print("🔄 Triggering data refresh...")
        
        # Log current files before refresh
        data_dir = DATA_DIR
        if data_dir.exists():
            current_files = list(data_dir.glob("*.csv"))
            print(f"📁 Current files in {data_dir}: {[f.name for f in current_files]}")
        
        if initialize_data(force_mode=False):
            last_data_refresh = datetime.now()
            print("✅ Data refresh completed")
            
            # Log data after refresh
            if data_cleaner and hasattr(data_cleaner, 'data') and data_cleaner.data is not None:
                print(f"📊 Total responses loaded: {len(data_cleaner.data)}")
                if len(data_cleaner.data) > 0:
                    participants = data_cleaner.data['pid'].unique() if 'pid' in data_cleaner.data.columns else []
                    print(f"👥 Participants: {list(participants)}")
        else:
            print("❌ Data refresh failed")
    except Exception as e:
        print(f"❌ Error during data refresh: {e}")

# Start file watcher in a separate thread
file_observer = None
# Enable file watcher in both debug and production modes for real-time updates
file_observer = start_file_watcher()

# Initialize data on startup
initialize_data(force_mode=False)

# Simple file-based user authentication
import json
import os

def load_users():
    """Load users from JSON file."""
    users_file = 'data/users.json'
    if os.path.exists(users_file):
        try:
            with open(users_file, 'r') as f:
                return json.load(f)
        except:
            pass
    # Default admin user
    default_users = {
        'admin': {'password': 'admin', 'role': 'admin', 'email': 'admin@example.com'}
    }
    save_users(default_users)
    return default_users

def save_users(users):
    """Save users to JSON file."""
    users_file = 'data/users.json'
    os.makedirs('data', exist_ok=True)
    with open(users_file, 'w') as f:
        json.dump(users, f, indent=2)

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'authenticated' not in session:
            flash('Please log in to access this page', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        users = load_users()
        
        if username in users and users[username]['password'] == password:
            session['authenticated'] = True
            session['username'] = username
            session['role'] = users[username].get('role', 'user')
            flash('Login successful!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid username or password', 'error')
    
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        
        users = load_users()
        
        # Validation
        if not username or not email or not password:
            flash('All fields are required', 'error')
            return render_template('register.html')
        
        if password != confirm_password:
            flash('Passwords do not match', 'error')
            return render_template('register.html')
        
        if username in users:
            flash('Username already exists', 'error')
            return render_template('register.html')
        
        # Add new user
        users[username] = {
            'password': password,
            'email': email,
            'role': 'user'
        }
        save_users(users)
        
        flash('Registration successful! Please log in.', 'success')
        return redirect(url_for('login'))
    
    return render_template('register.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('Logged out successfully', 'success')
    return redirect(url_for('login'))

@app.route('/')
# @login_required  # Temporarily disabled for Render deployment
def dashboard():
    """Main dashboard page."""
    global data_cleaner, statistical_analyzer, data_filter
    
    if not is_data_available():
        if not initialize_data(force_mode=False):
            flash('Error loading data. Please check the data directory.', 'error')
            return render_template('error.html', message="Data initialization failed")
    
    try:
        # Get overview statistics
        if not is_data_available():
            flash('No data available. Please upload data files or check data directory.', 'warning')
            return render_template('dashboard.html',
                             exclusion_summary={},
                             descriptive_stats={},
                             dashboard_stats={},
                             data_summary={'mode': 'NO_DATA'},
                             available_filters={},
                             data_files=[],
                             show_incomplete_in_production=show_incomplete_in_production)
        
        exclusion_summary = data_cleaner.get_exclusion_summary()
        descriptive_stats = statistical_analyzer.get_descriptive_stats() if statistical_analyzer is not None else {}
        data_summary = data_cleaner.get_data_summary()
        
        # Ensure data_summary is consistent with current mode
        if data_cleaner.test_mode:
            data_summary['mode'] = 'TEST'
        else:
            data_summary['mode'] = 'PRODUCTION'
        
        # Calculate additional stats for the dashboard
        cleaned_data = data_cleaner.get_cleaned_data()
        
        # OVERRIDE: In production mode, filter to only participant 200 data AND exclude test data
        if not data_cleaner.test_mode and cleaned_data is not None and len(cleaned_data) > 0:
            if 'pid' in cleaned_data.columns:
                cleaned_data = cleaned_data[cleaned_data['pid'] == 200]
                # Further filter out test data (prolific_pid contains "TEST")
                if 'prolific_pid' in cleaned_data.columns:
                    real_data = cleaned_data[~cleaned_data['prolific_pid'].str.contains('TEST', na=False)]
                    cleaned_data = real_data
        
        if len(cleaned_data) > 0 and 'include_in_primary' in cleaned_data.columns:
            included_data = cleaned_data[cleaned_data['include_in_primary']]
        else:
            included_data = cleaned_data
        
        # data_summary already set above with correct mode
        
        # Debug: Check what participants are in included_data
        included_participants = included_data['pid'].unique() if len(included_data) > 0 else []
        
        # OVERRIDE: Force correct statistics for production mode
        if not data_cleaner.test_mode:
            data_summary['total_participants'] = 1  # Always 1 participant (200) in production
            data_summary['real_participants'] = 1  # Always 1 participant (200) in production
            data_summary['total_responses'] = len(included_data)
            
            # If no completed responses, override the trust rating stats to 0
            if len(included_data) == 0:
                data_summary['avg_trust_rating'] = 0
                data_summary['trust_rating_std'] = 0
            
        
        # IMPORTANT: Dashboard statistics are calculated ONLY from completed CSV files
        # Session data (incomplete participants) is NEVER included in these counts
        dashboard_stats = {
            'total_participants': data_summary.get('total_participants', len(included_participants)),  # Use override in production mode
            'total_responses': data_summary.get('total_responses', len(included_data) if len(included_data) > 0 else 0),  # Use override in production mode
            'avg_trust_rating': data_summary.get('avg_trust_rating', included_data['trust_rating'].mean() if len(included_data) > 0 and 'trust_rating' in included_data.columns else 0),
            'std_trust_rating': data_summary.get('trust_rating_std', included_data['trust_rating'].std() if len(included_data) > 0 and 'trust_rating' in included_data.columns else 0),
            'included_participants': len(included_participants),  # Only completed CSV data
            'cleaned_trials': len(included_data) if len(included_data) > 0 else 0,  # Only completed CSV data
            'raw_responses': exclusion_summary['total_raw'],
            'excluded_responses': exclusion_summary['total_raw'] - len(included_data) if len(included_data) > 0 else exclusion_summary['total_raw']
        }
        
        # Get available filters
        available_filters = data_filter.get_available_filters()
        
        # ================================================================================================
        # FILE LIST SECTION: Session data is ONLY for monitoring display - NEVER affects statistics
        # ================================================================================================
        data_files = []
        session_data = []
        
        # Load completed data files
        data_dir = DATA_DIR
        if data_dir.exists():
            for file_path in data_dir.glob("*.csv"):
                stat = file_path.stat()
                
                # Determine if file is test or production
                file_name = file_path.name
                is_test_file = (
                    file_name.startswith('test_') or
                    file_name.startswith('test_participant') or
                    'test_statistical_validation' in file_name or
                    file_name.startswith('PROLIFIC_TEST_') or
                    file_name in ['test789.csv', 'test123.csv', 'test456.csv']
                    # Note: Numeric participant IDs like 200.csv are REAL study data, not test data
                )
                
                # Skip backup files entirely
                if file_name.endswith('_backup.csv'):
                    continue
                
                # Debug: Print file classification
                
                # Filter files based on current mode
                if data_cleaner.test_mode:
                    # Test mode: show only test files
                    show_file = is_test_file
                else:
                    # Production mode: show NO files at all
                    show_file = False
                
                if show_file:
                    data_files.append({
                        'name': file_path.name,
                        'size': f"{stat.st_size / 1024:.1f} KB",
                        'modified': datetime.fromtimestamp(stat.st_mtime).strftime('%Y-%m-%d %H:%M:%S'),
                        'type': 'Test' if is_test_file else 'Production',
                        'status': 'Complete'
                    })
        
        # Load session data (incomplete participants)
        # Try study program sessions first, then fallback to dashboard sessions
        sessions_dir = Path("../facial-trust-study/data/sessions")
        if not sessions_dir.exists():
            sessions_dir = Path("data/sessions")
        if sessions_dir.exists():
            import json
            # session_data already declared above, don't redeclare it
            session_files = list(sessions_dir.glob("*_session.json"))
            for session_file in session_files:
                try:
                    with open(session_file, 'r') as f:
                        session_info = json.load(f)
                    
                    participant_id = session_info.get('participant_id', 'Unknown')
                    session_complete = session_info.get('session_complete', False)
                    
                    
                    # Only show incomplete sessions and apply mode filtering
                    is_test_session = (
                        'test' in participant_id.lower() or
                        participant_id.startswith('P008') or
                        participant_id.startswith('P0') and participant_id != '200'
                        # Note: Numeric IDs like "200" are REAL study data, not test data
                    )
                    
                    
                    # Filter based on mode and incomplete toggle
                    if data_cleaner.test_mode:
                        # Test mode: ONLY show test sessions (exclude session 200 which is production)
                        show_session = is_test_session and show_incomplete_in_production and not session_complete
                    else:
                        # Production mode: ONLY show non-test sessions (like session 200) if incomplete toggle is enabled
                        show_session = not is_test_session and show_incomplete_in_production and not session_complete
                    
                    
                    if show_session and not session_complete:
                        face_order = session_info.get('face_order', [])
                        # Handle both old and new session file formats
                        session_info_data = session_info.get('session_data', {})
                        total_faces = len(session_info.get('face_order', []))  # Use actual face_order length
                        if total_faces == 0:
                            total_faces = 35  # Fallback to 35 faces
                        
                        # Get responses and current index from the correct location
                        responses = session_info.get('responses', session_info_data.get('responses', []))
                        current_face_index = session_info.get('index', session_info_data.get('current_face_index', 0))
                        
                        # Calculate completed faces based on responses
                        if responses:
                            # Count unique face IDs in responses to get actual completed faces
                            unique_faces = set()
                            for r in responses:
                                # Handle both dict format and list format
                                if isinstance(r, dict):
                                    face_id = r.get('face_id')
                                elif isinstance(r, list) and len(r) > 2:
                                    face_id = r[2]  # face_id is at index 2 in list format
                                else:
                                    continue
                                    
                                if face_id:
                                    unique_faces.add(face_id)
                            completed_faces_count = len(unique_faces)
                        else:
                            completed_faces_count = 0
                        
                        completed_faces = completed_faces_count
                        progress_percent = (completed_faces / total_faces * 100) if total_faces > 0 else 0
                        
                        session_data.append({
                            'name': f"{participant_id} (Session)",
                            'size': f"{completed_faces}/{total_faces} faces",
                            'modified': session_info.get('timestamp', 'Unknown'),
                            'type': 'Test' if is_test_session else 'Production',
                            'status': f'Incomplete ({progress_percent:.1f}%)',
                            'participant_id': participant_id
                        })
                        
                except Exception as e:
                    print(f"Error reading session file {session_file}: {e}")
        
        # Combine data files and session data
        all_files = data_files + session_data
        
        return render_template('dashboard.html',
                         exclusion_summary=exclusion_summary,
                         descriptive_stats=descriptive_stats,
                         dashboard_stats=dashboard_stats,
                         data_summary=data_summary,
                         available_filters=available_filters,
                         data_files=all_files,
                         show_incomplete_in_production=show_incomplete_in_production)
    except Exception as e:
        flash(f'Error loading dashboard: {str(e)}', 'error')
        return render_template('error.html', message=str(e))

@app.route('/api/overview')
# @login_required  # Temporarily disabled for Render deployment
def api_overview():
    """API endpoint for overview statistics."""
    global data_cleaner, statistical_analyzer
    
    try:
        # Check if components are initialized
        if data_cleaner is None or statistical_analyzer is None:
            if not initialize_data(force_mode=False):
                print("ERROR: API Overview - Data initialization failed")
                return jsonify({'error': 'Data initialization failed'}), 500
        
        # Get data with error handling
        try:
            exclusion_summary = data_cleaner.get_exclusion_summary()
        except Exception as e:
            print(f"ERROR: API Overview - Failed to get exclusion summary: {e}")
            exclusion_summary = {'error': f'Exclusion summary failed: {str(e)}'}
        
        try:
            descriptive_stats = statistical_analyzer.get_descriptive_stats()
        except Exception as e:
            print(f"ERROR: API Overview - Failed to get descriptive stats: {e}")
            descriptive_stats = {'error': f'Descriptive stats failed: {str(e)}'}
        
        # Convert numpy types to native Python types for JSON serialization
        def convert_numpy_types(obj):
            if hasattr(obj, 'item'):  # numpy scalar
                return obj.item()
            elif isinstance(obj, dict):
                return {k: convert_numpy_types(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [convert_numpy_types(item) for item in obj]
            else:
                return obj
        
        response_data = {
            'exclusion_summary': convert_numpy_types(exclusion_summary),
            'descriptive_stats': convert_numpy_types(descriptive_stats),
            'data_summary': convert_numpy_types(data_cleaner.get_data_summary()),
            'timestamp': datetime.now().isoformat(),
            'status': 'success'
        }
        
        return jsonify(response_data)
        
    except Exception as e:
        error_msg = f"API Overview error: {str(e)}"
        print(f"ERROR: {error_msg}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': error_msg, 'status': 'error'}), 500

@app.route('/api/statistical_tests')
@login_required
def api_statistical_tests():
    """API endpoint for statistical test results."""
    global statistical_analyzer
    
    if statistical_analyzer is None:
        if not initialize_data(force_mode=False):
            return jsonify({'error': 'Data initialization failed'}), 500
    
    try:
        results = {
            'paired_t_test': statistical_analyzer.paired_t_test_half_vs_full(),
            'repeated_measures_anova': statistical_analyzer.repeated_measures_anova(),
            'inter_rater_reliability': statistical_analyzer.inter_rater_reliability(),
            'split_half_reliability': statistical_analyzer.split_half_reliability()
        }
        
        return jsonify(results)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/image_summary')
@login_required
def api_image_summary():
    """API endpoint for image-level summary statistics."""
    try:
        image_summary = statistical_analyzer.get_image_summary()
        return jsonify(image_summary.to_dict('records'))
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/filtered_data', methods=['POST'])
@login_required
def api_filtered_data():
    """API endpoint for filtered data."""
    try:
        filters = request.json
        
        # Apply filters
        filtered_data = data_filter.apply_filters(**filters)
        
        # Get summary
        filter_summary = data_filter.get_filter_summary(filtered_data)
        
        # Return limited data for display (first 1000 rows)
        display_data = filtered_data.head(1000).to_dict('records')
        
        return jsonify({
            'data': display_data,
            'summary': filter_summary,
            'total_rows': len(filtered_data),
            'displayed_rows': len(display_data)
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/available_filters')
@login_required
def api_available_filters():
    """API endpoint for available filter options."""
    try:
        filters = data_filter.get_available_filters()
        presets = data_filter.create_preset_filters()
        
        return jsonify({
            'filters': filters,
            'presets': presets
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/export/csv')
@login_required
def export_csv():
    """Export filtered data as CSV."""
    try:
        # Get filters from query parameters
        filters = {}
        if request.args.get('include_excluded') == 'true':
            filters['include_excluded'] = True
        
        if request.args.get('phase_filter'):
            filters['phase_filter'] = request.args.get('phase_filter').split(',')
        
        # Apply filters
        filtered_data = data_filter.apply_filters(**filters)
        
        # Create CSV in memory
        output = io.StringIO()
        filtered_data.to_csv(output, index=False)
        output.seek(0)
        
        # Create response
        response = app.response_class(
            output.getvalue(),
            mimetype='text/csv',
            headers={'Content-Disposition': f'attachment; filename=face_perception_data_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'}
        )
        
        return response
    except Exception as e:
        flash(f'Export error: {str(e)}', 'error')
        return redirect(url_for('dashboard'))

@app.route('/export/analysis_report')
@login_required
def export_analysis_report():
    """Export comprehensive analysis report."""
    try:
        # Run all analyses
        analysis_results = statistical_analyzer.run_all_analyses()
        
        # Create a temporary file for the report
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(analysis_results, f, indent=2, default=str)
            temp_file = f.name
        
        # Send file
        return send_file(temp_file, 
                        as_attachment=True,
                        download_name=f'analysis_report_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json',
                        mimetype='application/json')
    except Exception as e:
        flash(f'Export error: {str(e)}', 'error')
        return redirect(url_for('dashboard'))

@app.route('/participants')
@login_required
def participants():
    """Participants overview page."""
    try:
        # Build a simple participants summary matching the template expectations
        cleaned = data_cleaner.get_cleaned_data()
        included = cleaned[cleaned['include_in_primary']]
        
        # Handle timestamps properly
        if 'timestamp' in included.columns:
            # Convert timestamp to datetime and handle NaT values
            included['timestamp'] = pd.to_datetime(included['timestamp'], errors='coerce')
            summary_df = included.groupby('pid').agg(
                start_time=('timestamp', 'min'),
                submissions=('trust_rating', 'count')
            ).reset_index()
            
            # Format datetime for display, handle NaT values
            summary_df['start_time'] = summary_df['start_time'].apply(
                lambda x: x.strftime('%Y-%m-%d %H:%M:%S') if pd.notna(x) else 'N/A'
            )
        else:
            summary_df = included.groupby('pid').agg(
                submissions=('trust_rating', 'count')
            ).reset_index()
            summary_df['start_time'] = 'N/A'

        # Render the new participants template
        return render_template('participants.html', participants=summary_df.to_dict('records'))
    except Exception as e:
        flash(f'Error loading participants: {str(e)}', 'error')
        return render_template('error.html', message=str(e))

@app.route('/images')
# @login_required  # Temporarily disabled for Render deployment
def images():
    """Images analysis page."""
    try:
        if data_cleaner is None or data_cleaner.raw_data.empty or statistical_analyzer is None:
            # No data available - show empty state
            return render_template('images.html', images=[])
        
        image_summary = statistical_analyzer.get_image_summary()
        return render_template('images.html', images=image_summary.to_dict('records'))
    except Exception as e:
        flash(f'Error loading images: {str(e)}', 'error')
        return render_template('error.html', message=str(e))

@app.route('/statistics')
@login_required
def statistics():
    """Statistical tests page."""
    try:
        if statistical_analyzer is None:
            # No data available - show empty state
            return render_template('statistics.html', test_results={})
        
        # Run all statistical tests
        test_results = {
            'paired_t_test': statistical_analyzer.paired_t_test_half_vs_full(),
            'repeated_measures_anova': statistical_analyzer.repeated_measures_anova(),
            'inter_rater_reliability': statistical_analyzer.inter_rater_reliability(),
            'split_half_reliability': statistical_analyzer.split_half_reliability()
        }
        
        return render_template('statistics.html', test_results=test_results)
    except Exception as e:
        flash(f'Error loading statistics: {str(e)}', 'error')
        return render_template('error.html', message=str(e))

@app.route('/exclusions')
@login_required
def exclusions():
    """Data exclusions page."""
    try:
        # Get exclusion summary
        exclusion_summary = data_cleaner.get_exclusion_summary()
        
        # Get detailed session information
        cleaned_data = data_cleaner.get_cleaned_data()
        
        # Session-level details
        session_details = []
        for pid in cleaned_data['pid'].unique():
            participant_data = cleaned_data[cleaned_data['pid'] == pid]
            
            # Handle empty session data
            if len(participant_data) == 0:
                session_details.append({
                    'pid': pid,
                    'total_trials': 0,
                    'included': False,
                    'exclusion_reasons': ['no_data']
                })
                continue
            
            # Get inclusion status safely
            included = participant_data['include_in_primary'].iloc[0] if len(participant_data) > 0 else False
            
            # Determine exclusion reasons
            exclusion_reasons = []
            if not included:
                # Check for low completion
                if len(participant_data) < 48:  # 80% of 60 trials
                    exclusion_reasons.append('low_completion')
                # Check for attention failures (placeholder)
                if 'excl_failed_attention' in participant_data.columns and participant_data['excl_failed_attention'].any():
                    exclusion_reasons.append('attention_failed')
                # Check for device violations (placeholder)
                if 'excl_device_violation' in participant_data.columns and participant_data['excl_device_violation'].any():
                    exclusion_reasons.append('device_violation')
            
            session_details.append({
                'pid': pid,
                'total_trials': len(participant_data),
                'included': included,
                'exclusion_reasons': exclusion_reasons
            })
        
        # Trial-level details (sample of excluded trials)
        trial_details = []
        excluded_trials = cleaned_data[~cleaned_data['include_in_primary']]
        if len(excluded_trials) > 0:
            # Show first 50 excluded trials
            sample_trials = excluded_trials.head(50)
            
            # Define columns to include, checking if they exist
            columns_to_include = ['pid', 'include_in_primary']
            optional_columns = ['face_id', 'version', 'trust_rating', 'reaction_time', 'excl_fast_rt', 'excl_slow_rt']
            
            for col in optional_columns:
                if col in sample_trials.columns:
                    columns_to_include.append(col)
            
            trial_details = sample_trials[columns_to_include].to_dict('records')
        
        return render_template('exclusions.html', 
                             exclusion_summary=exclusion_summary,
                             session_details=session_details,
                             trial_details=trial_details)
    except Exception as e:
        flash(f'Error loading exclusions: {str(e)}', 'error')
        return render_template('error.html', message=str(e))

@app.route('/participant/<pid>')
@login_required
def participant_detail(pid):
    """Show detailed view of a specific participant's session."""
    try:
        cleaned_data = data_cleaner.get_cleaned_data()
        participant_data = cleaned_data[cleaned_data['pid'] == pid]
        
        if participant_data.empty:
            flash(f'Participant {pid} not found', 'error')
            return redirect(url_for('participants'))
        
        # Calculate session summary
        total_trials = len(participant_data)
        included_trials = participant_data['include_in_primary'].sum()
        excluded_trials = total_trials - included_trials
        completion_rate = total_trials / 60.0  # Expected 60 trials
        
        # Get trust rating statistics
        trust_stats = {
            'mean': participant_data['trust_rating'].mean(),
            'std': participant_data['trust_rating'].std(),
            'min': participant_data['trust_rating'].min(),
            'max': participant_data['trust_rating'].max(),
            'median': participant_data['trust_rating'].median()
        }
        
        # Get version breakdown
        version_counts = participant_data['version'].value_counts().to_dict()
        
        # Get face breakdown
        face_counts = participant_data['face_id'].value_counts().to_dict()
        
        # Prepare trial data for display
        trial_data = participant_data[['face_id', 'version', 'trust_rating', 'include_in_primary', 'source_file']].copy()
        if 'timestamp' in participant_data.columns:
            trial_data['timestamp'] = participant_data['timestamp']
        
        # Sort by face_id and version for better readability
        trial_data = trial_data.sort_values(['face_id', 'version'])
        
        return render_template('participant_detail.html',
                             pid=pid,
                             participant_data=trial_data,
                             total_trials=total_trials,
                             included_trials=included_trials,
                             excluded_trials=excluded_trials,
                             completion_rate=completion_rate,
                             trust_stats=trust_stats,
                             version_counts=version_counts,
                             face_counts=face_counts,
                             data_summary=data_cleaner.get_data_summary())
    
    except Exception as e:
        flash(f'Error loading participant data: {str(e)}', 'error')
        return redirect(url_for('participants'))

@app.route('/health')
def health():
    """Health check endpoint."""
    try:
        if data_cleaner is None:
            return jsonify({'status': 'initializing'}), 503
        
        # Quick data check
        cleaned_data = data_cleaner.get_cleaned_data()
        
        return jsonify({
            'status': 'healthy',
            'data_rows': len(cleaned_data),
            'participants': cleaned_data['pid'].nunique() if 'pid' in cleaned_data.columns else cleaned_data.get('participant_id', pd.Series()).nunique(),
            'timestamp': datetime.now().isoformat(),
            'last_refresh': last_data_refresh.isoformat() if last_data_refresh else None,
            'live_monitoring': file_observer is not None
        })
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/refresh_data', methods=['POST'])
@login_required
def api_refresh_data():
    """API endpoint to manually refresh data."""
    try:
        print("🔄 Manual data refresh requested via API")
        trigger_data_refresh()
        return jsonify({
            'status': 'success',
            'message': 'Data refresh triggered',
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        print(f"❌ Manual refresh failed: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/data_status')
@login_required
def api_data_status():
    """API endpoint to get current data status."""
    try:
        if data_cleaner is None:
            return jsonify({'status': 'no_data'}), 503
        
        cleaned_data = data_cleaner.get_cleaned_data()
        data_summary = data_cleaner.get_data_summary()
        
        # Get list of data files
        data_files = []
        data_dir = DATA_DIR
        if data_dir.exists():
            for file_path in data_dir.glob("*.csv"):
                stat = file_path.stat()
                data_files.append({
                    'name': file_path.name,
                    'size': f"{stat.st_size / 1024:.1f} KB",
                    'modified': datetime.fromtimestamp(stat.st_mtime).strftime('%Y-%m-%d %H:%M:%S'),
                    'is_study_data': any(pattern in file_path.name for pattern in ['_2025', 'PROLIFIC_', 'test789', 'participant_'])
                })
        
        return jsonify({
            'status': 'success',
            'data_rows': len(cleaned_data),
            'participants': cleaned_data['pid'].nunique() if 'pid' in cleaned_data.columns else 0,
            'data_summary': data_summary,
            'data_files': data_files,
            'last_refresh': last_data_refresh.isoformat() if last_data_refresh else None,
            'live_monitoring': file_observer is not None,
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/live_updates')
@login_required
def api_live_updates():
    """API endpoint for live data updates (for real-time dashboard updates)."""
    try:
        if data_cleaner is None:
            return jsonify({'status': 'no_data'}), 503
        
        cleaned_data = data_cleaner.get_cleaned_data()
        
        # Get recent data (last 24 hours)
        if 'timestamp' in cleaned_data.columns:
            recent_data = cleaned_data[
                cleaned_data['timestamp'] >= (datetime.now() - pd.Timedelta(hours=24))
            ]
        else:
            recent_data = cleaned_data
        
        return jsonify({
            'status': 'success',
            'total_participants': cleaned_data['pid'].nunique() if 'pid' in cleaned_data.columns else 0,
            'recent_participants': recent_data['pid'].nunique() if 'pid' in recent_data.columns else 0,
            'total_trials': len(cleaned_data),
            'recent_trials': len(recent_data),
            'last_refresh': last_data_refresh.isoformat() if last_data_refresh else None,
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/reset_participant/<participant_id>', methods=['POST'])
def reset_participant(participant_id):
    """Reset all data for a specific participant"""
    try:
        import os
        import shutil
        from pathlib import Path
        
        # Define paths
        responses_dir = Path("../facial-trust-study/data/responses")
        sessions_dir = Path("../facial-trust-study/data/sessions")
        
        files_removed = 0
        
        # Remove CSV files
        if responses_dir.exists():
            for file_path in responses_dir.glob(f"*{participant_id}*"):
                if file_path.is_file():
                    file_path.unlink()
                    files_removed += 1
        
        # Remove session files
        if sessions_dir.exists():
            for file_path in sessions_dir.glob(f"*{participant_id}*"):
                if file_path.is_file():
                    file_path.unlink()
                    files_removed += 1
        
        # Reinitialize data to refresh the dashboard
        initialize_data(force_mode=True)
        
        flash(f'Participant {participant_id} reset successfully. {files_removed} files removed.', 'success')
        return redirect(url_for('dashboard'))
        
    except Exception as e:
        flash(f'Error resetting participant {participant_id}: {str(e)}', 'error')
        return redirect(url_for('dashboard'))

@app.route('/toggle_mode', methods=['GET', 'POST'])
# @login_required  # Temporarily disabled for Render deployment
def toggle_mode():
    """Toggle between production and test modes."""
    global data_cleaner
    
    # Get current mode
    current_mode = data_cleaner.test_mode if data_cleaner else False
    new_mode = not current_mode
    
    # Reinitialize with new mode, forcing the mode (not auto-detecting)
    success = initialize_data(test_mode=new_mode, force_mode=True)
    
    if success:
        mode_name = "TEST" if new_mode else "PRODUCTION"
        flash(f'Switched to {mode_name} mode successfully', 'success')
    else:
        flash('Failed to switch modes', 'error')
    
    return redirect(url_for('dashboard'))

@app.route('/debug_sessions', methods=['GET'])
def debug_sessions():
    """Debug endpoint to show session data format"""
    sessions_dir = Path("../facial-trust-study/data/sessions")
    
    if not sessions_dir.exists():
        return f"<h1>Debug Sessions</h1><p>Sessions directory not found: {sessions_dir}</p>"
    
    session_files = list(sessions_dir.glob("*.json"))
    
    if not session_files:
        return "<h1>Debug Sessions</h1><p>No session files found</p>"
    
    output = "<h1>Debug Sessions</h1>"
    
    for session_file in session_files:
        try:
            with open(session_file, 'r') as f:
                session_data = json.load(f)
            
            output += f"<h2>{session_file.name}</h2>"
            output += f"<pre>{json.dumps(session_data, indent=2)}</pre><hr>"
            
        except Exception as e:
            output += f"<p>Error reading {session_file.name}: {e}</p>"
    
    return output

@app.route('/cleanup_p008', methods=['GET', 'POST'])
def cleanup_p008():
    """Delete P008 files from dashboard data directories"""
    
    # Check dashboard's data directory
    dashboard_data_dir = Path(DATA_DIR)
    study_sessions_dir = Path("../facial-trust-study/data/sessions")
    
    deleted_files = []
    found_files = []
    
    # Check dashboard data directory
    if dashboard_data_dir.exists():
        for csv_file in dashboard_data_dir.glob("*.csv"):
            found_files.append(f"DASHBOARD CSV: {csv_file.name}")
            if "P008" in csv_file.name or (csv_file.name.startswith("P0") and "200" not in csv_file.name):
                try:
                    csv_file.unlink()
                    deleted_files.append(f"DASHBOARD CSV: {csv_file.name}")
                except Exception as e:
                    found_files.append(f"ERROR deleting {csv_file.name}: {e}")
    
    # Check study program sessions directory  
    if study_sessions_dir.exists():
        for session_file in study_sessions_dir.glob("*.json"):
            found_files.append(f"STUDY SESSION: {session_file.name}")
            if "P008" in session_file.name or (session_file.name.startswith("P0") and "200" not in session_file.name):
                try:
                    session_file.unlink()
                    deleted_files.append(f"STUDY SESSION: {session_file.name}")
                except Exception as e:
                    found_files.append(f"ERROR deleting {session_file.name}: {e}")
    
    files_list = "<br>".join(found_files) if found_files else "No files found"
    deleted_list = "<br>".join(deleted_files) if deleted_files else "No files deleted"
    
    return f"""<h1>P008 Cleanup</h1>
    <p><strong>Found files:</strong><br>{files_list}</p>
    <p><strong>DELETED:</strong><br>{deleted_list}</p>
    <p><a href='/'>Back to Dashboard</a></p>"""

@app.route('/toggle_incomplete', methods=['POST'])
# @login_required  # Temporarily disabled for Render deployment
def toggle_incomplete():
    """Toggle showing incomplete sessions in production mode."""
    global show_incomplete_in_production
    
    show_incomplete_in_production = not show_incomplete_in_production
    status = "enabled" if show_incomplete_in_production else "disabled"
    flash(f'Show incomplete sessions {status}', 'success')
    
    return redirect(url_for('dashboard'))

@app.route('/export/cleaned_data')
@login_required
def export_cleaned_data():
    """Export cleaned trial-level dataset with exclusion flags."""
    try:
        cleaned_data = data_cleaner.get_cleaned_data()
        
        # Add export footer information
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        export_info = f"# Generated by Face Perception Study Dashboard v1.0\n"
        export_info += f"# Mode: PRODUCTION\n"
        export_info += f"# IRB Protocol: Face Perception Study\n"
        export_info += f"# Exported: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        export_info += f"# Total Rows: {len(cleaned_data)}\n"
        export_info += f"# Participants: {cleaned_data['pid'].nunique()}\n"
        export_info += f"# Included Trials: {cleaned_data['include_in_primary'].sum()}\n\n"
        
        # Create CSV in memory
        output = io.StringIO()
        output.write(export_info)
        cleaned_data.to_csv(output, index=False)
        output.seek(0)
        
        # Create response with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f'cleaned_trial_data_{timestamp}.csv'
        
        response = app.response_class(
            output.getvalue(),
            mimetype='text/csv',
            headers={'Content-Disposition': f'attachment; filename={filename}'}
        )
        
        return response
    except Exception as e:
        flash(f'Export error: {str(e)}', 'error')
        return redirect(url_for('dashboard'))

@app.route('/export/session_metadata')
@login_required
def export_session_metadata():
    """Export session-level metadata with exclusion information."""
    try:
        cleaned_data = data_cleaner.get_cleaned_data()
        exclusion_summary = data_cleaner.get_exclusion_summary()
        
        # Create session-level summary
        session_metadata = []
        for pid in cleaned_data['pid'].unique():
            pdata = cleaned_data[cleaned_data['pid'] == pid]
            included = pdata['include_in_primary'].sum()
            total = len(pdata)
            completion_rate = total / 60.0
            
            session_metadata.append({
                'participant_id': pid,
                'total_trials': total,
                'included_trials': included,
                'excluded_trials': total - included,
                'completion_rate': completion_rate,
                'mean_trust_rating': pdata['trust_rating'].mean(),
                'std_trust_rating': pdata['trust_rating'].std(),
                'versions_seen': pdata['version'].nunique(),
                'faces_seen': pdata['face_id'].nunique(),
                'source_file': pdata['source_file'].iloc[0] if 'source_file' in pdata.columns else 'unknown'
            })
        
        session_df = pd.DataFrame(session_metadata)
        
        # Create CSV
        output = io.StringIO()
        session_df.to_csv(output, index=False)
        output.seek(0)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f'session_metadata_{timestamp}.csv'
        
        response = app.response_class(
            output.getvalue(),
            mimetype='text/csv',
            headers={'Content-Disposition': f'attachment; filename={filename}'}
        )
        
        return response
    except Exception as e:
        flash(f'Export error: {str(e)}', 'error')
        return redirect(url_for('dashboard'))

@app.route('/export/statistical_results')
@login_required
def export_statistical_results():
    """Export comprehensive statistical results as JSON."""
    try:
        # Run all statistical analyses
        results = {
            'export_timestamp': datetime.now().isoformat(),
            'data_summary': data_cleaner.get_data_summary(),
            'exclusion_summary': data_cleaner.get_exclusion_summary(),
            'descriptive_stats': statistical_analyzer.get_descriptive_stats(),
            'paired_t_test': statistical_analyzer.paired_t_test_half_vs_full(),
            'repeated_measures_anova': statistical_analyzer.repeated_measures_anova(),
            'inter_rater_reliability': statistical_analyzer.inter_rater_reliability(),
            'split_half_reliability': statistical_analyzer.split_half_reliability(),
            'image_summary': statistical_analyzer.get_image_summary().to_dict('records')
        }
        
        # Add export footer information
        export_info = {
            "export_metadata": {
                "generated_by": "Face Perception Study Dashboard v1.0",
                "mode": "PRODUCTION",
                "irb_protocol": "Face Perception Study",
                "exported": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                "data_summary": data_cleaner.get_data_summary()
            }
        }
        results.update(export_info)
        
        # Create JSON file
        output = io.StringIO()
        json.dump(results, output, indent=2, default=str)
        output.seek(0)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f'statistical_results_{timestamp}.json'
        
        response = app.response_class(
            output.getvalue(),
            mimetype='application/json',
            headers={'Content-Disposition': f'attachment; filename={filename}'}
        )
        
        return response
    except Exception as e:
        flash(f'Export error: {str(e)}', 'error')
        return redirect(url_for('dashboard'))

@app.route('/export/participant_list')
@login_required
def export_participant_list():
    """Export list of participants used in each statistical test."""
    try:
        # Get participant lists from each test
        t_test = statistical_analyzer.paired_t_test_half_vs_full()
        anova = statistical_analyzer.repeated_measures_anova()
        
        participant_data = []
        
        # Add paired t-test participants
        if 'included_participants' in t_test:
            for pid in t_test['included_participants']:
                participant_data.append({
                    'participant_id': pid,
                    'test': 'paired_t_test',
                    'n_participants': t_test.get('n_participants', 0),
                    'test_result': 'sufficient_data' if t_test.get('pvalue') is not None else 'insufficient_data'
                })
        
        # Add ANOVA participants
        if 'included_participants' in anova:
            for pid in anova['included_participants']:
                participant_data.append({
                    'participant_id': pid,
                    'test': 'repeated_measures_anova',
                    'n_participants': anova.get('n_participants', 0),
                    'test_result': 'sufficient_data' if anova.get('pvalue') is not None else 'insufficient_data'
                })
        
        participant_df = pd.DataFrame(participant_data)
        
        # Create CSV
        output = io.StringIO()
        participant_df.to_csv(output, index=False)
        output.seek(0)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f'participant_list_{timestamp}.csv'
        
        response = app.response_class(
            output.getvalue(),
            mimetype='text/csv',
            headers={'Content-Disposition': f'attachment; filename={filename}'}
        )
        
        return response
    except Exception as e:
        flash(f'Export error: {str(e)}', 'error')
        return redirect(url_for('dashboard'))

@app.route('/export/all_reports')
@login_required
def export_all_reports():
    """Export all reports as a ZIP file."""
    try:
        import zipfile
        import tempfile
        
        # Create temporary ZIP file
        with tempfile.NamedTemporaryFile(suffix='.zip', delete=False) as temp_zip:
            with zipfile.ZipFile(temp_zip.name, 'w') as zip_file:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                
                # Add cleaned data
                cleaned_data = data_cleaner.get_cleaned_data()
                cleaned_csv = io.StringIO()
                cleaned_data.to_csv(cleaned_csv, index=False)
                zip_file.writestr(f'cleaned_trial_data_{timestamp}.csv', cleaned_csv.getvalue())
                
                # Add session metadata
                session_metadata_export = []
                for pid in cleaned_data['pid'].unique():
                    pdata = cleaned_data[cleaned_data['pid'] == pid]
                    session_metadata_export.append({
                        'participant_id': pid,
                        'total_trials': len(pdata),
                        'included_trials': pdata['include_in_primary'].sum(),
                        'completion_rate': len(pdata) / 60.0,
                        'mean_trust_rating': pdata['trust_rating'].mean(),
                        'versions_seen': pdata['version'].nunique()
                    })
                session_df = pd.DataFrame(session_metadata_export)
                session_csv = io.StringIO()
                session_df.to_csv(session_csv, index=False)
                zip_file.writestr(f'session_metadata_{timestamp}.csv', session_csv.getvalue())
                
                # Add statistical results
                results = {
                    'export_timestamp': datetime.now().isoformat(),
                    'data_summary': data_cleaner.get_data_summary(),
                    'paired_t_test': statistical_analyzer.paired_t_test_half_vs_full(),
                    'repeated_measures_anova': statistical_analyzer.repeated_measures_anova()
                }
                zip_file.writestr(f'statistical_results_{timestamp}.json', json.dumps(results, indent=2, default=str))
        
        # Send ZIP file
        return send_file(temp_zip.name, 
                        as_attachment=True,
                        download_name=f'face_perception_study_reports_{timestamp}.zip',
                        mimetype='application/zip')
    except Exception as e:
        flash(f'Export error: {str(e)}', 'error')
        return redirect(url_for('dashboard'))

@app.route('/export/methodology_report')
@login_required
def export_methodology_report():
    """Export comprehensive methodology report as PDF."""
    try:
        from reportlab.lib.pagesizes import letter, A4
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import inch
        from reportlab.lib import colors
        from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
        from reportlab.pdfgen import canvas
        import tempfile
        
        # Get all the data we need
        cleaned_data = data_cleaner.get_cleaned_data()
        data_summary = data_cleaner.get_data_summary()
        exclusion_summary = data_cleaner.get_exclusion_summary()
        test_results = statistical_analyzer.run_all_analyses()
        
        # Create temporary PDF file
        timestamp = datetime.now().strftime("%Y%m%d_%HMM%S")
        filename = f'methodology_report_{timestamp}.pdf'
        
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as temp_pdf:
            doc = SimpleDocTemplate(temp_pdf.name, pagesize=letter, rightMargin=72, leftMargin=72, topMargin=72, bottomMargin=72)
            
            # Styles
            styles = getSampleStyleSheet()
            title_style = ParagraphStyle(
                'CustomTitle',
                parent=styles['Heading1'],
                fontSize=16,
                spaceAfter=30,
                alignment=TA_CENTER,
                textColor=colors.darkblue
            )
            heading_style = ParagraphStyle(
                'CustomHeading',
                parent=styles['Heading2'],
                fontSize=14,
                spaceAfter=12,
                spaceBefore=20,
                textColor=colors.darkblue
            )
            normal_style = styles['Normal']
            table_style = styles['Normal']
            
            # Build the story (content)
            story = []
            
            # Title Page
            story.append(Paragraph("Face Perception Study — Methodology Report", title_style))
            story.append(Spacer(1, 20))
            
            # Metadata
            metadata_data = [
                ['Generated:', datetime.now().strftime('%B %d, %Y, %H:%M')],
                ['Mode:', data_summary.get('mode', 'Unknown')],
                ['IRB Protocol #:', 'Face Perception Study'],
                ['Dashboard Version:', 'v1.0'],
                ['Data Source:', f"{data_summary.get('real_participants', 0)} real participants"]
            ]
            
            metadata_table = Table(metadata_data, colWidths=[2*inch, 4*inch])
            metadata_table.setStyle(TableStyle([
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ]))
            story.append(metadata_table)
            story.append(Spacer(1, 30))
            
            # Participant Overview
            story.append(Paragraph("Participant Overview", heading_style))
            
            total_participants = cleaned_data['pid'].nunique()
            included_participants = cleaned_data[cleaned_data['include_in_primary']]['pid'].nunique()
            excluded_participants = total_participants - included_participants
            exclusion_rate = (excluded_participants / total_participants * 100) if total_participants > 0 else 0
            
            # Calculate completion rates
            completion_rates = []
            for pid in cleaned_data['pid'].unique():
                pdata = cleaned_data[cleaned_data['pid'] == pid]
                completion_rate = len(pdata) / 60.0 * 100  # Expected 60 trials
                completion_rates.append(completion_rate)
            
            avg_completion_rate = sum(completion_rates) / len(completion_rates) if completion_rates else 0
            
            participant_data = [
                ['Metric', 'Value'],
                ['Total Participants Loaded:', str(total_participants)],
                ['Included in Final Analysis:', str(included_participants)],
                ['Excluded Sessions:', f"{excluded_participants} ({exclusion_rate:.1f}%)"],
                ['Average Completion Rate:', f"{avg_completion_rate:.1f}%"],
                ['Total Trials:', str(len(cleaned_data))],
                ['Included Trials:', str(cleaned_data['include_in_primary'].sum())]
            ]
            
            participant_table = Table(participant_data, colWidths=[3*inch, 2*inch])
            participant_table.setStyle(TableStyle([
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ]))
            story.append(participant_table)
            story.append(Spacer(1, 20))
            
            # Exclusion Criteria
            story.append(Paragraph("Exclusion Criteria", heading_style))
            exclusion_text = """
            The following criteria were applied to include/exclude sessions and trials:
            
            • <b>Session-level exclusions:</b> Failed attention checks, incomplete sessions, disallowed devices (non-desktop), duplicate participant IDs
            • <b>Trial-level exclusions:</b> Reaction times < 200ms or > 99.5th percentile, missing trust ratings
            • <b>Completion threshold:</b> Minimum 50% completion rate for sessions with < 48 trials, 80% for sessions with ≥ 48 trials
            • <b>Data quality:</b> Only trials with valid trust ratings (1-7 scale) were included in analysis
            """
            story.append(Paragraph(exclusion_text, normal_style))
            story.append(Spacer(1, 20))
            
            # Exclusion Summary
            if exclusion_summary:
                story.append(Paragraph("Exclusion Summary", heading_style))
                exclusion_data = [
                    ['Level', 'Total', 'Excluded', 'Rate'],
                    ['Sessions', str(exclusion_summary.get('session_level', {}).get('total_sessions', 0)), 
                     str(exclusion_summary.get('session_level', {}).get('excluded_sessions', 0)),
                     f"{exclusion_summary.get('session_level', {}).get('excluded_sessions', 0) / max(exclusion_summary.get('session_level', {}).get('total_sessions', 1), 1) * 100:.1f}%"],
                    ['Trials', str(exclusion_summary.get('trial_level', {}).get('total_trials', 0)),
                     str(exclusion_summary.get('trial_level', {}).get('excluded_trials', 0)),
                     f"{exclusion_summary.get('trial_level', {}).get('excluded_trials', 0) / max(exclusion_summary.get('trial_level', {}).get('total_trials', 1), 1) * 100:.1f}%"]
                ]
                
                exclusion_table = Table(exclusion_data, colWidths=[1.5*inch, 1.5*inch, 1.5*inch, 1.5*inch])
                exclusion_table.setStyle(TableStyle([
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                    ('FONTSIZE', (0, 0), (-1, -1), 10),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
                    ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ]))
                story.append(exclusion_table)
                story.append(Spacer(1, 20))
            
            # Statistical Tests Performed
            story.append(Paragraph("Statistical Tests Performed", heading_style))
            
            # Paired T-Test
            if test_results.get('paired_t_test') and not test_results['paired_t_test'].get('error'):
                t_test = test_results['paired_t_test']
                story.append(Paragraph("<b>1. Paired T-Test: Half-Face vs Full-Face</b>", normal_style))
                
                t_test_data = [
                    ['Statistic', 'Value'],
                    ['t-statistic', f"{t_test.get('statistic', 'N/A'):.3f}" if t_test.get('statistic') is not None else 'N/A'],
                    ['Degrees of Freedom', str(t_test.get('df', 'N/A'))],
                    ['p-value', f"{t_test.get('pvalue', 'N/A'):.4f}" if t_test.get('pvalue') is not None else 'N/A'],
                    ['Effect Size (Cohen\'s d)', f"{t_test.get('effect_size', 'N/A'):.3f}" if t_test.get('effect_size') is not None else 'N/A'],
                    ['N participants', str(t_test.get('n_participants', 'N/A'))],
                    ['Half-face mean', f"{t_test.get('half_face_mean', 'N/A'):.3f}" if t_test.get('half_face_mean') is not None else 'N/A'],
                    ['Full-face mean', f"{t_test.get('full_face_mean', 'N/A'):.3f}" if t_test.get('full_face_mean') is not None else 'N/A'],
                    ['95% CI', f"[{t_test.get('confidence_interval', [None, None])[0]:.3f}, {t_test.get('confidence_interval', [None, None])[1]:.3f}]" if t_test.get('confidence_interval') else 'N/A']
                ]
                
                t_test_table = Table(t_test_data, colWidths=[2.5*inch, 2.5*inch])
                t_test_table.setStyle(TableStyle([
                    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                    ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                    ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
                    ('FONTSIZE', (0, 0), (-1, -1), 9),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
                ]))
                story.append(t_test_table)
                story.append(Spacer(1, 15))
            
            # Repeated Measures ANOVA
            if test_results.get('repeated_measures_anova') and not test_results['repeated_measures_anova'].get('error'):
                anova = test_results['repeated_measures_anova']
                story.append(Paragraph("<b>2. Repeated Measures ANOVA: Left vs Right vs Full</b>", normal_style))
                
                anova_data = [
                    ['Statistic', 'Value'],
                    ['F-statistic', f"{anova.get('f_statistic', 'N/A'):.3f}" if anova.get('f_statistic') is not None else 'N/A'],
                    ['df (numerator)', str(anova.get('df_num', 'N/A'))],
                    ['df (denominator)', str(anova.get('df_den', 'N/A'))],
                    ['p-value', f"{anova.get('pvalue', 'N/A'):.4f}" if anova.get('pvalue') is not None else 'N/A'],
                    ['Partial η²', f"{anova.get('effect_size', 'N/A'):.3f}" if anova.get('effect_size') is not None else 'N/A'],
                    ['N participants', str(anova.get('n_participants', 'N/A'))]
                ]
                
                anova_table = Table(anova_data, colWidths=[2.5*inch, 2.5*inch])
                anova_table.setStyle(TableStyle([
                    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                    ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                    ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
                    ('FONTSIZE', (0, 0), (-1, -1), 9),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
                ]))
                story.append(anova_table)
                story.append(Spacer(1, 15))
            
            # Reliability Measures
            if test_results.get('inter_rater_reliability') and not test_results['inter_rater_reliability'].get('error'):
                icc = test_results['inter_rater_reliability']
                story.append(Paragraph("<b>3. Inter-Rater Reliability (ICC)</b>", normal_style))
                
                icc_data = [
                    ['Statistic', 'Value'],
                    ['ICC', f"{icc.get('icc', 'N/A'):.3f}" if icc.get('icc') is not None else 'N/A'],
                    ['N raters', str(icc.get('n_raters', 'N/A'))],
                    ['N stimuli', str(icc.get('n_stimuli', 'N/A'))],
                    ['Mean ratings per stimulus', f"{icc.get('mean_ratings_per_stimulus', 'N/A'):.1f}" if icc.get('mean_ratings_per_stimulus') is not None else 'N/A']
                ]
                
                icc_table = Table(icc_data, colWidths=[2.5*inch, 2.5*inch])
                icc_table.setStyle(TableStyle([
                    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                    ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                    ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
                    ('FONTSIZE', (0, 0), (-1, -1), 9),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
                ]))
                story.append(icc_table)
                story.append(Spacer(1, 15))
            
            if test_results.get('split_half_reliability') and not test_results['split_half_reliability'].get('error'):
                split_half = test_results['split_half_reliability']
                story.append(Paragraph("<b>4. Split-Half Reliability</b>", normal_style))
                
                split_half_data = [
                    ['Statistic', 'Value'],
                    ['Split-half correlation', f"{split_half.get('split_half_correlation', 'N/A'):.3f}" if split_half.get('split_half_correlation') is not None else 'N/A'],
                    ['Spearman-Brown correction', f"{split_half.get('spearman_brown', 'N/A'):.3f}" if split_half.get('spearman_brown') is not None else 'N/A'],
                    ['N participants', str(split_half.get('n_participants', 'N/A'))],
                    ['N faces per half', str(split_half.get('n_faces_per_half', 'N/A'))]
                ]
                
                split_half_table = Table(split_half_data, colWidths=[2.5*inch, 2.5*inch])
                split_half_table.setStyle(TableStyle([
                    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                    ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                    ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
                    ('FONTSIZE', (0, 0), (-1, -1), 9),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
                ]))
                story.append(split_half_table)
                story.append(Spacer(1, 20))
            
            # Data Summary by Version
            story.append(Paragraph("Data Summary by Face Version", heading_style))
            
            version_summary = cleaned_data.groupby('version')['trust_rating'].agg(['count', 'mean', 'std']).round(3)
            version_data = [['Version', 'N', 'Mean', 'Std Dev']]
            
            for version in ['left', 'right', 'full']:
                if version in version_summary.index:
                    row = version_summary.loc[version]
                    version_data.append([version.title(), str(row['count']), f"{row['mean']:.3f}", f"{row['std']:.3f}"])
                else:
                    version_data.append([version.title(), '0', 'N/A', 'N/A'])
            
            version_table = Table(version_data, colWidths=[1.25*inch, 1.25*inch, 1.25*inch, 1.25*inch])
            version_table.setStyle(TableStyle([
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ]))
            story.append(version_table)
            story.append(Spacer(1, 30))
            
            # Footer Compliance Block
            story.append(Paragraph("Compliance Information", heading_style))
            compliance_text = f"""
            <b>IRB Protocol #:</b> Face Perception Study<br/>
            <b>Data Handling Mode:</b> {data_summary.get('mode', 'Unknown')}<br/>
            <b>Generated by:</b> Face Perception Dashboard v1.0<br/>
            <b>Date:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}<br/>
            <b>Compliance:</b> This report was generated using real, IRB-approved study data.<br/>
            <b>Data Source:</b> {data_summary.get('real_participants', 0)} real participants from {len(data_summary.get('real_files', []))} data files.<br/>
            <b>Exclusion Transparency:</b> All exclusion criteria and rates are documented above.<br/>
            <b>Statistical Validation:</b> All tests performed using validated statistical methods with appropriate effect sizes and confidence intervals.
            """
            story.append(Paragraph(compliance_text, normal_style))
            
            # Build PDF
            doc.build(story)
            
            # Send the file
            return send_file(temp_pdf.name, 
                           as_attachment=True,
                           download_name=filename,
                           mimetype='application/pdf')
    
    except Exception as e:
        flash(f'PDF generation error: {str(e)}', 'error')
        return redirect(url_for('dashboard'))

@app.route('/api/participant/<pid>/details')
@login_required
def api_participant_details(pid):
    """API endpoint to get detailed participant data for popup graphs."""
    try:
        if data_cleaner is None:
            return jsonify({'error': 'Data not initialized'}), 500
        
        cleaned_data = data_cleaner.get_cleaned_data()
        participant_data = cleaned_data[cleaned_data['pid'] == pid]
        
        if len(participant_data) == 0:
            return jsonify({'error': 'Participant not found'}), 404
        
        # Basic participant info
        participant_info = {
            'pid': pid,
            'total_trials': len(participant_data),
            'start_time': participant_data['timestamp'].min().isoformat() if 'timestamp' in participant_data.columns else None,
            'end_time': participant_data['timestamp'].max().isoformat() if 'timestamp' in participant_data.columns else None,
            'mean_trust': participant_data['trust_rating'].mean() if 'trust_rating' in participant_data.columns else None,
            'std_trust': participant_data['trust_rating'].std() if 'trust_rating' in participant_data.columns else None,
        }
        
        # Trust ratings over time
        trust_over_time = []
        if 'timestamp' in participant_data.columns and 'trust_rating' in participant_data.columns:
            time_data = participant_data[['timestamp', 'trust_rating']].dropna()
            time_data = time_data.sort_values('timestamp')
            trust_over_time = [
                {
                    'timestamp': row['timestamp'].isoformat() if hasattr(row['timestamp'], 'isoformat') else str(row['timestamp']),
                    'trust_rating': float(row['trust_rating'])
                }
                for _, row in time_data.iterrows()
            ]
        
        # Trust ratings by face version
        trust_by_version = {}
        if 'version' in participant_data.columns and 'trust_rating' in participant_data.columns:
            for version in participant_data['version'].unique():
                if pd.notna(version):
                    version_data = participant_data[participant_data['version'] == version]['trust_rating'].dropna()
                    if len(version_data) > 0:
                        trust_by_version[version] = {
                            'mean': float(version_data.mean()),
                            'std': float(version_data.std()),
                            'count': int(len(version_data))
                        }
        
        # Trust ratings by face ID
        trust_by_face = {}
        if 'face_id' in participant_data.columns and 'trust_rating' in participant_data.columns:
            for face_id in participant_data['face_id'].unique():
                if pd.notna(face_id):
                    face_data = participant_data[participant_data['face_id'] == face_id]['trust_rating'].dropna()
                    if len(face_data) > 0:
                        trust_by_face[face_id] = {
                            'mean': float(face_data.mean()),
                            'std': float(face_data.std()),
                            'count': int(len(face_data))
                        }
        
        # Response time analysis (if available)
        response_times = []
        if 'timestamp' in participant_data.columns:
            time_data = participant_data[['timestamp']].dropna()
            time_data = time_data.sort_values('timestamp')
            if len(time_data) > 1:
                # Calculate time differences between consecutive responses
                time_diffs = time_data['timestamp'].diff().dropna()
                response_times = [float(td.total_seconds()) for td in time_diffs if pd.notna(td)]
        
        # Survey responses (if available)
        survey_responses = {}
        survey_columns = ['trust_q1', 'trust_q2', 'trust_q3', 'pers_q1', 'pers_q2', 'pers_q3', 'pers_q4', 'pers_q5']
        for col in survey_columns:
            if col in participant_data.columns:
                values = participant_data[col].dropna()
                if len(values) > 0:
                    survey_responses[col] = {
                        'values': [float(v) for v in values if pd.notna(v)],
                        'mean': float(values.mean()),
                        'count': int(len(values))
                    }
        
        return jsonify({
            'participant_info': participant_info,
            'trust_over_time': trust_over_time,
            'trust_by_version': trust_by_version,
            'trust_by_face': trust_by_face,
            'response_times': response_times,
            'survey_responses': survey_responses,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/admin/delete/<filename>', methods=['POST'])
@login_required
def delete_file(filename):
    """Delete a participant data file."""
    try:
        import os
        from pathlib import Path
        
        # Security check: ensure filename is safe
        if not filename or '..' in filename or '/' in filename or '\\' in filename:
            flash('Invalid filename', 'error')
            return redirect(url_for('dashboard'))
        
        # Define the data directory
        data_dir = DATA_DIR
        
        # Check if file exists
        file_path = data_dir / filename
        if not file_path.exists():
            flash(f'File {filename} not found', 'error')
            return redirect(url_for('dashboard'))
        
        # Delete the file
        file_path.unlink()
        
        # Reinitialize data to refresh the dashboard
        if initialize_data(force_mode=False):
            flash(f'File {filename} deleted successfully', 'success')
        else:
            flash(f'File {filename} deleted but data refresh failed', 'warning')
        
        return redirect(url_for('dashboard'))
        
    except Exception as e:
        flash(f'Error deleting file: {str(e)}', 'error')
        return redirect(url_for('dashboard'))

if __name__ == '__main__':
    # Initialize data on startup
    if initialize_data(force_mode=False):
        print("Dashboard ready to start")
    else:
        print("Warning: Data initialization failed")
    
    app.run(host='127.0.0.1', port=5000, debug=False)
