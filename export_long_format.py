#!/usr/bin/env python3
"""
Export data in long format for proper dashboard compatibility
"""
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime
import sys
import os

# Add the current directory to Python path
sys.path.append(str(Path(__file__).parent))

# Import the data cleaner
from dashboard.analysis.cleaning import DataCleaner

def export_long_format_data():
    """Export data in long format (one row per question response)"""
    
    print("🔄 Loading data...")
    
    # Initialize data cleaner
    data_cleaner = DataCleaner("data/responses")
    
    # Load raw data (before wide format conversion)
    raw_data = data_cleaner.load_data()
    
    print(f"✅ Loaded {len(raw_data)} raw responses")
    print(f"📊 Participants: {raw_data['pid'].nunique()}")
    print(f"📊 Questions: {raw_data['question'].value_counts().to_dict()}")
    print(f"📊 Versions: {raw_data['version'].value_counts().to_dict()}")
    
    # Create export directory
    export_dir = Path("exports")
    export_dir.mkdir(exist_ok=True)
    
    # Export the raw long format data
    print("\n📁 Exporting long format data...")
    long_format_file = export_dir / f"long_format_responses_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    
    # Select key columns for analysis
    export_columns = [
        'pid', 'face_id', 'version', 'question', 'response', 'timestamp'
    ]
    
    # Filter to only include columns that exist
    available_columns = [col for col in export_columns if col in raw_data.columns]
    long_data = raw_data[available_columns].copy()
    
    # Add metadata
    long_data['export_timestamp'] = datetime.now().isoformat()
    long_data['data_source'] = 'Face Perception Study Dashboard - Long Format'
    
    long_data.to_csv(long_format_file, index=False)
    print(f"✅ Long format data exported to: {long_format_file}")
    
    # Create summary by question type
    print("\n📁 Creating question type summary...")
    question_summary_file = export_dir / f"question_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    
    question_summary = []
    for question in long_data['question'].unique():
        question_data = long_data[long_data['question'] == question]
        for version in ['left', 'right', 'both']:
            version_data = question_data[question_data['version'] == version]
            if len(version_data) > 0:
                responses = pd.to_numeric(version_data['response'], errors='coerce').dropna()
                question_summary.append({
                    'question': question,
                    'version': version,
                    'n': len(responses),
                    'mean': responses.mean(),
                    'std': responses.std(),
                    'min': responses.min(),
                    'max': responses.max()
                })
    
    question_df = pd.DataFrame(question_summary)
    question_df.to_csv(question_summary_file, index=False)
    print(f"✅ Question summary exported to: {question_summary_file}")
    
    # Create trust ratings only (for statistical tests)
    print("\n📁 Creating trust ratings only dataset...")
    trust_only_file = export_dir / f"trust_ratings_only_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    
    trust_data = long_data[long_data['question'] == 'trust'].copy()
    trust_data['trust_rating'] = pd.to_numeric(trust_data['response'], errors='coerce')
    trust_data = trust_data.dropna(subset=['trust_rating'])
    
    # Select final columns
    trust_export = trust_data[['pid', 'face_id', 'version', 'trust_rating', 'timestamp', 'export_timestamp', 'data_source']].copy()
    
    trust_export.to_csv(trust_only_file, index=False)
    print(f"✅ Trust ratings only exported to: {trust_only_file}")
    
    print(f"\n🎉 Long format exports completed! Files saved in: {export_dir}")
    print("\nFiles created:")
    print(f"  - {long_format_file.name} (Long format: {len(long_data)} rows)")
    print(f"  - {question_summary_file.name} (Question type summary)")
    print(f"  - {trust_only_file.name} (Trust ratings only: {len(trust_export)} rows)")
    
    print(f"\n📊 Expected structure:")
    print(f"  - Total rows: {len(long_data)} (should be ~21,000)")
    print(f"  - Trust ratings: {len(trust_export)} (should be ~6,300)")
    print(f"  - Per participant: {len(long_data) / raw_data['pid'].nunique():.0f} responses")
    print(f"  - Per face: {len(long_data) / raw_data['face_id'].nunique():.0f} responses")

if __name__ == "__main__":
    export_long_format_data()
