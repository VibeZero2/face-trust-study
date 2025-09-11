"""
Long Format Data Processor for Face Viewer Dashboard
==================================================

This module handles loading and processing of long format CSV data
from the facial trust study. It's designed to work with the new
long format data structure where each row represents one response
to one question for one face view.

Long Format Structure:
- participant_id: ID of the participant
- image_id: ID of the face/image being shown
- face_view: left, right, or full
- question_type: trust_rating, masc_choice, fem_choice, etc.
- response: the actual response value
- timestamp: when the response was recorded
"""

import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, List, Tuple, Optional
import logging

logger = logging.getLogger(__name__)

class LongFormatProcessor:
    """
    Processes long format data from the facial trust study.
    """
    
    def __init__(self, data_dir: str = "data/responses", test_mode: bool = False):
        self.data_dir = Path(data_dir)
        self.test_mode = test_mode
        self.raw_data = None
        self.processed_data = None
        self.summary_stats = {}
        
    def load_data(self) -> pd.DataFrame:
        """
        Load long format CSV files from the responses directory.
        
        Returns:
            pd.DataFrame: Combined long format data
        """
        csv_files = list(self.data_dir.glob("*.csv"))
        if not csv_files:
            raise FileNotFoundError(f"No CSV files found in {self.data_dir}")
        
        # Filter files based on mode
        if self.test_mode:
            filtered_files = csv_files
            logger.info("TEST MODE: Loading all CSV files including test data")
        else:
            # Production mode: exclude test files
            filtered_files = []
            excluded_files = []
            
            for file_path in csv_files:
                file_name = file_path.name
                
                # Exclude test files
                if (file_name.startswith('test_') or 
                    file_name.startswith('test_participant') or
                    'test_statistical_validation' in file_name or
                    file_name.startswith('PROLIFIC_TEST_') or
                    file_name == 'test789.csv' or
                    file_name == 'test123.csv' or
                    file_name == 'test456.csv' or
                    file_name == 'test_participants_combined.csv'):
                    excluded_files.append(file_name)
                    continue
                
                # Include all other files
                filtered_files.append(file_path)
            
            if excluded_files:
                logger.info(f"PRODUCTION MODE: Excluded test files: {excluded_files}")
            
            if not filtered_files:
                raise FileNotFoundError(f"No real study data files found in {self.data_dir}")
        
        all_data = []
        real_participants = 0
        total_rows = 0
        
        for file_path in filtered_files:
            try:
                df = pd.read_csv(file_path)
                
                # Check if this is long format data
                if self._is_long_format(df):
                    # Add file metadata
                    df['source_file'] = file_path.name
                    df['loaded_at'] = pd.Timestamp.now()
                    all_data.append(df)
                    
                    # Count unique participants
                    unique_participants = df['participant_id'].nunique()
                    real_participants += unique_participants
                    total_rows += len(df)
                    
                    logger.info(f"Loaded {len(df)} long format rows from {file_path.name} ({unique_participants} participants)")
                else:
                    logger.warning(f"Skipping {file_path.name} - not in long format")
                    
            except Exception as e:
                logger.error(f"Error loading {file_path}: {e}")
                continue
        
        if not all_data:
            raise ValueError("No valid long format CSV files could be loaded")
        
        # Merge all dataframes
        self.raw_data = pd.concat(all_data, ignore_index=True)
        
        # Log summary
        if self.test_mode:
            logger.info(f"TEST MODE: Total long format data loaded: {len(self.raw_data)} rows from {len(filtered_files)} files")
        else:
            logger.info(f"PRODUCTION MODE: Loaded {len(self.raw_data)} long format rows from {real_participants} real participants")
        
        return self.raw_data
    
    def _is_long_format(self, df: pd.DataFrame) -> bool:
        """
        Check if a DataFrame is in long format.
        
        Args:
            df: DataFrame to check
            
        Returns:
            bool: True if in long format, False otherwise
        """
        required_columns = ['participant_id', 'image_id', 'face_view', 'question_type', 'response']
        return all(col in df.columns for col in required_columns)
    
    def process_data(self) -> pd.DataFrame:
        """
        Process the loaded long format data for analysis.
        
        Returns:
            pd.DataFrame: Processed data ready for analysis
        """
        if self.raw_data is None:
            raise ValueError("No data loaded. Call load_data() first.")
        
        # Create a copy for processing
        df = self.raw_data.copy()
        
        # Convert timestamp to datetime
        df['timestamp'] = pd.to_datetime(df['timestamp'], errors='coerce')
        
        # Clean response values
        df['response'] = df['response'].astype(str).str.strip()
        
        # Convert numeric responses to appropriate types
        numeric_questions = ['trust_rating', 'emotion_rating', 'trust_q2', 'trust_q3', 
                           'pers_q1', 'pers_q2', 'pers_q3', 'pers_q4', 'pers_q5']
        
        for question in numeric_questions:
            mask = df['question_type'] == question
            df.loc[mask, 'response'] = pd.to_numeric(df.loc[mask, 'response'], errors='coerce')
        
        # Create derived columns for easier analysis
        df['is_numeric_response'] = df['question_type'].isin(numeric_questions)
        df['response_numeric'] = pd.to_numeric(df['response'], errors='coerce')
        
        # Add face view order for analysis
        face_view_order = {'left': 1, 'right': 2, 'full': 3}
        df['face_view_order'] = df['face_view'].map(face_view_order)
        
        self.processed_data = df
        return self.processed_data
    
    def get_data_summary(self) -> Dict:
        """
        Get summary statistics of the processed data.
        
        Returns:
            Dict: Summary statistics
        """
        if self.processed_data is None:
            raise ValueError("No processed data available. Call process_data() first.")
        
        df = self.processed_data
        
        summary = {
            'total_responses': len(df),
            'unique_participants': df['participant_id'].nunique(),
            'unique_images': df['image_id'].nunique(),
            'question_types': df['question_type'].value_counts().to_dict(),
            'face_views': df['face_view'].value_counts().to_dict(),
            'responses_per_participant': df.groupby('participant_id').size().describe().to_dict(),
            'responses_per_image': df.groupby('image_id').size().describe().to_dict(),
            'date_range': {
                'earliest': df['timestamp'].min(),
                'latest': df['timestamp'].max()
            }
        }
        
        return summary
    
    def get_trust_ratings_by_view(self) -> pd.DataFrame:
        """
        Get trust ratings organized by face view for analysis.
        
        Returns:
            pd.DataFrame: Trust ratings pivoted by face view
        """
        if self.processed_data is None:
            raise ValueError("No processed data available. Call process_data() first.")
        
        # Filter for trust ratings only
        trust_data = self.processed_data[
            self.processed_data['question_type'] == 'trust_rating'
        ].copy()
        
        # Pivot to get left, right, full as columns
        trust_pivot = trust_data.pivot_table(
            index=['participant_id', 'image_id'],
            columns='face_view',
            values='response_numeric',
            aggfunc='mean'
        ).reset_index()
        
        return trust_pivot
    
    def get_question_responses(self, question_type: str) -> pd.DataFrame:
        """
        Get all responses for a specific question type.
        
        Args:
            question_type: The question type to filter for
            
        Returns:
            pd.DataFrame: Filtered responses
        """
        if self.processed_data is None:
            raise ValueError("No processed data available. Call process_data() first.")
        
        return self.processed_data[
            self.processed_data['question_type'] == question_type
        ].copy()
    
    def get_participant_data(self, participant_id: str) -> pd.DataFrame:
        """
        Get all data for a specific participant.
        
        Args:
            participant_id: The participant ID
            
        Returns:
            pd.DataFrame: Participant's data
        """
        if self.processed_data is None:
            raise ValueError("No processed data available. Call process_data() first.")
        
        return self.processed_data[
            self.processed_data['participant_id'] == participant_id
        ].copy()
    
    def get_image_summary(self) -> pd.DataFrame:
        """
        Get summary statistics for each image across all participants.
        
        Returns:
            pd.DataFrame: Image summary statistics
        """
        if self.processed_data is None:
            raise ValueError("No processed data available. Call process_data() first.")
        
        # Get trust ratings by image and view
        trust_data = self.get_question_responses('trust_rating')
        
        if trust_data.empty:
            return pd.DataFrame()
        
        # Group by image and face view
        image_summary = trust_data.groupby(['image_id', 'face_view']).agg({
            'response_numeric': ['count', 'mean', 'std', 'min', 'max'],
            'participant_id': 'nunique'
        }).round(2)
        
        # Flatten column names
        image_summary.columns = ['_'.join(col).strip() for col in image_summary.columns]
        image_summary = image_summary.reset_index()
        
        return image_summary
    
    def export_for_analysis(self, output_dir: str = "exports") -> Dict[str, str]:
        """
        Export processed data in formats suitable for statistical analysis.
        
        Args:
            output_dir: Directory to save export files
            
        Returns:
            Dict[str, str]: Paths to exported files
        """
        if self.processed_data is None:
            raise ValueError("No processed data available. Call process_data() first.")
        
        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True)
        
        exported_files = {}
        
        # Export full long format data
        full_data_path = output_path / "long_format_full_data.csv"
        self.processed_data.to_csv(full_data_path, index=False)
        exported_files['full_data'] = str(full_data_path)
        
        # Export trust ratings pivoted by view
        trust_pivot = self.get_trust_ratings_by_view()
        if not trust_pivot.empty:
            trust_path = output_path / "trust_ratings_by_view.csv"
            trust_pivot.to_csv(trust_path, index=False)
            exported_files['trust_by_view'] = str(trust_path)
        
        # Export image summary
        image_summary = self.get_image_summary()
        if not image_summary.empty:
            image_path = output_path / "image_summary.csv"
            image_summary.to_csv(image_path, index=False)
            exported_files['image_summary'] = str(image_path)
        
        logger.info(f"Exported {len(exported_files)} files to {output_path}")
        return exported_files
