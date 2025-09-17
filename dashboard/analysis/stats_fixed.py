import pandas as pd
import numpy as np
# SCIPY DISABLED FOR RENDER DEPLOYMENT
# from scipy import stats
# from scipy.stats import pearsonr, spearmanr
from typing import Dict, List, Tuple, Optional
import logging

logger = logging.getLogger(__name__)

# Mock scipy functions for deployment
class MockStats:
    def pearsonr(self, x, y):
        return (0.0, 1.0)  # (correlation, p-value)
    
    def spearmanr(self, x, y):
        return (0.0, 1.0)  # (correlation, p-value)
    
    def ttest_rel(self, x, y):
        return (0.0, 1.0)  # (statistic, p-value)
    
    def f_oneway(self, *args):
        return (0.0, 1.0)  # (F-statistic, p-value)

stats = MockStats()
pearsonr = stats.pearsonr
spearmanr = stats.spearmanr

class StatisticalAnalyzer:
    """
    Statistical analysis for face perception study data.
    Temporarily disabled scipy functions for Render deployment.
    """
    
    def __init__(self, data_cleaner):
        self.data_cleaner = data_cleaner
        self.cleaned_data = data_cleaner.get_cleaned_data()
    
    def get_descriptive_stats(self) -> Dict:
        """Get basic descriptive statistics."""
        try:
            included_data = self.cleaned_data[self.cleaned_data['include_in_primary']]
            
            if len(included_data) == 0:
                return {
                    'total_participants': 0,
                    'total_trials': 0,
                    'mean_trust_rating': 0,
                    'std_trust_rating': 0,
                    'median_trust_rating': 0,
                    'min_trust_rating': 0,
                    'max_trust_rating': 0
                }
            
            # Check if we have long format data (question/response columns)
            if 'question' in included_data.columns and 'response' in included_data.columns:
                # Long format: filter for trust_rating question type
                trust_data = included_data[included_data['question'] == 'trust_rating']['response']
                trust_data = pd.to_numeric(trust_data, errors='coerce')
                trust_data = trust_data.dropna()
                
                if len(trust_data) > 0:
                    mean_val = trust_data.mean()
                    std_val = trust_data.std()
                    median_val = trust_data.median()
                    min_val = trust_data.min()
                    max_val = trust_data.max()
                else:
                    mean_val = std_val = median_val = min_val = max_val = 0
                    
            elif 'trust_rating' in included_data.columns:
                # Wide format: use trust_rating column directly
                trust_data = pd.to_numeric(included_data['trust_rating'], errors='coerce')
                trust_data = trust_data.dropna()
                
                if len(trust_data) > 0:
                    mean_val = trust_data.mean()
                    std_val = trust_data.std()
                    median_val = trust_data.median()
                    min_val = trust_data.min()
                    max_val = trust_data.max()
                else:
                    mean_val = std_val = median_val = min_val = max_val = 0
            else:
                # No trust rating data available
                mean_val = std_val = median_val = min_val = max_val = 0
            
            return {
                'total_participants': included_data['pid'].nunique(),
                'total_trials': len(included_data),
                'mean_trust_rating': mean_val,
                'std_trust_rating': std_val,
                'median_trust_rating': median_val,
                'min_trust_rating': min_val,
                'max_trust_rating': max_val
            }
        except Exception as e:
            logger.error(f"Error calculating descriptive stats: {e}")
            import traceback
            traceback.print_exc()
            return {}
    
    def run_all_analyses(self) -> Dict:
        """Run all statistical analyses - DISABLED for deployment."""
        return {
            'descriptive_stats': self.get_descriptive_stats(),
            'note': 'Advanced statistical analyses temporarily disabled for deployment'
        }
    
    def get_image_summary(self) -> pd.DataFrame:
        """Get summary statistics by image."""
        try:
            included_data = self.cleaned_data[self.cleaned_data['include_in_primary']]
            
            if len(included_data) == 0:
                return pd.DataFrame()
            
            image_summary = included_data.groupby(['face_id', 'version']).agg({
                'trust_rating': ['count', 'mean', 'std'],
                'pid': 'nunique'
            }).round(3)
            
            image_summary.columns = ['rating_count', 'mean_trust', 'std_trust', 'unique_participants']
            return image_summary.reset_index()
            
        except Exception as e:
            logger.error(f"Error calculating image summary: {e}")
            return pd.DataFrame()
    
    # Mock methods for compatibility
    def paired_t_test_half_vs_full(self):
        return {'note': 'Statistical tests disabled for deployment'}
    
    def repeated_measures_anova(self):
        return {'note': 'Statistical tests disabled for deployment'}
    
    def inter_rater_reliability(self):
        return {'note': 'Statistical tests disabled for deployment'}
    
    def split_half_reliability(self):
        return {'note': 'Statistical tests disabled for deployment'}
