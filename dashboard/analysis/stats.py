import pandas as pd
import numpy as np
from scipy import stats
from scipy.stats import pearsonr, spearmanr
from typing import Dict, List, Tuple, Optional
import logging

logger = logging.getLogger(__name__)

class StatisticalAnalyzer:
    """
    Statistical analysis for face perception study data.
    """
    
    def __init__(self, data_cleaner):
        self.data_cleaner = data_cleaner
        self.cleaned_data = data_cleaner.get_cleaned_data()
    
    def get_descriptive_stats(self) -> Dict:
        """
        Get descriptive statistics for trust ratings by version.
        """
        stats_dict = {}
        
        for version in ['left', 'right', 'full']:
            version_data = self.data_cleaner.get_data_by_version(version)
            
            if len(version_data) > 0:
                trust_ratings = version_data['trust_rating'].dropna()
                
                stats_dict[version] = {
                    'n': len(trust_ratings),
                    'mean': trust_ratings.mean(),
                    'std': trust_ratings.std(),
                    'median': trust_ratings.median(),
                    'min': trust_ratings.min(),
                    'max': trust_ratings.max(),
                    'q25': trust_ratings.quantile(0.25),
                    'q75': trust_ratings.quantile(0.75)
                }
            else:
                stats_dict[version] = {
                    'n': 0, 'mean': np.nan, 'std': np.nan, 'median': np.nan,
                    'min': np.nan, 'max': np.nan, 'q25': np.nan, 'q75': np.nan
                }
        
        return stats_dict
    
    def paired_t_test_half_vs_full(self) -> Dict:
        """
        Paired t-test comparing half-face (left/right average) vs full-face ratings.
        Returns t, p, df, Cohen's d (paired), mean difference and 95% CI, and included participant IDs.
        """
        # Get data for each version
        left_data = self.data_cleaner.get_data_by_version('left')
        right_data = self.data_cleaner.get_data_by_version('right')
        full_data = self.data_cleaner.get_data_by_version('full')
        
        # Create participant-level averages
        left_means = left_data.groupby('pid')['trust_rating'].mean()
        right_means = right_data.groupby('pid')['trust_rating'].mean()
        full_means = full_data.groupby('pid')['trust_rating'].mean()
        
        # Calculate half-face average (left + right) / 2
        half_face_means = pd.concat([left_means, right_means], axis=1).mean(axis=1)
        
        # Align data for paired test
        common_participants = half_face_means.index.intersection(full_means.index)
        n = len(common_participants)
        if n < 2:
            return {
                'statistic': np.nan,
                'pvalue': np.nan,
                'effect_size': np.nan,
                'df': n - 1 if n > 0 else np.nan,
                'n_participants': n,
                'half_face_mean': np.nan,
                'full_face_mean': np.nan,
                'difference': np.nan,
                'ci_lower': np.nan,
                'ci_upper': np.nan,
                'included_participants': list(common_participants),
                'error': 'Insufficient data for paired t-test'
            }
        
        half_face_values = half_face_means.loc[common_participants]
        full_face_values = full_means.loc[common_participants]
        
        # Perform paired t-test
        t_stat, p_value = stats.ttest_rel(half_face_values, full_face_values)
        
        # Paired differences
        diffs = (half_face_values - full_face_values).astype(float)
        mean_diff = float(diffs.mean())
        sd_diff = float(diffs.std(ddof=1))
        df_val = n - 1
        se_diff = sd_diff / np.sqrt(n) if n > 0 else np.nan
        
        # Cohen's d for paired samples (mean of diffs / sd of diffs)
        effect_size = mean_diff / sd_diff if sd_diff > 0 else np.nan
        
        # 95% CI for mean difference
        t_crit = stats.t.ppf(0.975, df_val) if df_val > 0 else np.nan
        ci_lower = mean_diff - t_crit * se_diff if np.isfinite(t_crit) else np.nan
        ci_upper = mean_diff + t_crit * se_diff if np.isfinite(t_crit) else np.nan
        
        return {
            'statistic': float(t_stat),
            'pvalue': float(p_value),
            'effect_size': float(effect_size) if np.isfinite(effect_size) else np.nan,
            'df': int(df_val),
            'n_participants': int(n),
            'half_face_mean': float(half_face_values.mean()),
            'full_face_mean': float(full_face_values.mean()),
            'difference': float(mean_diff),
            'ci_lower': float(ci_lower) if np.isfinite(ci_lower) else np.nan,
            'ci_upper': float(ci_upper) if np.isfinite(ci_upper) else np.nan,
            'included_participants': list(map(str, common_participants))
        }
    
    def repeated_measures_anova(self) -> Dict:
        """
        One-way repeated measures ANOVA across versions (left, right, full).
        Returns F, p, df_num, df_den, partial eta-squared, means/sds, and included participant IDs.
        """
        # Get data for each version
        left_data = self.data_cleaner.get_data_by_version('left')
        right_data = self.data_cleaner.get_data_by_version('right')
        full_data = self.data_cleaner.get_data_by_version('full')
        
        # Create participant-level averages
        left_means = left_data.groupby('pid')['trust_rating'].mean()
        right_means = right_data.groupby('pid')['trust_rating'].mean()
        full_means = full_data.groupby('pid')['trust_rating'].mean()
        
        # Find common participants across all versions
        common_participants = left_means.index.intersection(right_means.index).intersection(full_means.index)
        n = len(common_participants)
        k = 3
        if n < 2:
            return {
                'f_statistic': np.nan,
                'pvalue': np.nan,
                'effect_size': np.nan,
                'df_num': np.nan,
                'df_den': np.nan,
                'n_participants': n,
                'means': {},
                'stds': {},
                'included_participants': list(common_participants),
                'error': 'Insufficient data for repeated measures ANOVA'
            }
        
        # Data matrix (n x k)
        data_matrix = pd.DataFrame({
            'left': left_means.loc[common_participants],
            'right': right_means.loc[common_participants],
            'full': full_means.loc[common_participants]
        })
        
        # Compute repeated-measures ANOVA components
        grand_mean = data_matrix.values.mean()
        condition_means = data_matrix.mean(axis=0)
        subject_means = data_matrix.mean(axis=1)
        
        # Sums of squares
        ss_conditions = n * ((condition_means - grand_mean) ** 2).sum()
        ss_subjects = k * ((subject_means - grand_mean) ** 2).sum()
        ss_total = ((data_matrix - grand_mean) ** 2).values.sum()
        ss_error = ss_total - ss_conditions - ss_subjects
        
        # Degrees of freedom
        df_num = k - 1
        df_den = (k - 1) * (n - 1)
        
        if df_den <= 0 or ss_error <= 0:
            return {
                'f_statistic': np.nan,
                'pvalue': np.nan,
                'effect_size': np.nan,
                'df_num': df_num,
                'df_den': df_den,
                'n_participants': n,
                'means': condition_means.to_dict(),
                'stds': data_matrix.std(axis=0, ddof=1).to_dict(),
                'included_participants': list(map(str, common_participants)),
                'error': 'Insufficient variance for ANOVA'
            }
        
        ms_conditions = ss_conditions / df_num
        ms_error = ss_error / df_den
        f_stat = ms_conditions / ms_error if ms_error > 0 else np.nan
        p_value = stats.f.sf(f_stat, df_num, df_den) if np.isfinite(f_stat) else np.nan
        
        # Partial eta-squared
        partial_eta_sq = ss_conditions / (ss_conditions + ss_error) if (ss_conditions + ss_error) > 0 else np.nan
        
        return {
            'f_statistic': float(f_stat) if np.isfinite(f_stat) else np.nan,
            'pvalue': float(p_value) if np.isfinite(p_value) else np.nan,
            'effect_size': float(partial_eta_sq) if np.isfinite(partial_eta_sq) else np.nan,
            'df_num': int(df_num),
            'df_den': int(df_den),
            'n_participants': int(n),
            'means': {k: float(v) for k, v in condition_means.items()},
            'stds': {k: float(v) for k, v in data_matrix.std(axis=0, ddof=1).items()},
            'included_participants': list(map(str, common_participants))
        }
    
    def inter_rater_reliability(self) -> Dict:
        """
        Calculate inter-rater reliability (ICC) for trust ratings.
        """
        # Get data for full face only (most reliable for inter-rater reliability)
        full_data = self.data_cleaner.get_data_by_version('full')
        
        if len(full_data) == 0:
            return {
                'icc': np.nan,
                'n_raters': 0,
                'n_stimuli': 0,
                'error': 'No full face data available'
            }
        
        # Group by face_id and calculate ICC
        face_col = 'image_id' if 'image_id' in full_data.columns else 'face_id'
        trust_col = 'trust' if 'trust' in full_data.columns else 'trust_rating'
        face_ratings = full_data.groupby(face_col)[trust_col].apply(list)
        
        # Filter faces with multiple ratings
        face_ratings = face_ratings[face_ratings.apply(len) > 1]
        
        if len(face_ratings) < 2:
            return {
                'icc': np.nan,
                'n_raters': 0,
                'n_stimuli': len(face_ratings),
                'error': 'Insufficient data for ICC calculation'
            }
        
        # Calculate ICC (simplified version)
        try:
            # Create rating matrix
            max_ratings = max(len(ratings) for ratings in face_ratings)
            rating_matrix = []
            
            for ratings in face_ratings:
                # Pad with NaN if needed
                padded_ratings = ratings + [np.nan] * (max_ratings - len(ratings))
                rating_matrix.append(padded_ratings)
            
            rating_matrix = np.array(rating_matrix)
            
            # Calculate ICC (type 1,1 - single score, absolute agreement)
            icc = self._calculate_icc(rating_matrix)
            
            return {
                'icc': icc,
                'n_raters': max_ratings,
                'n_stimuli': len(face_ratings),
                'mean_ratings_per_stimulus': np.mean([len(ratings) for ratings in face_ratings])
            }
        except Exception as e:
            logger.error(f"Error calculating ICC: {e}")
            return {
                'icc': np.nan,
                'n_raters': 0,
                'n_stimuli': len(face_ratings),
                'error': str(e)
            }
    
    def _calculate_icc(self, data_matrix: np.ndarray) -> float:
        """
        Calculate Intraclass Correlation Coefficient (ICC).
        """
        # Remove rows with all NaN
        data_matrix = data_matrix[~np.all(np.isnan(data_matrix), axis=1)]
        
        if data_matrix.shape[0] < 2 or data_matrix.shape[1] < 2:
            return np.nan
        
        # Calculate means
        grand_mean = np.nanmean(data_matrix)
        row_means = np.nanmean(data_matrix, axis=1)
        col_means = np.nanmean(data_matrix, axis=0)
        
        # Calculate sums of squares
        n_rows, n_cols = data_matrix.shape
        
        # Total SS
        ss_total = np.nansum((data_matrix - grand_mean) ** 2)
        
        # Between-subjects SS
        ss_between = n_cols * np.nansum((row_means - grand_mean) ** 2)
        
        # Between-raters SS
        ss_raters = n_rows * np.nansum((col_means - grand_mean) ** 2)
        
        # Error SS
        ss_error = ss_total - ss_between - ss_raters
        
        # Degrees of freedom
        df_between = n_rows - 1
        df_raters = n_cols - 1
        df_error = (n_rows - 1) * (n_cols - 1)
        
        # Mean squares
        ms_between = ss_between / df_between if df_between > 0 else 0
        ms_raters = ss_raters / df_raters if df_raters > 0 else 0
        ms_error = ss_error / df_error if df_error > 0 else 0
        
        # ICC (type 1,1 - single score, absolute agreement)
        if ms_error > 0:
            icc = (ms_between - ms_error) / (ms_between + (n_cols - 1) * ms_error)
        else:
            icc = 1.0 if ms_between > 0 else 0.0
        
        return max(0, min(1, icc))  # Clamp between 0 and 1
    
    def split_half_reliability(self) -> Dict:
        """
        Calculate split-half reliability for trust ratings.
        """
        # Get data for full face only
        full_data = self.data_cleaner.get_data_by_version('full')
        
        if len(full_data) == 0:
            return {
                'split_half_correlation': np.nan,
                'spearman_brown': np.nan,
                'n_participants': 0,
                'error': 'No full face data available'
            }
        
        # Group by participant and face_id to get complete ratings
        participant_face_ratings = full_data.groupby(['pid', 'face_id'])['trust_rating'].first().reset_index()
        
        # Pivot to get participants as rows and faces as columns
        rating_matrix = participant_face_ratings.pivot(index='pid', columns='face_id', values='trust_rating')
        
        # Remove participants with too many missing values
        min_faces = rating_matrix.shape[1] * 0.5  # At least 50% of faces
        rating_matrix = rating_matrix.dropna(thresh=min_faces)
        
        if rating_matrix.shape[0] < 2:
            return {
                'split_half_correlation': np.nan,
                'spearman_brown': np.nan,
                'n_participants': 0,
                'error': 'Insufficient data for split-half reliability'
            }
        
        # Split faces into two halves
        n_faces = rating_matrix.shape[1]
        half_size = n_faces // 2
        
        # Randomly split faces
        np.random.seed(42)  # For reproducibility
        face_indices = np.random.permutation(n_faces)
        half1_indices = face_indices[:half_size]
        half2_indices = face_indices[half_size:]
        
        half1_scores = rating_matrix.iloc[:, half1_indices].mean(axis=1)
        half2_scores = rating_matrix.iloc[:, half2_indices].mean(axis=1)
        
        # Calculate correlation
        valid_mask = ~(half1_scores.isna() | half2_scores.isna())
        if valid_mask.sum() < 2:
            return {
                'split_half_correlation': np.nan,
                'spearman_brown': np.nan,
                'n_participants': 0,
                'error': 'Insufficient valid data for correlation'
            }
        
        correlation, _ = pearsonr(half1_scores[valid_mask], half2_scores[valid_mask])
        
        # Spearman-Brown correction
        spearman_brown = (2 * correlation) / (1 + correlation) if correlation != 1 else 1
        
        return {
            'split_half_correlation': correlation,
            'spearman_brown': spearman_brown,
            'n_participants': valid_mask.sum(),
            'n_faces_per_half': half_size
        }
    
    def get_image_summary(self) -> pd.DataFrame:
        """
        Get summary statistics for each image across versions.
        Shows all 35 faces in the study, even if they don't have data yet.
        """
        # Handle empty data case
        if self.cleaned_data.empty:
            # Return empty dataframe with all faces and all expected columns
            all_face_ids = [f'face_{i}' for i in range(1, 36)]  # face_1 through face_35
            return pd.DataFrame({
                'face_id': all_face_ids,
                'mean_trust': [0.0] * 35,  # Use 0.0 instead of np.nan
                'half_face_avg': [0.0] * 35,  # Use 0.0 instead of np.nan
                'full_minus_half_diff': [0.0] * 35,  # Use 0.0 instead of np.nan
                'rating_count': [0] * 35,
                'unique_participants': [0] * 35,
                'std_trust': [0.0] * 35  # Use 0.0 instead of np.nan
            })
        
        cleaned_data = self.cleaned_data[self.cleaned_data['include_in_primary']]
        
        # Get the actual face_id values from the data
        actual_face_ids = sorted(cleaned_data['face_id'].unique())
        # For display purposes, create a mapping to face_1, face_2, etc.
        face_id_mapping = {face_id: f'face_{i+1}' for i, face_id in enumerate(actual_face_ids)}
        all_face_ids = list(face_id_mapping.values())
        
        # Group by face_id and version for faces that have data
        image_summary = cleaned_data.groupby(['face_id', 'version']).agg({
            'trust_rating': ['count', 'mean', 'std'],
            'pid': 'nunique'
        }).round(3)
        
        # Flatten column names
        image_summary.columns = ['rating_count', 'mean_trust', 'std_trust', 'unique_participants']
        image_summary = image_summary.reset_index()
        
        # Map actual face_id values to display format
        image_summary['display_face_id'] = image_summary['face_id'].map(face_id_mapping)
        
        # Calculate difference between full face and half-face average
        full_face_data = image_summary[image_summary['version'] == 'full'].set_index('display_face_id')
        half_face_data = image_summary[image_summary['version'].isin(['left', 'right'])]
        
        if not half_face_data.empty:
            half_face_avg = (
                half_face_data.groupby('display_face_id').agg({
                    'mean_trust': 'mean',
                    'rating_count': 'sum',
                    'unique_participants': 'sum'
                })
                .rename(columns={'mean_trust': 'half_face_avg',
                                 'rating_count': 'half_rating_count',
                                 'unique_participants': 'half_unique_participants'})
            )
            
            # Merge and calculate difference
            comparison = full_face_data.merge(half_face_avg, left_index=True, right_index=True, how='outer')
            comparison['full_minus_half_diff'] = comparison['mean_trust'] - comparison['half_face_avg']
            # Create unified counts for template
            comparison['rating_count'] = comparison.get('rating_count', 0).fillna(0) + comparison.get('half_rating_count', 0).fillna(0)
            comparison['unique_participants'] = comparison.get('unique_participants', 0).fillna(0) + comparison.get('half_unique_participants', 0).fillna(0)
            
            # Add all faces to the result, even if they don't have data
            result = comparison.reset_index()
            # Drop the original face_id column and rename display_face_id to face_id
            if 'face_id' in result.columns:
                result = result.drop(columns=['face_id'])
            result = result.rename(columns={'display_face_id': 'face_id'})
            
            # Create a complete dataframe with all faces
            complete_faces = pd.DataFrame({'face_id': all_face_ids})
            
            # Merge with existing data, keeping all faces
            final_result = complete_faces.merge(result, on='face_id', how='left')
            
            # Fill NaN values for faces without data
            final_result = final_result.fillna({
                'mean_trust': 0.0,  # Use 0.0 instead of np.nan
                'half_face_avg': 0.0,  # Use 0.0 instead of np.nan
                'full_minus_half_diff': 0.0,  # Use 0.0 instead of np.nan
                'rating_count': 0,
                'unique_participants': 0,
                'std_trust': 0.0  # Use 0.0 instead of np.nan
            })
            
            return final_result
        
        # If no half-face data, still return all faces
        if not full_face_data.empty:
            result = full_face_data.reset_index()
            # Drop the original face_id column and rename display_face_id to face_id
            if 'face_id' in result.columns:
                result = result.drop(columns=['face_id'])
            result = result.rename(columns={'display_face_id': 'face_id'})
            complete_faces = pd.DataFrame({'face_id': all_face_ids})
            final_result = complete_faces.merge(result, on='face_id', how='left')
            final_result = final_result.fillna({
                'mean_trust': 0.0,  # Use 0.0 instead of np.nan
                'rating_count': 0,
                'unique_participants': 0,
                'std_trust': 0.0  # Use 0.0 instead of np.nan
            })
            return final_result
        
        # If no data at all, return empty dataframe with all faces and all expected columns
        num_faces = len(all_face_ids)
        return pd.DataFrame({
            'face_id': all_face_ids,
            'mean_trust': [0.0] * num_faces,  # Use 0.0 instead of np.nan
            'half_face_avg': [0.0] * num_faces,  # Use 0.0 instead of np.nan
            'full_minus_half_diff': [0.0] * num_faces,  # Use 0.0 instead of np.nan
            'rating_count': [0] * num_faces,
            'unique_participants': [0] * num_faces,
            'std_trust': [0.0] * num_faces  # Use 0.0 instead of np.nan
        })
    
    def run_all_analyses(self) -> Dict:
        """
        Run all statistical analyses and return comprehensive results.
        """
        results = {
            'descriptive_stats': self.get_descriptive_stats(),
            'paired_t_test': self.paired_t_test_half_vs_full(),
            'repeated_measures_anova': self.repeated_measures_anova(),
            'inter_rater_reliability': self.inter_rater_reliability(),
            'split_half_reliability': self.split_half_reliability(),
            'image_summary': self.get_image_summary().to_dict('records'),
            'exclusion_summary': self.data_cleaner.get_exclusion_summary()
        }
        
        return results
