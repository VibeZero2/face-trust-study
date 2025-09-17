#!/usr/bin/env python3
"""
Find the exact line causing the dashboard error
"""

import sys
import os
import traceback
sys.path.append('.')
sys.path.append('dashboard')

def test_data_loading():
    """Test data loading to find the comparison error"""
    try:
        from dashboard.analysis.cleaning import DataCleaner
        
        print("Testing DataCleaner...")
        cleaner = DataCleaner()
        
        print("Loading data...")
        cleaner.load_data()
        
        print("Getting cleaned data...")
        cleaned_data = cleaner.get_cleaned_data()
        
        print("Data loaded successfully")
        return True
        
    except Exception as e:
        print(f"ERROR in data loading: {e}")
        traceback.print_exc()
        return False

def test_stats_calculation():
    """Test statistics calculation"""
    try:
        from dashboard.analysis.stats import StatisticalAnalyzer
        from dashboard.analysis.cleaning import DataCleaner
        
        cleaner = DataCleaner()
        cleaner.load_data()
        
        print("Testing StatisticalAnalyzer...")
        analyzer = StatisticalAnalyzer(cleaner.get_cleaned_data())
        
        print("Getting image summary...")
        images = analyzer.get_image_summary()
        
        print("Stats calculation successful")
        return True
        
    except Exception as e:
        print(f"ERROR in stats calculation: {e}")
        traceback.print_exc()
        return False

def test_filters():
    """Test filters"""
    try:
        from dashboard.analysis.filters import FilterManager
        from dashboard.analysis.cleaning import DataCleaner
        
        cleaner = DataCleaner()
        cleaner.load_data()
        
        print("Testing FilterManager...")
        filter_mgr = FilterManager(cleaner.get_cleaned_data())
        
        print("Getting available filters...")
        filters = filter_mgr.get_available_filters()
        
        print("Filters successful")
        return True
        
    except Exception as e:
        print(f"ERROR in filters: {e}")
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("=== Testing Data Loading ===")
    test_data_loading()
    
    print("\n=== Testing Stats Calculation ===")
    test_stats_calculation()
    
    print("\n=== Testing Filters ===")
    test_filters()
