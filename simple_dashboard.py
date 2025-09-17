#!/usr/bin/env python3
"""
Simple dashboard that bypasses the complex initialization
"""

from flask import Flask, render_template_string
import pandas as pd
from pathlib import Path
import sys
import os

# Add paths
sys.path.append('.')
sys.path.append('dashboard')

app = Flask(__name__)

# Simple HTML template
TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Psychology Study Dashboard</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; }
        .container { max-width: 1200px; margin: 0 auto; }
        .stats { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin: 20px 0; }
        .stat-card { background: #f5f5f5; padding: 20px; border-radius: 8px; text-align: center; }
        .stat-number { font-size: 2em; font-weight: bold; color: #2c3e50; }
        .stat-label { color: #7f8c8d; margin-top: 5px; }
        table { width: 100%; border-collapse: collapse; margin: 20px 0; }
        th, td { padding: 12px; text-align: left; border-bottom: 1px solid #ddd; }
        th { background-color: #34495e; color: white; }
        tr:hover { background-color: #f5f5f5; }
        .error { background: #e74c3c; color: white; padding: 15px; border-radius: 5px; margin: 20px 0; }
    </style>
</head>
<body>
    <div class="container">
        <h1>Psychology Study Dashboard</h1>
        
        {% if error %}
        <div class="error">{{ error }}</div>
        {% else %}
        
        <div class="stats">
            <div class="stat-card">
                <div class="stat-number">{{ stats.total_responses }}</div>
                <div class="stat-label">Total Responses</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">{{ stats.participants }}</div>
                <div class="stat-label">Participants</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">{{ stats.faces }}</div>
                <div class="stat-label">Unique Faces</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">{{ stats.files }}</div>
                <div class="stat-label">CSV Files</div>
            </div>
        </div>
        
        <h2>Recent Data</h2>
        <table>
            <thead>
                <tr>
                    <th>Participant</th>
                    <th>Face ID</th>
                    <th>Version</th>
                    <th>Question</th>
                    <th>Response</th>
                    <th>Timestamp</th>
                </tr>
            </thead>
            <tbody>
                {% for row in recent_data %}
                <tr>
                    <td>{{ row.pid }}</td>
                    <td>{{ row.face_id }}</td>
                    <td>{{ row.version }}</td>
                    <td>{{ row.question }}</td>
                    <td>{{ row.response }}</td>
                    <td>{{ row.timestamp }}</td>
                </tr>
                {% endfor %}
            </tbody>
        </table>
        
        {% endif %}
    </div>
</body>
</html>
"""

@app.route('/')
@app.route('/dashboard/')
def dashboard():
    try:
        # Load CSV data
        data_dir = Path('data/responses')
        csv_files = list(data_dir.glob('*.csv'))
        
        if not csv_files:
            return render_template_string(TEMPLATE, error="No CSV files found")
        
        # Load all data
        all_data = []
        for file_path in csv_files:
            try:
                df = pd.read_csv(file_path)
                all_data.append(df)
            except Exception as e:
                print(f"Error loading {file_path}: {e}")
        
        if not all_data:
            return render_template_string(TEMPLATE, error="Could not load any data")
        
        # Combine data
        combined = pd.concat(all_data, ignore_index=True)
        
        # Calculate stats
        stats = {
            'total_responses': len(combined),
            'participants': combined['pid'].nunique() if 'pid' in combined.columns else 0,
            'faces': combined['face_id'].nunique() if 'face_id' in combined.columns else 0,
            'files': len(csv_files)
        }
        
        # Get recent data (last 20 rows)
        recent_data = combined.tail(20).to_dict('records')
        
        return render_template_string(TEMPLATE, stats=stats, recent_data=recent_data)
        
    except Exception as e:
        return render_template_string(TEMPLATE, error=f"Error: {str(e)}")

if __name__ == '__main__':
    print("Starting dashboard on http://localhost:3000/dashboard/")
    app.run(host='0.0.0.0', port=3000, debug=False)
