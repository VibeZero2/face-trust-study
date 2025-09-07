#!/usr/bin/env python3
"""
Legacy Data Conversion Script
============================

This script converts existing wide format CSV files to the new long format.
It reads all CSV files in data/responses/ and converts them to long format,
saving the converted files in data/long_format_exports/.

Usage:
    python convert_legacy_to_long_format.py

The script will:
1. Read all CSV files in data/responses/
2. Convert wide format to long format
3. Save converted files in data/long_format_exports/
4. Preserve original files
"""

import csv
import pandas as pd
from pathlib import Path
from datetime import datetime
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def convert_wide_to_long_format(wide_responses: list) -> list:
    """
    Convert wide format responses to long format.
    
    Args:
        wide_responses: List of dictionaries in wide format
        
    Returns:
        List of dictionaries in long format
    """
    long_responses = []
    
    for response in wide_responses:
        participant_id = response.get("pid", "")
        timestamp = response.get("timestamp", "")
        face_id = response.get("face_id", "")
        face_view = response.get("version", "")
        
        # Skip survey rows
        if face_id == "survey":
            continue
            
        # Define question types and their corresponding response values
        question_mappings = [
            ("trust_rating", response.get("trust_rating")),
            ("masc_choice", response.get("masc_choice")),
            ("fem_choice", response.get("fem_choice")),
            ("emotion_rating", response.get("emotion_rating")),
            ("trust_q2", response.get("trust_q2")),
            ("trust_q3", response.get("trust_q3")),
            ("pers_q1", response.get("pers_q1")),
            ("pers_q2", response.get("pers_q2")),
            ("pers_q3", response.get("pers_q3")),
            ("pers_q4", response.get("pers_q4")),
            ("pers_q5", response.get("pers_q5"))
        ]
        
        # Create a long format row for each non-null response
        for question_type, response_value in question_mappings:
            if response_value is not None and response_value != "":
                long_row = {
                    "participant_id": participant_id,
                    "image_id": face_id,
                    "face_view": face_view,
                    "question_type": question_type,
                    "response": response_value,
                    "timestamp": timestamp
                }
                long_responses.append(long_row)
    
    return long_responses

def convert_csv_file(input_path: Path, output_dir: Path) -> bool:
    """
    Convert a single CSV file from wide to long format.
    
    Args:
        input_path: Path to the input CSV file
        output_dir: Directory to save the converted file
        
    Returns:
        bool: True if conversion was successful, False otherwise
    """
    try:
        logger.info(f"Converting {input_path.name}...")
        
        # Read the CSV file
        df = pd.read_csv(input_path)
        
        # Convert to list of dictionaries
        wide_responses = df.to_dict('records')
        
        # Convert to long format
        long_responses = convert_wide_to_long_format(wide_responses)
        
        if not long_responses:
            logger.warning(f"No valid responses found in {input_path.name}")
            return False
        
        # Create output filename
        output_filename = f"long_format_{input_path.stem}.csv"
        output_path = output_dir / output_filename
        
        # Write long format CSV
        long_format_headers = ["participant_id", "image_id", "face_view", "question_type", "response", "timestamp"]
        
        with open(output_path, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=long_format_headers)
            writer.writeheader()
            writer.writerows(long_responses)
        
        logger.info(f"✅ Converted {input_path.name}: {len(wide_responses)} wide rows → {len(long_responses)} long rows")
        logger.info(f"   Saved to: {output_path}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Error converting {input_path.name}: {e}")
        return False

def main():
    """Main conversion function."""
    logger.info("🔄 Starting legacy data conversion to long format...")
    
    # Define paths
    data_dir = Path("data")
    responses_dir = data_dir / "responses"
    output_dir = data_dir / "long_format_exports"
    
    # Check if responses directory exists
    if not responses_dir.exists():
        logger.error(f"❌ Responses directory not found: {responses_dir}")
        return
    
    # Create output directory
    output_dir.mkdir(exist_ok=True)
    logger.info(f"📁 Output directory: {output_dir}")
    
    # Find all CSV files
    csv_files = list(responses_dir.glob("*.csv"))
    
    if not csv_files:
        logger.warning("⚠️ No CSV files found in responses directory")
        return
    
    logger.info(f"📊 Found {len(csv_files)} CSV files to convert")
    
    # Convert each file
    successful_conversions = 0
    failed_conversions = 0
    
    for csv_file in csv_files:
        if convert_csv_file(csv_file, output_dir):
            successful_conversions += 1
        else:
            failed_conversions += 1
    
    # Summary
    logger.info("=" * 50)
    logger.info("📋 CONVERSION SUMMARY")
    logger.info("=" * 50)
    logger.info(f"✅ Successful conversions: {successful_conversions}")
    logger.info(f"❌ Failed conversions: {failed_conversions}")
    logger.info(f"📁 Converted files saved in: {output_dir}")
    logger.info("=" * 50)
    
    if successful_conversions > 0:
        logger.info("🎉 Legacy conversion completed successfully!")
        logger.info("💡 You can now use the converted files for analysis.")
    else:
        logger.warning("⚠️ No files were successfully converted.")

if __name__ == "__main__":
    main()
