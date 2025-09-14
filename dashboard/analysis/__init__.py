"""
Analysis package for the Facial Trust Study dashboard.
This package contains modules for data cleaning, filtering, and statistical analysis.
"""

# Import key components to make them available at the package level
from .cleaning import DataCleaner
from .filters import DataFilter
from .stats import StatisticalAnalyzer
from .long_format_processor import LongFormatProcessor
# from .statistical_models import AdvancedStatisticalModels  # Temporarily disabled due to scipy error

# For backward compatibility
process_long_format_data = LongFormatProcessor

def run_statistical_models(*args, **kwargs):
    """Backward compatibility wrapper for AdvancedStatisticalModels.
    
    This function creates an instance of AdvancedStatisticalModels and runs the analysis.
    """
    # analyzer = AdvancedStatisticalModels()  # Temporarily disabled
    # return analyzer.analyze(*args, **kwargs)
    return None  # Placeholder

__all__ = [
    'DataCleaner',
    'DataFilter',
    'StatisticalAnalyzer',
    'LongFormatProcessor',
    # 'AdvancedStatisticalModels',  # Temporarily disabled
    'process_long_format_data',  # For backward compatibility
    'run_statistical_models'    # For backward compatibility
]
