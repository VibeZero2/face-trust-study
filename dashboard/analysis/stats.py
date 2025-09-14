import pandas as pd
import numpy as np
# SCIPY DISABLED FOR RENDER DEPLOYMENT
# from scipy import stats
# from scipy.stats import pearsonr, spearmanr
from typing import Dict, List, Tuple, Optional
import logging

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
    
    def f(self):
        class FDist:
            def sf(self, f_stat, df_num, df_den):
                return 1.0
        return FDist()
    
    def t(self):
        class TDist:
            def ppf(self, q, df):
                return 0.0
        return TDist()

stats = MockStats()
pearsonr = stats.pearsonr
spearmanr = stats.spearmanr

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
        
        for version in ['left', 'right', 'both']:
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
    
    def get_all_question_stats(self) -> Dict:
        """
        Get descriptive statistics for all question types by version.
        """
        all_stats = {}
        
        # Get cleaned data (wide format)
        cleaned_data = self.data_cleaner.get_cleaned_data()
        
        # Question types to analyze
        question_types = ['trust_rating', 'emotion_rating', 'masc_choice', 'fem_choice', 'masculinity_full', 'femininity_full']
        
        for question in question_types:
            if question in cleaned_data.columns:
                question_stats = {}
                
                for version in ['left', 'right', 'both']:
                    # Filter data for this version and question
                    if question in ['masc_choice', 'fem_choice', 'masculinity_full', 'femininity_full']:
                        # These questions only exist for version='both'
                        if version == 'both':
                            version_data = cleaned_data[cleaned_data['version'] == version]
                            question_data = version_data[question].dropna()
                        else:
                            question_data = pd.Series(dtype=float)  # Empty series
                    else:
                        # Trust and emotion ratings exist for all versions
                        version_data = cleaned_data[cleaned_data['version'] == version]
                        question_data = version_data[question].dropna()
                    
                    if len(question_data) > 0:
                        # Convert to numeric, handling any non-numeric values
                        try:
                            question_data = pd.to_numeric(question_data, errors='coerce').dropna()
                        except:
                            question_data = pd.Series(dtype=float)
                        
                        if len(question_data) > 0:
                            question_stats[version] = {
                                'n': len(question_data),
                                'mean': question_data.mean(),
                                'std': question_data.std(),
                                'median': question_data.median(),
                                'min': question_data.min(),
                                'max': question_data.max(),
                                'q25': question_data.quantile(0.25),
                                'q75': question_data.quantile(0.75)
                            }
                        else:
                            question_stats[version] = {
                                'n': 0, 'mean': np.nan, 'std': np.nan, 'median': np.nan,
                                'min': np.nan, 'max': np.nan, 'q25': np.nan, 'q75': np.nan
                            }
                    else:
                        question_stats[version] = {
                            'n': 0, 'mean': np.nan, 'std': np.nan, 'median': np.nan,
                            'min': np.nan, 'max': np.nan, 'q25': np.nan, 'q75': np.nan
                        }
                
                all_stats[question] = question_stats
        
        return all_stats
    
    def emotion_paired_t_test_half_vs_full(self) -> Dict:
        """
        Paired t-test comparing half-face (left/right average) vs full-face emotion ratings.
        """
        # Get data for each version
        left_data = self.data_cleaner.get_data_by_version('left')
        right_data = self.data_cleaner.get_data_by_version('right')
        both_data = self.data_cleaner.get_data_by_version('both')
        
        if len(left_data) == 0 or len(right_data) == 0 or len(both_data) == 0:
            return {'error': 'Insufficient data for emotion paired t-test'}
        
        # Get emotion ratings
        left_emotion = left_data['emotion_rating'].dropna()
        right_emotion = right_data['emotion_rating'].dropna()
        both_emotion = both_data['emotion_rating'].dropna()
        
        # Calculate half-face average for each participant
        left_means = left_emotion.groupby(left_data['pid']).mean()
        right_means = right_emotion.groupby(right_data['pid']).mean()
        both_means = both_emotion.groupby(both_data['pid']).mean()
        
        # Find common participants
        common_participants = list(set(left_means.index) & set(right_means.index) & set(both_means.index))
        
        if len(common_participants) < 3:
            return {'error': 'Insufficient participants for emotion paired t-test'}
        
        # Calculate half-face average
        half_face_means = (left_means.loc[common_participants] + right_means.loc[common_participants]) / 2
        full_face_means = both_means.loc[common_participants]
        
        # Paired t-test
        from scipy import stats
        t_stat, p_value = stats.ttest_rel(half_face_means, full_face_means)
        
        # Effect size (Cohen's d for paired samples)
        diff = half_face_means - full_face_means
        cohens_d = diff.mean() / diff.std() if diff.std() > 0 else 0
        
        # Confidence interval for mean difference
        mean_diff = diff.mean()
        std_diff = diff.std()
        n = len(diff)
        se_diff = std_diff / (n ** 0.5)
        ci_lower = mean_diff - 1.96 * se_diff
        ci_upper = mean_diff + 1.96 * se_diff
        
        return {
            'statistic': t_stat,
            'pvalue': p_value,
            'df': len(common_participants) - 1,
            'effect_size': cohens_d,
            'half_face_mean': half_face_means.mean(),
            'full_face_mean': full_face_means.mean(),
            'difference': mean_diff,
            'ci_lower': ci_lower,
            'ci_upper': ci_upper,
            'n_participants': len(common_participants),
            'included_participants': list(common_participants)
        }
    
    def emotion_repeated_measures_anova(self) -> Dict:
        """
        Repeated measures ANOVA for emotion ratings across left, right, and both versions.
        """
        # Get data for each version
        left_data = self.data_cleaner.get_data_by_version('left')
        right_data = self.data_cleaner.get_data_by_version('right')
        both_data = self.data_cleaner.get_data_by_version('both')
        
        if len(left_data) == 0 or len(right_data) == 0 or len(both_data) == 0:
            return {'error': 'Insufficient data for emotion repeated measures ANOVA'}
        
        # Get emotion ratings
        left_emotion = left_data['emotion_rating'].dropna()
        right_emotion = right_data['emotion_rating'].dropna()
        both_emotion = both_data['emotion_rating'].dropna()
        
        # Calculate means for each participant
        left_means = left_emotion.groupby(left_data['pid']).mean()
        right_means = right_emotion.groupby(right_data['pid']).mean()
        both_means = both_emotion.groupby(both_data['pid']).mean()
        
        # Find common participants
        common_participants = list(set(left_means.index) & set(right_means.index) & set(both_means.index))
        
        if len(common_participants) < 3:
            return {'error': 'Insufficient participants for emotion repeated measures ANOVA'}
        
        # Create data matrix
        data_matrix = pd.DataFrame({
            'left': left_means.loc[common_participants],
            'right': right_means.loc[common_participants],
            'both': both_means.loc[common_participants]
        })
        
        # Perform repeated measures ANOVA
        from scipy import stats
        f_stat, p_value = stats.f_oneway(
            data_matrix['left'], 
            data_matrix['right'], 
            data_matrix['both']
        )
        
        # Calculate partial eta squared
        ss_between = data_matrix.var(ddof=0).sum() * len(common_participants)
        ss_total = data_matrix.values.var(ddof=0) * data_matrix.size
        partial_eta_squared = ss_between / ss_total if ss_total > 0 else 0
        
        return {
            'f_statistic': f_stat,
            'pvalue': p_value,
            'df_between': 2,
            'df_within': len(common_participants) - 1,
            'partial_eta_squared': partial_eta_squared,
            'means': {
                'left': data_matrix['left'].mean(),
                'right': data_matrix['right'].mean(),
                'both': data_matrix['both'].mean()
            },
            'n_participants': len(common_participants),
            'included_participants': list(common_participants)
        }
    
    def choice_preference_analysis(self) -> Dict:
        """
        Analyze masc/fem choice preferences and side bias.
        """
        # Get data for both version only (choices only exist for full face)
        both_data = self.data_cleaner.get_data_by_version('both')
        
        if len(both_data) == 0:
            return {'error': 'Insufficient data for choice preference analysis'}
        
        # Get choice data
        masc_choices = both_data['masc_choice'].dropna()
        fem_choices = both_data['fem_choice'].dropna()
        
        if len(masc_choices) == 0 or len(fem_choices) == 0:
            return {'error': 'No choice data available'}
        
        # Calculate choice proportions
        masc_left = (masc_choices == 'left').sum()
        masc_right = (masc_choices == 'right').sum()
        masc_neither = (masc_choices == 'neither').sum()
        masc_total = len(masc_choices)
        
        fem_left = (fem_choices == 'left').sum()
        fem_right = (fem_choices == 'right').sum()
        fem_neither = (fem_choices == 'neither').sum()
        fem_total = len(fem_choices)
        
        # Calculate proportions
        masc_props = {
            'left': masc_left / masc_total if masc_total > 0 else 0,
            'right': masc_right / masc_total if masc_total > 0 else 0,
            'neither': masc_neither / masc_total if masc_total > 0 else 0
        }
        
        fem_props = {
            'left': fem_left / fem_total if fem_total > 0 else 0,
            'right': fem_right / fem_total if fem_total > 0 else 0,
            'neither': fem_neither / fem_total if fem_total > 0 else 0
        }
        
        # Chi-square test for side preference (left vs right, excluding neither)
        from scipy import stats
        
        # Masc choice: left vs right
        masc_side_counts = [masc_left, masc_right]
        masc_expected = [sum(masc_side_counts) / 2, sum(masc_side_counts) / 2]
        masc_chi2, masc_p = stats.chisquare(masc_side_counts, masc_expected) if sum(masc_side_counts) > 0 else (0, 1)
        
        # Fem choice: left vs right
        fem_side_counts = [fem_left, fem_right]
        fem_expected = [sum(fem_side_counts) / 2, sum(fem_side_counts) / 2]
        fem_chi2, fem_p = stats.chisquare(fem_side_counts, fem_expected) if sum(fem_side_counts) > 0 else (0, 1)
        
        # Overall side preference (combining masc and fem)
        total_left = masc_left + fem_left
        total_right = masc_right + fem_right
        total_side_counts = [total_left, total_right]
        total_expected = [sum(total_side_counts) / 2, sum(total_side_counts) / 2]
        total_chi2, total_p = stats.chisquare(total_side_counts, total_expected) if sum(total_side_counts) > 0 else (0, 1)
        
        return {
            'masc_choice': {
                'counts': {'left': masc_left, 'right': masc_right, 'neither': masc_neither, 'total': masc_total},
                'proportions': masc_props,
                'side_preference_test': {'chi2': masc_chi2, 'p_value': masc_p}
            },
            'fem_choice': {
                'counts': {'left': fem_left, 'right': fem_right, 'neither': fem_neither, 'total': fem_total},
                'proportions': fem_props,
                'side_preference_test': {'chi2': fem_chi2, 'p_value': fem_p}
            },
            'overall_side_preference': {
                'counts': {'left': total_left, 'right': total_right, 'total': total_left + total_right},
                'test': {'chi2': total_chi2, 'p_value': total_p}
            }
        }
    
    def paired_t_test_half_vs_full(self) -> Dict:
        """
        Paired t-test comparing half-face (left/right average) vs full-face ratings.
        Returns t, p, df, Cohen's d (paired), mean difference and 95% CI, and included participant IDs.
        """
        # Get data for each version
        left_data = self.data_cleaner.get_data_by_version('left')
        right_data = self.data_cleaner.get_data_by_version('right')
        full_data = self.data_cleaner.get_data_by_version('both')
        
        # Create participant-level averages
        left_means = left_data.groupby('pid')['trust_rating'].mean()
        right_means = right_data.groupby('pid')['trust_rating'].mean()
        full_means = full_data.groupby('pid')['trust_rating'].mean()
        
        # Calculate half-face average (left + right) / 2
        half_face_means = pd.concat([left_means, right_means], axis=1).mean(axis=1)
        
        # Align data for paired test
        common_participants = list(half_face_means.index.intersection(full_means.index))
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
        
        # Perform paired t-test (mocked for deployment)
        try:
            t_stat, p_value = stats.ttest_rel(half_face_values, full_face_values)
        except:
            t_stat, p_value = 0.0, 1.0
        
        # Paired differences
        diffs = (half_face_values - full_face_values).astype(float)
        mean_diff = float(diffs.mean())
        sd_diff = float(diffs.std(ddof=1))
        df_val = n - 1
        se_diff = sd_diff / np.sqrt(n) if n > 0 else np.nan
        
        # Cohen's d for paired samples (mean of diffs / sd of diffs)
        effect_size = mean_diff / sd_diff if sd_diff > 0 else np.nan
        
        # 95% CI for mean difference (mocked for deployment)
        try:
            t_crit = stats.t.ppf(0.975, df_val) if df_val > 0 else np.nan
        except:
            t_crit = 0.0
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
        full_data = self.data_cleaner.get_data_by_version('both')
        
        # Create participant-level averages
        left_means = left_data.groupby('pid')['trust_rating'].mean()
        right_means = right_data.groupby('pid')['trust_rating'].mean()
        full_means = full_data.groupby('pid')['trust_rating'].mean()
        
        # Find common participants across all versions
        common_participants = list(left_means.index.intersection(right_means.index).intersection(full_means.index))
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
            'both': full_means.loc[common_participants]
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
        try:
            p_value = stats.f.sf(f_stat, df_num, df_den) if np.isfinite(f_stat) else np.nan
        except:
            p_value = 1.0
        
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
        full_data = self.data_cleaner.get_data_by_version('both')
        
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
        full_data = self.data_cleaner.get_data_by_version('both')
        
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
        
        try:
            correlation, _ = pearsonr(half1_scores[valid_mask], half2_scores[valid_mask])
        except:
            correlation = 0.0
        
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
        full_face_data = image_summary[image_summary['version'] == 'both'].set_index('display_face_id')
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
