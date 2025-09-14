#!/usr/bin/env python3
"""
Export individual test responses for SPSS analysis
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

def export_individual_responses():
    """Export individual test responses for SPSS verification"""
    
    print("🔄 Loading data...")
    
    # Initialize data cleaner
    data_cleaner = DataCleaner("data/responses")
    
    # Load and clean data
    raw_data = data_cleaner.load_data()
    cleaned_data = data_cleaner.standardize_data()
    
    print(f"✅ Loaded {len(cleaned_data)} total responses")
    print(f"📊 Participants: {cleaned_data['pid'].nunique()}")
    print(f"📊 Versions: {cleaned_data['version'].value_counts().to_dict()}")
    
    # Create export directory
    export_dir = Path("exports")
    export_dir.mkdir(exist_ok=True)
    
    # 1. Export all individual responses (cleaned data)
    print("\n📁 Exporting individual responses...")
    individual_file = export_dir / f"individual_responses_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    
    # Select key columns for analysis
    export_columns = [
        'pid', 'face_id', 'version', 'trust_rating', 'emotion_rating',
        'fem_choice', 'femininity_full', 'masc_choice', 'masculinity_full'
    ]
    
    # Filter to only include columns that exist
    available_columns = [col for col in export_columns if col in cleaned_data.columns]
    individual_data = cleaned_data[available_columns].copy()
    
    # Add metadata
    individual_data['export_timestamp'] = datetime.now().isoformat()
    individual_data['data_source'] = 'Face Perception Study Dashboard'
    
    individual_data.to_csv(individual_file, index=False)
    print(f"✅ Individual responses exported to: {individual_file}")
    
    # 2. Export trust ratings by version for verification
    print("\n📁 Exporting trust ratings by version...")
    trust_file = export_dir / f"trust_ratings_by_version_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    
    trust_data = []
    for version in ['left', 'right', 'both']:
        version_data = cleaned_data[cleaned_data['version'] == version]
        if len(version_data) > 0:
            trust_ratings = version_data['trust_rating'].dropna()
            trust_data.append({
                'version': version,
                'n': len(trust_ratings),
                'mean': trust_ratings.mean(),
                'std': trust_ratings.std(),
                'median': trust_ratings.median(),
                'min': trust_ratings.min(),
                'max': trust_ratings.max(),
                'q25': trust_ratings.quantile(0.25),
                'q75': trust_ratings.quantile(0.75)
            })
    
    trust_df = pd.DataFrame(trust_data)
    trust_df.to_csv(trust_file, index=False)
    print(f"✅ Trust ratings by version exported to: {trust_file}")
    
    # 3. Export participant-level data for paired tests
    print("\n📁 Exporting participant-level data...")
    participant_file = export_dir / f"participant_level_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    
    participant_data = []
    for pid in cleaned_data['pid'].unique():
        participant_df = cleaned_data[cleaned_data['pid'] == pid]
        
        # Calculate means for each version
        left_mean = participant_df[participant_df['version'] == 'left']['trust_rating'].mean()
        right_mean = participant_df[participant_df['version'] == 'right']['trust_rating'].mean()
        both_mean = participant_df[participant_df['version'] == 'both']['trust_rating'].mean()
        
        participant_data.append({
            'pid': pid,
            'left_mean': left_mean if not pd.isna(left_mean) else None,
            'right_mean': right_mean if not pd.isna(right_mean) else None,
            'both_mean': both_mean if not pd.isna(both_mean) else None,
            'half_face_mean': (left_mean + right_mean) / 2 if not pd.isna(left_mean) and not pd.isna(right_mean) else None,
            'total_responses': len(participant_df),
            'left_responses': len(participant_df[participant_df['version'] == 'left']),
            'right_responses': len(participant_df[participant_df['version'] == 'right']),
            'both_responses': len(participant_df[participant_df['version'] == 'both'])
        })
    
    participant_df = pd.DataFrame(participant_data)
    participant_df.to_csv(participant_file, index=False)
    print(f"✅ Participant-level data exported to: {participant_file}")
    
    # 4. Export summary statistics
    print("\n📁 Exporting summary statistics...")
    summary_file = export_dir / f"summary_statistics_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    
    summary_data = {
        'metric': [
            'Total Participants',
            'Total Responses',
            'Left Responses',
            'Right Responses', 
            'Both Responses',
            'Overall Mean Trust Rating',
            'Overall Std Trust Rating',
            'Left Mean Trust Rating',
            'Right Mean Trust Rating',
            'Both Mean Trust Rating'
        ],
        'value': [
            cleaned_data['pid'].nunique(),
            len(cleaned_data),
            len(cleaned_data[cleaned_data['version'] == 'left']),
            len(cleaned_data[cleaned_data['version'] == 'right']),
            len(cleaned_data[cleaned_data['version'] == 'both']),
            cleaned_data['trust_rating'].mean(),
            cleaned_data['trust_rating'].std(),
            cleaned_data[cleaned_data['version'] == 'left']['trust_rating'].mean(),
            cleaned_data[cleaned_data['version'] == 'right']['trust_rating'].mean(),
            cleaned_data[cleaned_data['version'] == 'both']['trust_rating'].mean()
        ]
    }
    
    summary_df = pd.DataFrame(summary_data)
    summary_df.to_csv(summary_file, index=False)
    print(f"✅ Summary statistics exported to: {summary_file}")
    
    print(f"\n🎉 All exports completed! Files saved in: {export_dir}")
    print("\nFiles created:")
    print(f"  - {individual_file.name} (Individual responses for detailed analysis)")
    print(f"  - {trust_file.name} (Trust ratings by version)")
    print(f"  - {participant_file.name} (Participant-level means for paired tests)")
    print(f"  - {summary_file.name} (Summary statistics)")

if __name__ == "__main__":
    export_individual_responses()
