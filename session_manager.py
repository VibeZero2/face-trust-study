"""
Session Manager for Facial Trust Study
IRB-Approved Research - DO NOT MODIFY CRITICAL SYSTEMS

This module provides safe session persistence without changing existing functionality.
"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional

# Session storage directory
SESSIONS_DIR = Path(__file__).parent / "data" / "sessions"

def ensure_sessions_dir():
    """Ensure sessions directory exists, with fallback options."""
    global SESSIONS_DIR
    try:
        SESSIONS_DIR.mkdir(parents=True, exist_ok=True)
        return True
    except (OSError, PermissionError) as e:
        print(f"Warning: Could not create sessions directory: {e}")
        try:
            # Create a fallback directory in temp
            import tempfile
            SESSIONS_DIR = Path(tempfile.gettempdir()) / "facial_trust_sessions"
            SESSIONS_DIR.mkdir(parents=True, exist_ok=True)
            print(f"Using fallback sessions directory: {SESSIONS_DIR}")
            return True
        except Exception as e2:
            print(f"Error: Could not create fallback sessions directory: {e2}")
            return False

# Initialize sessions directory
_sessions_available = ensure_sessions_dir()

def save_session_state(participant_id: str, session_data: Dict[str, Any]) -> bool:
    """
    Save current session state to file.
    
    Args:
        participant_id: The participant ID
        session_data: Current session data from Flask session
        
    Returns:
        bool: True if saved successfully, False otherwise
    """
    try:
        # Ensure directory exists before saving
        if not _sessions_available:
            if not ensure_sessions_dir():
                return False
                
        # Create a safe filename
        safe_id = participant_id.replace(" ", "_").replace("/", "_").replace("\\", "_")
        session_file = SESSIONS_DIR / f"{safe_id}_session.json"
        
        # Prepare session data for saving
        session_state = {
            "participant_id": participant_id,
            "timestamp": datetime.utcnow().isoformat(),
            "index": session_data.get("index", 0),
            "face_order": session_data.get("face_order", []),
            "responses": session_data.get("responses", []),
            "prolific_pid": session_data.get("prolific_pid", ""),
            "left_first": session_data.get("left_first", True),  # Save the left_first value
            "session_complete": bool(session_data.get("session_complete", False))
        }

        if session_data.get("completion_timestamp"):
            session_state["completion_timestamp"] = session_data.get("completion_timestamp")

        
        # Save to JSON file
        with open(session_file, 'w') as f:
            json.dump(session_state, f, indent=2)
            
        print(f"✅ Session saved for participant {participant_id}")
        print(f"   📊 Saved {len(session_state.get('responses', []))} responses at index {session_state.get('index', 0)}")
        print(f"   📁 File: {session_file}")
        return True
        
    except Exception as e:
        print(f"❌ Error saving session for {participant_id}: {e}")
        return False

def load_session_state(participant_id: str) -> Optional[Dict[str, Any]]:
    """
    Load saved session state for a participant.
    
    Args:
        participant_id: The participant ID
        
    Returns:
        Dict containing session data or None if not found
    """
    try:
        # Create a safe filename
        safe_id = participant_id.replace(" ", "_").replace("/", "_").replace("\\", "_")
        session_file = SESSIONS_DIR / f"{safe_id}_session.json"
        
        if not session_file.exists():
            return None
            
        # Load session data
        with open(session_file, 'r') as f:
            session_state = json.load(f)
            
        print(f"✅ Session loaded for participant {participant_id}")
        return session_state
        
    except Exception as e:
        print(f"❌ Error loading session for {participant_id}: {e}")
        return None

def check_session_exists(participant_id: str) -> bool:
    """
    Check if a saved session exists for a participant.
    
    Args:
        participant_id: The participant ID
        
    Returns:
        bool: True if session exists, False otherwise
    """
    try:
        safe_id = participant_id.replace(" ", "_").replace("/", "_").replace("\\", "_")
        session_file = SESSIONS_DIR / f"{safe_id}_session.json"
        return session_file.exists()
    except:
        return False

def mark_session_complete(participant_id: str) -> bool:
    """
    Mark a session as complete (when participant finishes the study).
    
    Args:
        participant_id: The participant ID
        
    Returns:
        bool: True if marked successfully, False otherwise
    """
    try:
        session_state = load_session_state(participant_id)
        if session_state:
            session_state["session_complete"] = True
            session_state["completion_timestamp"] = datetime.utcnow().isoformat()
            
            safe_id = participant_id.replace(" ", "_").replace("/", "_").replace("\\", "_")
            session_file = SESSIONS_DIR / f"{safe_id}_session.json"
            
            with open(session_file, 'w') as f:
                json.dump(session_state, f, indent=2)
                
            print(f"✅ Session marked complete for participant {participant_id}")
            return True
        return False
        
    except Exception as e:
        print(f"❌ Error marking session complete for {participant_id}: {e}")
        return False

def get_session_progress(participant_id: str) -> Optional[Dict[str, Any]]:
    """
    Get session progress information for display.
    
    Args:
        participant_id: The participant ID
        
    Returns:
        Dict with progress info or None if not found
    """
    try:
        session_state = load_session_state(participant_id)
        if not session_state:
            return None
            
        total_faces = len(session_state.get("face_order", []))
        current_index = session_state.get("index", 0)
        completed_faces = current_index // 2  # Each face has 2 stages (toggle + full)
        
        return {
            "participant_id": participant_id,
            "total_faces": total_faces,
            "completed_faces": completed_faces,
            "progress_percent": (completed_faces / total_faces * 100) if total_faces > 0 else 0,
            "last_activity": session_state.get("timestamp", ""),
            "session_complete": session_state.get("session_complete", False)
        }
        
    except Exception as e:
        print(f"❌ Error getting progress for {participant_id}: {e}")
        return None
