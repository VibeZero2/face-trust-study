"""
Test script for Prolific ID integration in the facial-trust-study application.
This script simulates a participant coming from Prolific with a PROLIFIC_PID parameter.
"""

import requests
import webbrowser
import time
import os
from urllib.parse import urljoin

# Configuration
BASE_URL = "http://localhost:5000"  # Change if your app runs on a different port
TEST_PROLIFIC_ID = "test_prolific_123456"  # Test Prolific ID
TEST_PARTICIPANT_ID = "test_participant_001"  # Test participant ID

def test_prolific_integration():
    """Test the Prolific ID integration by opening a browser with the appropriate URL parameters."""
    # Construct the URL with Prolific ID parameter
    url = f"{BASE_URL}/?PROLIFIC_PID={TEST_PROLIFIC_ID}"
    
    print(f"Opening browser with URL: {url}")
    print(f"This simulates a participant coming from Prolific with ID: {TEST_PROLIFIC_ID}")
    print("Please follow these steps to test the integration:")
    print("1. Complete the consent form")
    print(f"2. Enter '{TEST_PARTICIPANT_ID}' as the participant ID when prompted")
    print("3. Complete at least one face rating")
    print("4. Complete the survey")
    print("5. Verify that the completion page shows the Prolific ID and completion link")
    
    # Open the browser with the test URL
    webbrowser.open(url)
    
    print("\nAfter completing the test, check the data files in the 'data' directory")
    print(f"Look for '{TEST_PARTICIPANT_ID}.csv' and verify that it contains the Prolific ID")

if __name__ == "__main__":
    # Check if the Flask app is running
    try:
        response = requests.get(BASE_URL, timeout=2)
        test_prolific_integration()
    except requests.exceptions.ConnectionError:
        print("Error: The Flask application is not running.")
        print("Please start the application first with:")
        print("    python app.py")
        print("Then run this test script again.")
