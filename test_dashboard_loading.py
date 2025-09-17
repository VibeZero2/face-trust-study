#!/usr/bin/env python3
"""
Test dashboard loading with long-format data
"""

import sys
sys.path.append('.')
sys.path.append('dashboard')

from dashboard.analysis.cleaning import DataCleaner

def test_dashboard_loading():
    print('Testing dashboard with new long-format data...')
    
    try:
        cleaner = DataCleaner()
        cleaner.load_data()
        cleaned_data = cleaner.get_cleaned_data()
        
        print(f'Total rows loaded: {len(cleaned_data)}')
        print(f'Columns: {list(cleaned_data.columns)}')
        
        if 'pid' in cleaned_data.columns:
            print(f'Unique participants: {cleaned_data["pid"].nunique()}')
        
        if 'face_id' in cleaned_data.columns:
            print(f'Unique faces: {cleaned_data["face_id"].nunique()}')
        
        if len(cleaned_data) > 0:
            print('\nSample data:')
            print(cleaned_data.head(10).to_string())
            
            # Test specific long-format structure
            if 'question' in cleaned_data.columns and 'response' in cleaned_data.columns:
                print('\nQuestion types found:')
                print(cleaned_data['question'].value_counts())
                
                print('\nVersion breakdown:')
                print(cleaned_data['version'].value_counts())
                
        return True
        
    except Exception as e:
        print(f'Error loading dashboard data: {e}')
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_dashboard_loading()
