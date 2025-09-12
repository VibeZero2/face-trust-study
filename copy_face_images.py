"""
Copy face images from the Face Viewer directory and rename them for the facial trust study.
This script copies the first 35 face images and renames them to face_01.jpg through face_35.jpg
"""

import os
import shutil
from pathlib import Path

# Source directory with face images
source_dir = Path(r"C:\Users\Chris\CascadeProjects\ALL\New Face Viewer\images")

# Destination directory
dest_dir = Path("static/images")
dest_dir.mkdir(parents=True, exist_ok=True)

# List of face image files (first 35)
face_files = [
    "001_03.jpg", "002_03.jpg", "003_03.jpg", "004_03.jpg", "005_03.jpg",
    "006_03.jpg", "007_03.jpg", "008_03.jpg", "009_03.jpg", "010_03.jpg",
    "011_03.jpg", "012_03.jpg", "013_03.jpg", "014_03.jpg", "016_03.jpg",
    "017_03.jpg", "018_03.jpg", "019_03.jpg", "020_03.jpg", "021_03.jpg",
    "022_03.jpg", "024_03.jpg", "025_03.jpg", "026_03.jpg", "027_03.jpg",
    "029_03.jpg", "030_03.jpg", "031_03.jpg", "032_03.jpg", "033_03.jpg",
    "034_03.jpg", "036_03.jpg", "037_03.jpg", "038_03.jpg", "039_03.jpg"
]

def copy_face_images():
    """Copy and rename face images."""
    copied_count = 0
    
    for i, filename in enumerate(face_files, 1):
        source_file = source_dir / filename
        dest_file = dest_dir / f"face_{i:02d}.jpg"
        
        if source_file.exists():
            try:
                shutil.copy2(source_file, dest_file)
                print(f"Copied {filename} -> face_{i:02d}.jpg")
                copied_count += 1
            except Exception as e:
                print(f"Error copying {filename}: {e}")
        else:
            print(f"Source file not found: {filename}")
    
    print(f"\nCopied {copied_count} face images successfully!")
    return copied_count

if __name__ == "__main__":
    copy_face_images()
