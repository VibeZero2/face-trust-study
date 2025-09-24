import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple, Optional
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def _infer_completed_faces(df) -> int:
    """Heuristic: count faces with recorded responses."""
    if df is None or getattr(df, "empty", True):
        return 0
    if "face_id" not in df.columns:
        return 0
    try:
        counts = df["face_id"].astype(str).value_counts()
        return int((counts > 0).sum())
    except Exception:
        return 0


class DataCleaner:
    """
    Data cleaning and exclusion logic for face perception study data.
    """
    
    def __init__(self, data_dir: str = "data/responses", mode: str = "PRODUCTION"):
        self.data_dir = Path(data_dir)
        self.mode = mode.upper() if mode else "PRODUCTION"
        self.raw_data = None
        self.expected_total_faces = 35
        self.file_metadata: List[Dict] = []
        self.cleaned_data = None
        self.exclusion_summary = {}
    
    @staticmethod
    def _is_test_file(file_name: str) -> bool:
        if not file_name:
            return False
        lowered = file_name.lower()
        if lowered.startswith('test'):
            return True
        separators = ['_test', '-test', ' test']
        if any(sep in lowered for sep in separators):
            return True
        extra_keywords = ['prolific_test', 'testparticipant', 'test_stat', 'testdata']
        return any(keyword in lowered for keyword in extra_keywords)


    def load_data(self) -> pd.DataFrame:
        """Load and merge CSV files from the responses directory respecting the selected mode."""
        csv_files = list(self.data_dir.glob('*.csv'))

        if not csv_files:
            raise FileNotFoundError(f"No CSV files found in {self.data_dir}")

        self.file_metadata: List[Dict] = []
        latest_per_pid: Dict[str, Dict] = {}
        latest_complete: Dict[str, Dict] = {}

        for file_path in csv_files:
            try:
                df = pd.read_csv(file_path)
            except Exception as e:
                logger.error("Error loading %s: %s", file_path, e)
                continue

            participant_id = None
            pid_values = df.get('pid')
            if pid_values is not None and not pid_values.dropna().empty:
                candidate = str(pid_values.dropna().astype(str).iloc[0]).strip()
                if candidate and candidate.upper() not in {'UNKNOWN', 'UNKNOWN_PID', 'NAN'}:
                    participant_id = candidate
            if not participant_id:
                prolific_values = df.get('prolific_pid')
                if prolific_values is not None and not prolific_values.dropna().empty:
                    candidate = str(prolific_values.dropna().astype(str).iloc[0]).strip()
                    if candidate and candidate.upper() not in {'UNKNOWN', 'UNKNOWN_PID', 'NAN'}:
                        participant_id = candidate
            if not participant_id:
                participant_id = file_path.stem.split('_')[0]

            versions = df.get('version')
            if versions is not None:
                normalized_versions = versions.dropna().astype(str).str.lower()
                has_full = normalized_versions.eq('full').any()
            else:
                has_full = False

            completed_faces = _infer_completed_faces(df)
            total_faces = self.expected_total_faces or 35
            progress_percent = (min(completed_faces, total_faces) / total_faces * 100) if total_faces else 0
            is_complete = completed_faces >= total_faces

            first_timestamp = None
            last_timestamp = None
            timestamps = df.get('timestamp')
            if timestamps is not None and not timestamps.dropna().empty:
                parsed_ts = pd.to_datetime(timestamps, errors='coerce').dropna()
                if not parsed_ts.empty:
                    first_timestamp = parsed_ts.min()
                    last_timestamp = parsed_ts.max()

            metadata = {
                'pid': participant_id,
                'name': file_path.name,
                'path': file_path,
                'mtime': file_path.stat().st_mtime,
                'modified_display': datetime.fromtimestamp(file_path.stat().st_mtime).strftime('%Y-%m-%d %H:%M:%S'),
                'is_test': self._is_test_file(file_path.name),
                'complete': is_complete,
                'completed_faces': completed_faces,
                'total_faces': total_faces,
                'progress_percent': progress_percent,
                'row_count': len(df),
                'first_timestamp': first_timestamp,
                'last_timestamp': last_timestamp,
            }

            latest = latest_per_pid.get(participant_id)
            if latest is None or metadata['mtime'] > latest['mtime']:
                latest_per_pid[participant_id] = metadata.copy()

            if metadata['complete']:
                best_complete = latest_complete.get(participant_id)
                if best_complete is None or metadata['mtime'] > best_complete['mtime']:
                    latest_complete[participant_id] = metadata.copy()

        self.file_metadata = list(latest_per_pid.values())

        selection_source = latest_complete if latest_complete else latest_per_pid

        if not selection_source:
            self.raw_data = pd.DataFrame()
            return self.raw_data

        mode = (self.mode or 'PRODUCTION').upper()
        files_to_load: List[Path] = []
        for info in selection_source.values():
            is_test = info.get('is_test', False)
            if mode == 'PRODUCTION' and is_test:
                continue
            if mode == 'TEST' and not is_test:
                continue
            files_to_load.append(info['path'])

        if not files_to_load:
            self.raw_data = pd.DataFrame()
            return self.raw_data

        logger.info("Loading %s files for %s mode", len(files_to_load), mode)

        all_data = []
        for file_path in files_to_load:
            try:
                df = pd.read_csv(file_path)
                df['source_file'] = file_path.name
                all_data.append(df)
            except Exception as e:
                logger.error("Error loading %s: %s", file_path, e)
                continue

        if all_data:
            self.raw_data = pd.concat(all_data, ignore_index=True)
        else:
            self.raw_data = pd.DataFrame()

        return self.raw_data
    def get_data_summary(self) -> Dict:
        """Get summary of currently loaded data."""
        if self.raw_data is None:
            return {"status": "No data loaded"}

        if (
            len(self.raw_data) == 0
            or not hasattr(self.raw_data, 'columns')
            or 'source_file' not in self.raw_data.columns
        ):
            return {
                "mode": self.mode,
                "total_rows": 0,
                "real_participants": 0,
                "test_files": 0,
                "real_files": [],
                "test_files_list": [],
            }

        loaded_files = list(self.raw_data['source_file'].unique())
        test_files = [name for name in loaded_files if self._is_test_file(name)]
        real_files = [name for name in loaded_files if name not in test_files]

        if self.mode == 'TEST':
            visible_participants = test_files
        elif self.mode == 'PRODUCTION':
            visible_participants = real_files
        else:  # ALL
            visible_participants = loaded_files

        return {
            "mode": self.mode,
            "total_rows": len(self.raw_data),
            "real_participants": len(visible_participants),
            "test_files": len(test_files),
            "real_files": real_files,
            "test_files_list": test_files,
        }

    def standardize_data(self) -> pd.DataFrame:
        """
        Standardize data format across different CSV structures.
        Streamlined to handle only the new study program format.
        """
        if self.raw_data is None:
            self.load_data()
        
        df = self.raw_data.copy()
        
        # Handle different column naming conventions
        # Map all data to study program format (pid, face_id, version, trust_rating)
        column_mapping = {
            # Study program uses these exact names - keep them
            'pid': 'pid',
            'face_id': 'face_id', 
            'version': 'version',
            'trust_rating': 'trust_rating',
            'timestamp': 'timestamp',
            'prolific_pid': 'prolific_pid',
            'order_presented': 'order_presented',
            # Map old format to study program format (for backward compatibility)
            'participant_id': 'pid',
            'participant id': 'pid',  # Handle space in column name
            'participantid': 'pid',
            'facenumber': 'face_id',  # Old format uses facenumber
            'face number': 'face_id',  # Handle space in column name
            'image_id': 'face_id',  # New format uses image_id
            'face_view': 'version',  # New format uses face_view
            'face': 'face_id',
            'faceid': 'face_id',
            'faceversion': 'version',  # Old format uses faceversion
            'face version': 'version',  # Handle space in column name
            'trust': 'trust_rating',   # Old format uses trust
            'emotion': 'emotion_rating',
            'masculinity': 'masculinity_rating',
            'femininity': 'femininity_rating',
            'symmetry': 'symmetry_rating',
            # Study program specific mappings
            'masc_choice': 'masc_choice',
            'fem_choice': 'fem_choice',
            # New format with question/response columns
            'question': 'question',
            'response': 'response',
            'trust_q1': 'trust_q1',
            'trust_q2': 'trust_q2', 
            'trust_q3': 'trust_q3',
            'pers_q1': 'pers_q1',
            'pers_q2': 'pers_q2',
            'pers_q3': 'pers_q3',
            'pers_q4': 'pers_q4',
            'pers_q5': 'pers_q5'
        }
        
        # Rename columns that exist
        existing_cols = {k: v for k, v in column_mapping.items() if k in df.columns}
        logger.info(f"Mapping columns: {existing_cols}")
        
        # Rename the columns
        df = df.rename(columns=existing_cols)
        
        # Debug: Check what columns we have after mapping
        logger.info(f"Columns after mapping: {list(df.columns)}")
        
        # Handle new question/response format - keep in long format for correct counting
        if 'question_type' in df.columns and 'response' in df.columns:
            logger.info("Detected question_type/response format - keeping in long format")
            
            # Keep data in long format - don't pivot
            # This preserves the correct response counts (1 face = 10 responses: 2 left + 2 right + 6 both)
            logger.info("Data is in long format - preserving for accurate response counting")
            
            # Ensure we have the expected column names
            # Keep standardized long format names used across the dashboard
            # Ensure columns are exactly: pid, face_id, version, question_type, response, timestamp
            # We already mapped 'question' -> 'question_type' above when needed
            
            # Add a flag to indicate this is long format data
            df['_is_long_format'] = True
            
            logger.info("Successfully processed question/response data in long format")
            logger.info(f"After processing: {len(df)} rows, columns: {list(df.columns)}")
            if 'version' in df.columns:
                logger.info(f"Version counts: {df['version'].value_counts().to_dict()}")
            if 'question_type' in df.columns:
                logger.info(f"Question type counts: {df['question_type'].value_counts().to_dict()}")
        
        # Handle duplicate column names by keeping first occurrence
        if df.columns.duplicated().any():
            logger.info("Handling duplicate columns by keeping first occurrence")
            df = df.loc[:, ~df.columns.duplicated()]
            logger.info("Removed duplicate columns")
        
        # Handle face_id conversion for study program format
        if 'face_id' in df.columns:
            # Convert face_id to string first to handle both string and numeric formats
            df['face_id'] = df['face_id'].astype(str)
            
            # Study program uses 'face_1', 'face_2', etc.
            # Handle "Face ID (25)" format from 200.csv
            face_id_pattern = df['face_id'].str.match(r'Face ID \((\d+)\)', na=False)
            if face_id_pattern.any():
                # Extract the number from "Face ID (25)" and convert to "face_25"
                df.loc[face_id_pattern, 'face_id'] = 'face_' + df.loc[face_id_pattern, 'face_id'].str.extract(r'Face ID \((\d+)\)')[0]
                logger.info("Converted 'Face ID (X)' format to study program format")
            
            # Handle simple numeric face IDs like "1", "2", "3" from old test data
            numeric_pattern = df['face_id'].str.match(r'^\d+$', na=False)
            if numeric_pattern.any():
                # Convert "1" to "face_1", "2" to "face_2", etc.
                df.loc[numeric_pattern, 'face_id'] = 'face_' + df.loc[numeric_pattern, 'face_id']
                logger.info("Converted numeric face IDs to study program format")
            
            # Handle new test data format (face_01, face_02, etc.) - ensure consistent format
            face_xx_pattern = df['face_id'].str.match(r'face_(\d+)$', na=False)
            if face_xx_pattern.any():
                # Convert face_01 to face_1, face_02 to face_2, etc.
                df.loc[face_xx_pattern, 'face_id'] = 'face_' + df.loc[face_xx_pattern, 'face_id'].str.extract(r'face_(\d+)$')[0].astype(int).astype(str)
                logger.info("Converted face_XX format to face_X format")
        
        # Ensure version exists and has data (study program uses 'version')
        if 'faceversion' in df.columns and 'version' in df.columns:
            df['version'] = df['faceversion']
            logger.info("Copied faceversion data to empty version column")
            # Drop the faceversion column since we have version
            df = df.drop(columns=['faceversion'])
            logger.info("Dropped faceversion column after ensuring version has data")
        elif 'faceversion' in df.columns and 'version' not in df.columns:
            # If we only have faceversion, rename it to version
            df = df.rename(columns={'faceversion': 'version'})
            logger.info("Renamed faceversion to version")
        
        # Check for trust data in long format only
        has_trust_data = 'trust_rating' in df.columns
        
        if 'trust' in df.columns and 'trust_rating' in df.columns:
            # Copy trust data to trust_rating if trust_rating is empty
            if df['trust_rating'].isna().all():
                df['trust_rating'] = df['trust']
                logger.info("Copied trust data to empty trust_rating column")
            # Drop the trust column since we have trust_rating
            df = df.drop(columns=['trust'])
            logger.info("Dropped trust column after ensuring trust_rating has data")
        elif 'trust' in df.columns and 'trust_rating' not in df.columns:
            # If we only have trust, rename it to trust_rating
            df = df.rename(columns={'trust': 'trust_rating'})
            logger.info("Renamed trust to trust_rating")
        
        # Log what trust data we have
        if has_trust_data:
            logger.info("Found trust data (trust_rating)")
        if not has_trust_data:
            logger.warning("No trust data found in either toggle or full format")
        

        
        # Ensure required columns exist (long format only)
        required_cols = ['pid', 'face_id', 'version', 'question', 'response']
        
        missing_cols = []
        for col in required_cols:
            if col not in df.columns:
                missing_cols.append(col)
        
        if missing_cols:
            logger.warning(f"Missing required columns: {missing_cols}")
            # Add missing columns with default values
            for col in missing_cols:
                df[col] = None
        
        # Check if we have trust data in long format
        has_trust_data = 'trust_rating' in df.columns
        
        if not has_trust_data:
            logger.warning("No trust rating data found in either toggle or full format")
            # Don't filter out all data, just log the warning
        
        # Standardize version values and filter out toggle/survey rows
        if 'version' in df.columns:
            # Convert to string first, then apply string operations
            df['version'] = df['version'].astype(str).str.strip()
            version_mapping = {
                'left half': 'left',
                'right half': 'right',
                'full face': 'both',
                'both': 'both',
                'left': 'left',
                'right': 'right',
                'full': 'both',
                'Left Half': 'left',
                'Right Half': 'right', 
                'Full Face': 'both'
            }
            # First try exact mapping
            df['version'] = df['version'].map(version_mapping).fillna(df['version'])
            
            # If still have original values, try case-insensitive mapping
            if df['version'].isin(['Left Half', 'Right Half', 'Full Face']).any():
                # Convert to lowercase for mapping
                df['version'] = df['version'].str.lower().map({
                    'left half': 'left',
                    'right half': 'right',
                    'full face': 'both'
                }).fillna(df['version'])
            
            # Keep all versions including toggle, full, both, left, right
            # Only filter out survey rows
            df = df[~df['version'].isin(['survey'])]
            logger.info(f"Filtered out survey rows. Remaining rows: {len(df)}")
        
        # Convert timestamp to datetime
        if 'timestamp' in df.columns:
            df['timestamp'] = pd.to_datetime(df['timestamp'], errors='coerce')
        
        # Convert ratings to numeric (long format only)
        rating_cols = ['trust_rating', 'emotion_rating', 'masculinity_rating', 'femininity_rating', 'symmetry_rating']
        for col in rating_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')
        
        self.raw_data = df
        return df
    
    def apply_exclusion_rules(self) -> pd.DataFrame:
        """
        Apply exclusion rules to create cleaned dataset.
        """
        if self.raw_data is None:
            self.standardize_data()
        
        df = self.raw_data.copy()
        
        # Initialize exclusion flags
        df['excl_failed_attention'] = False
        df['excl_fast_rt'] = False
        df['excl_slow_rt'] = False
        df['excl_device_violation'] = False
        df['include_in_primary'] = True
        
        # Session-level exclusions
        session_exclusions = self._apply_session_exclusions(df)
        df = session_exclusions['data']
        
        # Trial-level exclusions
        trial_exclusions = self._apply_trial_exclusions(df)
        df = trial_exclusions['data']
        
        # Combine exclusion summaries
        self.exclusion_summary = {
            'session_level': session_exclusions['summary'],
            'trial_level': trial_exclusions['summary'],
            'total_raw': len(self.raw_data),
            'total_cleaned': len(df[df['include_in_primary']])
        }
        
        self.cleaned_data = df
        return df
    
    def _apply_session_exclusions(self, df: pd.DataFrame) -> Dict:
        """
        Apply session-level exclusion rules.
        """
        summary = {
            'total_sessions': df['pid'].nunique(),
            'excluded_sessions': 0,
            'exclusion_reasons': {}
        }
        
        # Get unique participants
        participants = df['pid'].unique()
        
        for participant in participants:
            participant_data = df[df['pid'] == participant]
            
            # Check for attention check failures (placeholder - adjust based on your data)
            # This would need to be customized based on your actual attention check implementation
            attention_failed = False  # Placeholder
            
            # Check for device violations (placeholder)
            device_violation = False  # Placeholder
            
            # Check for duplicate prolific_pid (keep most complete session)
            if 'prolific_pid' in df.columns:
                prolific_pids = participant_data['prolific_pid'].dropna().astype(str).unique()
                if len(prolific_pids) > 1:
                    # Keep session with most trials
                    # Convert prolific_pid to string to avoid type comparison issues
                    participant_data_copy = participant_data.copy()
                    participant_data_copy['prolific_pid'] = participant_data_copy['prolific_pid'].astype(str)
                    session_completeness = participant_data_copy.groupby('prolific_pid').size()
                    keep_pid = session_completeness.idxmax()
                    df.loc[df['prolific_pid'] != keep_pid, 'include_in_primary'] = False
            
            # Check for minimum trial completion
            # Real participant files (participant_P*.csv) and numeric IDs (200, 201, etc.) should not be excluded for completion rate
            is_real_participant = (str(participant).startswith('P') and len(str(participant)) >= 2) or str(participant).isdigit()
            
            # For test data, be more lenient (50% instead of 80%)
            # But only if it's actually test data (not real participant data)
            is_test_data = any(test_pattern in str(participant) for test_pattern in ['test_', 'test123', 'test456', 'test789', 'test_p1', 'test_p2'])
            
            if is_real_participant:
                # Don't exclude real participants for completion rate
                # Set completion rate to 100% for display purposes
                completion_rate = 1.0
            else:
                # For non-real participants, check completion rate
                expected_trials = 60  # Adjust based on your study design
                actual_trials = len(participant_data)
                completion_rate = actual_trials / expected_trials
                
                if is_test_data:
                    min_completion_rate = 0.5  # 50% for test data
                    if completion_rate < min_completion_rate:
                        df.loc[df['pid'] == participant, 'include_in_primary'] = False
                        summary['exclusion_reasons']['low_completion'] = summary['exclusion_reasons'].get('low_completion', 0) + 1
                else:
                    min_completion_rate = 0.8  # 80% for other data
                    if completion_rate < min_completion_rate:
                        df.loc[df['pid'] == participant, 'include_in_primary'] = False
                        summary['exclusion_reasons']['low_completion'] = summary['exclusion_reasons'].get('low_completion', 0) + 1
            
            if attention_failed:
                df.loc[df['pid'] == participant, 'excl_failed_attention'] = True
                df.loc[df['pid'] == participant, 'include_in_primary'] = False
                summary['exclusion_reasons']['attention_failed'] = summary['exclusion_reasons'].get('attention_failed', 0) + 1
            
            if device_violation:
                df.loc[df['pid'] == participant, 'excl_device_violation'] = True
                df.loc[df['pid'] == participant, 'include_in_primary'] = False
                summary['exclusion_reasons']['device_violation'] = summary['exclusion_reasons'].get('device_violation', 0) + 1
        
        summary['excluded_sessions'] = len(participants) - df[df['include_in_primary']]['pid'].nunique()
        
        return {'data': df, 'summary': summary}
    
    def _apply_trial_exclusions(self, df: pd.DataFrame) -> Dict:
        """
        Apply trial-level exclusion rules.
        """
        summary = {
            'total_trials': len(df),
            'excluded_trials': 0,
            'exclusion_reasons': {}
        }
        
        # Drop trials with RT < 200ms (if RT data available)
        if 'reaction_time' in df.columns:
            fast_trials = df['reaction_time'] < 200
            df.loc[fast_trials, 'excl_fast_rt'] = True
            df.loc[fast_trials, 'include_in_primary'] = False
            summary['exclusion_reasons']['fast_rt'] = fast_trials.sum()
        
        # Drop RTs > 99.5 percentile within subject (if RT data available)
        if 'reaction_time' in df.columns:
            for participant in df['pid'].unique():
                participant_data = df[df['pid'] == participant]
                rt_threshold = participant_data['reaction_time'].quantile(0.995)
                slow_trials = (df['pid'] == participant) & (df['reaction_time'] > rt_threshold)
                df.loc[slow_trials, 'excl_slow_rt'] = True
                df.loc[slow_trials, 'include_in_primary'] = False
                summary['exclusion_reasons']['slow_rt'] = summary['exclusion_reasons'].get('slow_rt', 0) + slow_trials.sum()
        
        summary['excluded_trials'] = len(df) - df['include_in_primary'].sum()
        
        return {'data': df, 'summary': summary}
    
    def get_cleaned_data(self) -> pd.DataFrame:
        """
        Get the cleaned dataset with exclusion flags.
        """
        if self.cleaned_data is None:
            self.apply_exclusion_rules()
        
        return self.cleaned_data
    
    def get_exclusion_summary(self) -> Dict:
        """
        Get summary of exclusion rules applied.
        """
        if self.exclusion_summary == {}:
            self.apply_exclusion_rules()
        
        return self.exclusion_summary
    
    def get_data_by_version(self, version: str) -> pd.DataFrame:
        """
        Get data filtered by face version (left, right, full).
        """
        cleaned_data = self.get_cleaned_data()
        return cleaned_data[
            (cleaned_data['version'] == version) & 
            (cleaned_data['include_in_primary'])
        ]
    
    def _is_complete_participant(self, participant_data: pd.DataFrame) -> bool:
        """
        Check if a participant has completed at least one full face.
        Handles both WIDE format (trust_rating, emotion_rating columns) and LONG format (question_type, response columns).
        """
        if len(participant_data) == 0:
            return False
        
        # Check if this is long format data (question_type/response columns)
        if 'question_type' in participant_data.columns and 'response' in participant_data.columns:
            # Long format: check if participant has at least 10 responses (1 complete face)
            # Each complete face should have 10 responses: 2 left + 2 right + 6 both
            response_count = len(participant_data)
            if response_count >= 10:
                return True
            return False
        
        # Wide format: check for required columns
        required_columns = ['trust_rating', 'emotion_rating', 'masc_choice', 'fem_choice']
        
        # Check if all required columns exist
        if not all(col in participant_data.columns for col in required_columns):
            return False
            
        # Check each row (face) for complete data
        for _, row in participant_data.iterrows():
            # Check if this face has all required responses (not null/empty)
            if all(pd.notna(row[col]) and str(row[col]).strip() != '' for col in required_columns):
                return True
        
        return False
    
    def get_complete_participants_only(self) -> pd.DataFrame:
        """
        Get only participants who have completed at least one full face (10+ responses).
        """
        cleaned_data = self.get_cleaned_data()
        participant_data = cleaned_data[cleaned_data['include_in_primary']]
        
        # Filter to only complete participants
        complete_participants = []
        for pid in participant_data['pid'].unique():
            pid_data = participant_data[participant_data['pid'] == pid]
            if self._is_complete_participant(pid_data):
                complete_participants.extend(pid_data.index)
        
        return participant_data.loc[complete_participants] if complete_participants else pd.DataFrame()
    
    def get_participant_summary(self) -> pd.DataFrame:
        """
        Get summary statistics per participant (complete participants only).
        """
        participant_data = self.get_complete_participants_only()
        
        if len(participant_data) == 0:
            return pd.DataFrame(columns=['pid', 'total_trials', 'mean_trust', 'std_trust', 'versions_seen', 'faces_seen'])
        
        summary = participant_data.groupby('pid').agg({
            'trust_rating': ['count', 'mean', 'std'],
            'version': 'nunique',
            'face_id': 'nunique'
        }).round(3)
        
        summary.columns = ['total_trials', 'mean_trust', 'std_trust', 'versions_seen', 'faces_seen']
        return summary.reset_index()

