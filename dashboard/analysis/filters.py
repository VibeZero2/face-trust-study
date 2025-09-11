import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Union
import logging

logger = logging.getLogger(__name__)

class DataFilter:
    """
    Data filtering utilities for the face perception study dashboard.
    """
    
    def __init__(self, data_cleaner):
        self.data_cleaner = data_cleaner
        self.cleaned_data = data_cleaner.get_cleaned_data()
    
    def apply_filters(self, 
                     date_range: Optional[Dict] = None,
                     device_filter: Optional[List[str]] = None,
                     country_filter: Optional[List[str]] = None,
                     age_group_filter: Optional[List[str]] = None,
                     phase_filter: Optional[List[str]] = None,
                     stimulus_set_filter: Optional[List[str]] = None,
                     include_excluded: bool = False,
                     **kwargs) -> pd.DataFrame:
        """
        Apply multiple filters to the cleaned data.
        
        Args:
            date_range: Dict with 'start' and 'end' dates
            device_filter: List of device types to include
            country_filter: List of countries to include
            age_group_filter: List of age groups to include
            phase_filter: List of phases/versions to include
            stimulus_set_filter: List of stimulus sets to include
            include_excluded: Whether to include excluded trials
            **kwargs: Additional filter parameters
        
        Returns:
            Filtered DataFrame
        """
        filtered_data = self.cleaned_data.copy()
        
        # Apply inclusion filter
        if not include_excluded:
            filtered_data = filtered_data[filtered_data['include_in_primary']]
        
        # Date range filter
        if date_range:
            filtered_data = self._filter_by_date_range(filtered_data, date_range)
        
        # Device filter
        if device_filter and 'device' in filtered_data.columns:
            filtered_data = filtered_data[filtered_data['device'].isin(device_filter)]
        
        # Country filter
        if country_filter and 'country' in filtered_data.columns:
            filtered_data = filtered_data[filtered_data['country'].isin(country_filter)]
        
        # Age group filter
        if age_group_filter and 'age_group' in filtered_data.columns:
            filtered_data = filtered_data[filtered_data['age_group'].isin(age_group_filter)]
        
        # Phase/version filter
        if phase_filter:
            filtered_data = filtered_data[filtered_data['version'].isin(phase_filter)]
        
        # Stimulus set filter
        if stimulus_set_filter and 'stimulus_set' in filtered_data.columns:
            filtered_data = filtered_data[filtered_data['stimulus_set'].isin(stimulus_set_filter)]
        
        # Additional custom filters
        for key, value in kwargs.items():
            if key in filtered_data.columns:
                if isinstance(value, list):
                    filtered_data = filtered_data[filtered_data[key].isin(value)]
                else:
                    filtered_data = filtered_data[filtered_data[key] == value]
        
        return filtered_data
    
    def _filter_by_date_range(self, data: pd.DataFrame, date_range: Dict) -> pd.DataFrame:
        """
        Filter data by date range.
        """
        if 'timestamp' not in data.columns:
            return data
        
        start_date = date_range.get('start')
        end_date = date_range.get('end')
        
        if start_date:
            if isinstance(start_date, str):
                start_date = pd.to_datetime(start_date)
            data = data[data['timestamp'] >= start_date]
        
        if end_date:
            if isinstance(end_date, str):
                end_date = pd.to_datetime(end_date)
            data = data[data['timestamp'] <= end_date]
        
        return data
    
    def get_available_filters(self) -> Dict:
        """
        Get available filter options from the data.
        """
        filters = {}
        
        # Date range
        if 'timestamp' in self.cleaned_data.columns:
            timestamps = pd.to_datetime(self.cleaned_data['timestamp'], errors='coerce')
            valid_timestamps = timestamps.dropna()
            if len(valid_timestamps) > 0:
                filters['date_range'] = {
                    'min_date': valid_timestamps.min().strftime('%Y-%m-%d'),
                    'max_date': valid_timestamps.max().strftime('%Y-%m-%d')
                }
        
        # Device types
        if 'device' in self.cleaned_data.columns:
            filters['devices'] = sorted(self.cleaned_data['device'].dropna().unique().tolist())
        
        # Countries
        if 'country' in self.cleaned_data.columns:
            filters['countries'] = sorted(self.cleaned_data['country'].dropna().unique().tolist())
        
        # Age groups
        if 'age_group' in self.cleaned_data.columns:
            filters['age_groups'] = sorted(self.cleaned_data['age_group'].dropna().unique().tolist())
        
        # Phases/versions
        filters['phases'] = sorted(self.cleaned_data['version'].dropna().unique().tolist())
        
        # Stimulus sets
        if 'stimulus_set' in self.cleaned_data.columns:
            filters['stimulus_sets'] = sorted(self.cleaned_data['stimulus_set'].dropna().unique().tolist())
        
        # Face IDs
        filters['face_ids'] = sorted(self.cleaned_data['face_id'].dropna().unique().tolist())
        
        return filters
    
    def get_filter_summary(self, filtered_data: pd.DataFrame) -> Dict:
        """
        Get summary statistics for filtered data.
        """
        summary = {
            'total_trials': len(filtered_data),
            'unique_participants': filtered_data['participant_id'].nunique(),
            'unique_faces': filtered_data['face_id'].nunique(),
            'versions': filtered_data['version'].value_counts().to_dict(),
            'date_range': None,
            'exclusion_breakdown': {}
        }
        
        # Date range
        if 'timestamp' in filtered_data.columns:
            timestamps = pd.to_datetime(filtered_data['timestamp'], errors='coerce')
            valid_timestamps = timestamps.dropna()
            if len(valid_timestamps) > 0:
                summary['date_range'] = {
                    'start': valid_timestamps.min().strftime('%Y-%m-%d'),
                    'end': valid_timestamps.max().strftime('%Y-%m-%d')
                }
        
        # Exclusion breakdown
        if 'include_in_primary' in filtered_data.columns:
            summary['exclusion_breakdown'] = {
                'included': filtered_data['include_in_primary'].sum(),
                'excluded': (~filtered_data['include_in_primary']).sum(),
                'exclusion_reasons': {
                    'attention_failed': filtered_data['excl_failed_attention'].sum() if 'excl_failed_attention' in filtered_data.columns else 0,
                    'fast_rt': filtered_data['excl_fast_rt'].sum() if 'excl_fast_rt' in filtered_data.columns else 0,
                    'slow_rt': filtered_data['excl_slow_rt'].sum() if 'excl_slow_rt' in filtered_data.columns else 0,
                    'device_violation': filtered_data['excl_device_violation'].sum() if 'excl_device_violation' in filtered_data.columns else 0
                }
            }
        
        return summary
    
    def create_preset_filters(self) -> Dict:
        """
        Create preset filter configurations for common use cases.
        """
        presets = {
            'all_data': {
                'name': 'All Data',
                'description': 'Include all data with exclusions applied',
                'filters': {'include_excluded': False}
            },
            'raw_data': {
                'name': 'Raw Data',
                'description': 'Include all data without exclusions',
                'filters': {'include_excluded': True}
            },
            'full_face_only': {
                'name': 'Full Face Only',
                'description': 'Only full face ratings',
                'filters': {'phase_filter': ['full'], 'include_excluded': False}
            },
            'half_face_only': {
                'name': 'Half Face Only',
                'description': 'Only half face ratings (left and right)',
                'filters': {'phase_filter': ['left', 'right'], 'include_excluded': False}
            },
            'recent_data': {
                'name': 'Recent Data',
                'description': 'Data from the last 30 days',
                'filters': {
                    'date_range': {
                        'start': (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
                    },
                    'include_excluded': False
                }
            }
        }
        
        return presets
    
    def validate_filters(self, filters: Dict) -> Dict:
        """
        Validate filter parameters and return any issues.
        """
        issues = []
        warnings = []
        
        # Check date range
        if 'date_range' in filters:
            date_range = filters['date_range']
            if 'start' in date_range:
                try:
                    pd.to_datetime(date_range['start'])
                except:
                    issues.append("Invalid start date format")
            
            if 'end' in date_range:
                try:
                    pd.to_datetime(date_range['end'])
                except:
                    issues.append("Invalid end date format")
        
        # Check phase filter
        if 'phase_filter' in filters:
            valid_phases = self.cleaned_data['version'].unique()
            invalid_phases = [p for p in filters['phase_filter'] if p not in valid_phases]
            if invalid_phases:
                issues.append(f"Invalid phases: {invalid_phases}")
        
        # Check device filter
        if 'device_filter' in filters and 'device' in self.cleaned_data.columns:
            valid_devices = self.cleaned_data['device'].dropna().unique()
            invalid_devices = [d for d in filters['device_filter'] if d not in valid_devices]
            if invalid_devices:
                warnings.append(f"Unknown devices: {invalid_devices}")
        
        return {
            'valid': len(issues) == 0,
            'issues': issues,
            'warnings': warnings
        }
