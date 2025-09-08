import os
import csv
import random
from datetime import datetime
from pathlib import Path
from flask import Flask, render_template, request, redirect, url_for, session, abort
from cryptography.fernet import Fernet
from dotenv import load_dotenv

# Session management (IRB-safe addition)
try:
    from session_manager import save_session_state, load_session_state, check_session_exists, mark_session_complete, get_session_progress
    SESSION_MANAGEMENT_ENABLED = True
except ImportError:
    SESSION_MANAGEMENT_ENABLED = False
    print("⚠️ Session management not available - continuing without save/resume functionality")

# ----------------------------------------------------------------------------
# Initial setup
# ----------------------------------------------------------------------------
load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", os.urandom(24))

# Encryption key (must be 32 url-safe base64-encoded bytes)
FERNET_KEY = os.getenv("FERNET_KEY")
if not FERNET_KEY:
    raise RuntimeError("FERNET_KEY missing in .env")
fernet = Fernet(FERNET_KEY)

# Folder constants
BASE_DIR = Path(__file__).resolve().parent
IMAGES_DIR = BASE_DIR / "static" / "images"
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)

# Load image list once at startup.
# We accept any JPG/PNG in the folder and will present the SAME image three times
# (left crop, right crop, full) using CSS clipping.
# Accept .jpg or .jpeg in any capitalization
FACE_FILES = []
for pattern in ("*.jpg", "*.jpeg", "*.JPG", "*.JPEG"):
    FACE_FILES.extend([p.name for p in IMAGES_DIR.glob(pattern)])
# Deduplicate by filename stem (without extension) to avoid counting duplicates
unique = {}
for fname in FACE_FILES:
    stem = Path(fname).stem
    if stem not in unique:
        unique[stem] = fname  # keep first occurrence
FACE_FILES = sorted(unique.values())
assert FACE_FILES, "No face images found. Place images in static/images/."

# ----------------------------------------------------------------------------
# Helper functions
# ----------------------------------------------------------------------------

def save_participant_data(participant_id: str, responses: list, headers: list) -> str:
    """
    Save participant responses to CSV file.
    
    Args:
        participant_id: The participant ID
        responses: List of response dictionaries
        headers: List of column headers
        
    Returns:
        str: Path to saved file or None if failed
    """
    try:
        # Create responses directory
        responses_dir = DATA_DIR / "responses"
        responses_dir.mkdir(exist_ok=True)
        
        # Create timestamped filename
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        filename = f"{participant_id}_{timestamp}.csv"
        filepath = responses_dir / filename
        
        # Write CSV file
        with open(filepath, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=headers)
            writer.writeheader()
            writer.writerows(responses)
            
        print(f"✅ Saved participant data to {filepath}")
        return str(filepath)
        
    except Exception as e:
        print(f"❌ Error saving participant data: {e}")
        return None

def create_participant_run(pid: str, prolific_pid: str = None):
    """Initialises session variables for a new participant."""
    
    # Randomly pick left-first or right-first presentation
    left_first = random.choice([True, False])
    
    # Randomize the order of face files for this participant
    # Use a copy to avoid modifying the original FACE_FILES list
    randomized_faces = FACE_FILES.copy()
    random.shuffle(randomized_faces)
    
    # Store the randomized order for analysis
    face_order = [Path(fname).stem for fname in randomized_faces]
    
    sequence = []
    for fname in randomized_faces:
        # order list simply contains the same filename with a tag indicating crop
        if left_first:
            halves = [
                {"version": "left", "file": fname},
                {"version": "right", "file": fname},
            ]
        else:
            halves = [
                {"version": "right", "file": fname},
                {"version": "left", "file": fname},
            ]
        sequence.append({
            "face_id": Path(fname).stem,
            "order": [{"version": "toggle", "file": fname, "start": ("left" if left_first else "right")}, {"version": "full", "file": fname}]
        })
    
    session["pid"] = pid
    session["index"] = 0  # index in sequence
    session["sequence"] = sequence
    session["responses"] = []
    session["face_order"] = face_order  # Store the randomized face order
    session["left_first"] = left_first  # Store the left_first value for session resumption
    
    # Store Prolific ID if provided
    if prolific_pid:
        session["prolific_pid"] = prolific_pid
    


def save_encrypted_csv(pid: str, rows: list):
    """Encrypts and saves participant data."""
    csv_content = csv.StringIO()
    writer = csv.writer(csv_content)
    # header
    writer.writerow([
        "pid", "timestamp", "face_id", "version", "order_presented",
        "trust_rating", "masc_choice", "fem_choice",
        "emotion_rating", "trust_q2", "trust_q3",
        "pers_q1", "pers_q2", "pers_q3", "pers_q4", "pers_q5",
        "prolific_pid"  # Add Prolific ID to header
    ])
    writer.writerows(rows)
    
    # Save face order information in a separate row
    if "face_order" in session:
        # Get prolific_pid from session if available
        prolific_pid = session.get("prolific_pid", "")
        face_order_row = [pid, datetime.utcnow().isoformat(), "face_order", "metadata", "", "", "", "", "", "", "", "", "", "", "", "", prolific_pid]
        writer.writerow(face_order_row)
        # Add the face order as additional rows with index numbers
        for i, face_id in enumerate(session["face_order"]):
            order_row = [pid, "", face_id, "order_index", i+1, "", "", "", "", "", "", "", "", "", "", ""]
            writer.writerow(order_row)
    
    # Encrypt the CSV content
    encrypted_data = fernet.encrypt(csv_content.getvalue().encode())
    
    # Save to file
    enc_path = DATA_DIR / f"{pid}.enc"
    with open(enc_path, "wb") as f:
        f.write(encrypted_data)
        
    # Also save as CSV for easy access
    csv_path = DATA_DIR / f"{pid}.csv"
    with open(csv_path, "w", newline="") as f:
        f.write(csv_content.getvalue())
        
    # Return both paths for confirmation
    return {"enc": enc_path, "csv": csv_path}


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

def save_participant_data(participant_id: str, responses: list, headers=None):
    """Save responses to a CSV file in data/responses/ in LONG FORMAT
    
    Args:
        participant_id: The participant ID (PROLIFIC_PID or assigned ID)
        responses: List of dictionaries containing response data
        headers: Optional list of column headers (uses dict keys if not provided)
    """
    try:
        # Create data/responses directory if it doesn't exist
        responses_dir = DATA_DIR / "responses"
        responses_dir.mkdir(exist_ok=True)
        
        # Use a timestamp in the filename to prevent overwriting
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        
        # Ensure participant_id is valid for a filename
        safe_id = participant_id.replace(" ", "_").replace("/", "_").replace("\\", "_")
        if not safe_id:
            safe_id = "anon"  # Use 'anon' if ID is empty
            
        # Define the filepath with timestamp
        filepath = responses_dir / f"{safe_id}_{timestamp}.csv"
        
        # Ensure we have valid responses
        if not responses or len(responses) == 0:
            print(f"⚠️ No responses to save for participant {participant_id}")
            return None
        
        # Convert wide format to long format
        long_responses = convert_wide_to_long_format(responses)
        
        if not long_responses:
            print(f"⚠️ No valid responses after conversion to long format for participant {participant_id}")
            return None
            
        # Define long format headers
        long_format_headers = ["participant_id", "image_id", "face_view", "question_type", "response", "timestamp"]
        
        # Write the CSV file in long format
        with open(filepath, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=long_format_headers)
            writer.writeheader()
            writer.writerows(long_responses)
        
        print(f"✅ Saved participant data in LONG FORMAT to {filepath}")
        print(f"   📊 Converted {len(responses)} wide format rows to {len(long_responses)} long format rows")
        return filepath
        
    except Exception as e:
        print(f"❌ Error saving participant data: {e}")
        return None

# ----------------------------------------------------------------------------
# Routes
# ----------------------------------------------------------------------------

@app.route("/consent", methods=["GET", "POST"])
def consent():
    """Informed consent page shown before anything else."""
    if request.method == "POST":
        choice = request.form.get("choice")
        if choice == "agree":
            session["consent"] = True
            return redirect(url_for("landing"))
        # Declined – clear session and show goodbye
        session.clear()
        return render_template("declined.html")
    return render_template("consent.html")


@app.route("/survey", methods=["GET", "POST"])
def survey():
    if "pid" not in session:
        return redirect(url_for("landing"))
    if request.method == "POST":
        # Get form data with correct input names
        # The template now uses trust1, trust2, trust3 instead of trust1, trust2, trust3
        t1 = request.form.get("trust1")
        t2 = request.form.get("trust2")
        t3 = request.form.get("trust3")
        p1 = request.form.get("pers1")
        p2 = request.form.get("pers2")
        p3 = request.form.get("pers3")
        p4 = request.form.get("pers4")
        p5 = request.form.get("pers5")
        prolific_pid = session.get("prolific_pid", "")
        
        # Log the form data for debugging
        print(f"Form data received: {dict(request.form)}")
        
        session["responses"].append([
            session["pid"], datetime.utcnow().isoformat(), "survey", "survey", session["index"],
            None, None, None,
            t1, t2, t3, p1, p2, p3, p4, p5,
            prolific_pid  # Add Prolific ID
        ])
        
        # Save and finish
        try:
            # Save encrypted CSV (original format)
            save_encrypted_csv(session["pid"], session["responses"])
            print(f"✅ Successfully saved encrypted CSV for participant {session['pid']}")
            
            # Convert session responses to dictionary format for save_participant_data
            participant_id = session["pid"]
            prolific_pid = session.get("prolific_pid", participant_id)
            
            # Use the Prolific ID if available, otherwise use the participant ID
            save_id = prolific_pid if prolific_pid else participant_id
            
            # Convert list-based responses to dictionary format
            dict_responses = []
            headers = [
                "pid", "timestamp", "face_id", "version", "order_presented",
                "trust_rating", "masc_choice", "fem_choice",
                "trust_q1", "trust_q2", "trust_q3",
                "pers_q1", "pers_q2", "pers_q3", "pers_q4", "pers_q5",
                "prolific_pid"
            ]
            
            for row in session["responses"]:
                dict_row = {}
                for i, header in enumerate(headers):
                    if i < len(row):
                        dict_row[header] = row[i]
                    else:
                        dict_row[header] = None
                dict_responses.append(dict_row)
            
            # Save participant data to data/responses directory
            filepath = save_participant_data(save_id, dict_responses, headers)
            print(f"✅ Successfully saved participant data to {filepath}")
            
            # Also save a backup copy with just the participant ID to ensure it's found
            backup_filepath = save_participant_data(f"participant_{participant_id}", dict_responses, headers)
            print(f"✅ Successfully saved backup participant data to {backup_filepath}")
            
        except Exception as e:
            print(f"❌ Error saving participant data: {e}")
        
        # IRB-Safe: Mark session as complete (non-intrusive addition)
        if SESSION_MANAGEMENT_ENABLED:
            try:
                mark_session_complete(session["pid"])
            except Exception as e:
                print(f"⚠️ Session completion marking failed (non-critical): {e}")
        
        pid = session["pid"]
        prolific_pid = session.get("prolific_pid", "")
        session.clear()
        return redirect(url_for("done", pid=pid, PROLIFIC_PID=prolific_pid))
    return render_template("survey.html")


@app.route("/")
def landing():
    # Force consent first
    if "consent" not in session:
        return redirect(url_for("consent"))

    pid = request.args.get("pid")
    prolific_pid = request.args.get("PROLIFIC_PID", "")
    
    if pid:
        # Start session immediately
        create_participant_run(pid, prolific_pid)
        return redirect(url_for("task", pid=pid))
    
    # Pass prolific_pid to template if available
    return render_template("index.html", prolific_pid=prolific_pid)

@app.route("/instructions")
def instructions():
    if "pid" not in session:
        return redirect(url_for("landing"))
    return render_template("instructions.html")


@app.route("/start", methods=["POST"])
def start_manual():
    pid = request.form.get("pid", "").strip()
    if not pid:
        abort(400)
    
    # Capture Prolific ID if provided
    prolific_pid = request.form.get("prolific_pid", "").strip()
    
    # IRB-Safe: Check for existing session before creating new one
    if SESSION_MANAGEMENT_ENABLED:
        try:
            existing_session = load_session_state(pid)
            if existing_session:
            if existing_session and not existing_session.get("session_complete", False):
                # Resume existing session
                session["pid"] = pid
                session["responses"] = existing_session.get("responses", [])
                session["face_order"] = existing_session.get("face_order", [])
                
                # Rebuild sequence from face_order with proper structure
                face_order = existing_session.get("face_order", [])
                left_first = existing_session.get("left_first", True)  # Default to True if not stored
                sequence = []
                for face_id in face_order:
                    # Create the exact same sequence structure as the original
                    sequence.append({
                        "face_id": face_id,
                        "order": [
                            {"version": "toggle", "file": f"{face_id}.jpg", "start": ("left" if left_first else "right")}, 
                            {"version": "full", "file": f"{face_id}.jpg"}
                        ]
                    })
                session["sequence"] = sequence
                
                # Determine the correct index to resume at
                existing_index = existing_session.get("index", 0)
                existing_responses = existing_session.get("responses", [])
                
                # Calculate which face we're on and if it's complete
                face_index = existing_index // 2  # Each face has 2 stages (toggle, full)
                stage_in_face = existing_index % 2  # 0 = toggle, 1 = full
                
                print(f"   📊 Existing index: {existing_index}, face_index: {face_index}, stage_in_face: {stage_in_face}")
                
                # Check if current face is complete (has both toggle and full responses)
                face_responses = [r for r in existing_responses if r[2] == face_order[face_index]]  # Filter by face_id
                has_toggle = any(r[3] == "toggle" for r in face_responses)
                has_full = any(r[3] == "full" for r in face_responses)
                
                print(f"   📊 Face {face_order[face_index]} responses: toggle={has_toggle}, full={has_full}")
                
                # If face is incomplete, resume at the missing stage
                if not has_toggle:
                    # Resume at toggle stage of current face
                    session["index"] = face_index * 2  # toggle stage
                    print(f"   📊 Resuming at toggle stage (index {session['index']})")
                elif not has_full:
                    # Resume at full stage of current face
                    session["index"] = face_index * 2 + 1  # full stage
                    print(f"   📊 Resuming at full stage (index {session['index']})")
                else:
                    # Face is complete, move to next face
                    session["index"] = (face_index + 1) * 2  # toggle stage of next face
                    print(f"   📊 Face complete, moving to next face (index {session['index']})")
                
                session["responses"] = existing_responses
                print(f"   📊 Final index: {session['index']}, total responses: {len(session['responses'])}")
                
                if existing_session.get("prolific_pid"):
                    session["prolific_pid"] = existing_session["prolific_pid"]
                
                print(f"✅ Resumed session for participant {pid}")
                print(f"   Resuming at index: {session['index']}")
                print(f"   📊 Total responses: {len(session['responses'])}")
                print(f"   🔄 Redirecting to task page...")
                return redirect(url_for("task", pid=pid))
        except Exception as e:
            print(f"⚠️ Session resume failed (non-critical): {e}")
            import traceback
            traceback.print_exc()
    
    # Create new session (existing behavior unchanged)
    create_participant_run(pid, prolific_pid)
    if len(session['sequence']) > 0:
        first_face = session['sequence'][0]
    return redirect(url_for("instructions"))

@app.route("/task", methods=["GET", "POST"])
def task():
    # If session missing but pid present in query (e.g., redirect loop), try to resume first
    if "pid" not in session:
        qpid = request.args.get("pid")
        if qpid:
            # Try to resume existing session first
            if SESSION_MANAGEMENT_ENABLED:
                try:
                    existing_session = load_session_state(qpid)
                    if existing_session and not existing_session.get("session_complete", False):
                        # Resume the session with proper index calculation
                        session["pid"] = existing_session["participant_id"]
                        session["face_order"] = existing_session["face_order"]
                        session["responses"] = existing_session["responses"]
                        
                        # Rebuild sequence
                        left_first = existing_session.get("left_first", True)  # Default to True if not stored
                        sequence = []
                        for face_id in existing_session["face_order"]:
                            sequence.append({
                                "face_id": face_id,
                                "order": [{"version": "toggle", "file": f"{face_id}.jpg", "start": ("left" if left_first else "right")}, {"version": "full", "file": f"{face_id}.jpg"}]
                            })
                        session["sequence"] = sequence
                        
                        # Determine the correct index to resume at (same logic as start_manual)
                        existing_index = existing_session.get("index", 0)
                        existing_responses = existing_session.get("responses", [])
                        face_order = existing_session.get("face_order", [])
                        
                        # Calculate which face we're on and if it's complete
                        face_index = existing_index // 2  # Each face has 2 stages (toggle, full)
                        stage_in_face = existing_index % 2  # 0 = toggle, 1 = full
                        
                        
                        # Check if current face is complete (has both toggle and full responses)
                        if face_index < len(face_order):
                            face_responses = [r for r in existing_responses if r[2] == face_order[face_index]]  # Filter by face_id
                            has_toggle = any(r[3] == "toggle" for r in face_responses)
                            has_full = any(r[3] == "full" for r in face_responses)
                            
                            
                            # If face is incomplete, resume at the missing stage
                            if not has_toggle:
                                # Resume at toggle stage of current face
                                session["index"] = face_index * 2  # toggle stage
                            elif not has_full:
                                # Resume at full stage of current face
                                session["index"] = face_index * 2 + 1  # full stage
                            else:
                                # Face is complete, move to next face
                                session["index"] = (face_index + 1) * 2  # toggle stage of next face
                        else:
                            # We're past all faces, keep the existing index
                            session["index"] = existing_index
                        
                        if existing_session.get("prolific_pid"):
                            session["prolific_pid"] = existing_session["prolific_pid"]
                            
                    else:
                        create_participant_run(qpid)
                except Exception as e:
                    create_participant_run(qpid)
            else:
                create_participant_run(qpid)
        else:
            return redirect(url_for("landing"))

    # Handle POST (save previous answer)
    if request.method == "POST":
        data = session["sequence"][session["index"] // 2]
        face_id = data["face_id"]
        version = request.form["version"]
        if version == "toggle":
            trust_left = request.form.get("trust_left")
            trust_right = request.form.get("trust_right")
            emotion_left = request.form.get("emotion_left")
            emotion_right = request.form.get("emotion_right")
            masc_toggle = request.form.get("masc_toggle")
            fem_toggle = request.form.get("fem_toggle")
            # record left then right (order flag indicates which shown first but both stored)
            prolific_pid = session.get("prolific_pid", "")
            
            row_l = [
                session["pid"], datetime.utcnow().isoformat(), face_id,
                "left", session["index"], trust_left, masc_toggle, fem_toggle,
                emotion_left, None, None, None, None, None, None, None
            ]
            row_l.append(prolific_pid)  # Add Prolific ID
            session["responses"].append(row_l)
            
            row_r = [
                session["pid"], datetime.utcnow().isoformat(), face_id,
                "right", session["index"], trust_right, masc_toggle, fem_toggle,
                emotion_right, None, None, None, None, None, None, None
            ]
            row_r.append(prolific_pid)  # Add Prolific ID
            session["responses"].append(row_r)
        else:
            trust_rating = request.form.get("trust")
            emotion_rating = request.form.get("emotion")
            masc_choice = request.form.get("masc")
            fem_choice = request.form.get("fem")
            prolific_pid = session.get("prolific_pid", "")
            
            row_o = [
                session["pid"], datetime.utcnow().isoformat(), face_id,
                version, session["index"], trust_rating, masc_choice, fem_choice,
                emotion_rating, None, None, None, None, None, None, None
            ]
            row_o.append(prolific_pid)  # Add Prolific ID
            session["responses"].append(row_o)
        # Save the current index before advancing
        current_index = session["index"]
        session["index"] += 1
        
        
        # IRB-Safe: Save session state after each response (non-intrusive addition)
        if SESSION_MANAGEMENT_ENABLED:
            try:
                save_result = save_session_state(session["pid"], dict(session))
                
                # Also save a backup copy directly to ensure it works
                try:
                    import json
                    backup_file = DATA_DIR / "sessions" / f"{session['pid']}_backup.json"
                    backup_data = {
                        "participant_id": session["pid"],
                        "timestamp": datetime.utcnow().isoformat(),
                        "index": session["index"],
                        "face_order": session["face_order"],
                        "responses": session["responses"],
                        "prolific_pid": session.get("prolific_pid", ""),
                        "session_complete": False
                    }
                    with open(backup_file, 'w') as f:
                        json.dump(backup_data, f, indent=2)
                    print(f"✅ Backup session saved to {backup_file}")
                except Exception as backup_e:
                    print(f"⚠️ Backup save failed: {backup_e}")
                    
            except Exception as e:
                print(f"⚠️ Session save failed (non-critical): {e}")
                import traceback
                traceback.print_exc()
        
        # Save responses to CSV immediately for dashboard visibility
        try:
            # Convert session responses to dictionary format for save_participant_data
            participant_id = session["pid"]
            prolific_pid = session.get("prolific_pid", participant_id)
            
            # Use the Prolific ID if available, otherwise use the participant ID
            save_id = prolific_pid if prolific_pid else participant_id
            
            # Convert list-based responses to dictionary format
            dict_responses = []
            headers = [
                "pid", "timestamp", "face_id", "version", "order_presented",
                "trust_rating", "masc_choice", "fem_choice",
                "emotion_rating", "trust_q2", "trust_q3",
                "pers_q1", "pers_q2", "pers_q3", "pers_q4", "pers_q5",
                "prolific_pid"
            ]
            
            for row in session["responses"]:
                dict_row = {}
                for i, header in enumerate(headers):
                    if i < len(row):
                        dict_row[header] = row[i]
                    else:
                        dict_row[header] = None
                dict_responses.append(dict_row)
            
            # Save participant data to data/responses directory
            filepath = save_participant_data(save_id, dict_responses, headers)
            if filepath:
                print(f"✅ Saved live response data to {filepath}")
            else:
                print(f"❌ save_participant_data returned None - saving failed")
            
            # Also save a backup copy with just the participant ID to ensure it's found
            backup_filepath = save_participant_data(f"participant_{participant_id}", dict_responses, headers)
            if backup_filepath:
                print(f"✅ Saved backup response data to {backup_filepath}")
            
            # Create a simple CSV file for dashboard compatibility (in long format)
            responses_dir = DATA_DIR / "responses"
            responses_dir.mkdir(exist_ok=True)
            simple_csv_path = responses_dir / f"{participant_id}.csv"
            try:
                # Convert to long format for dashboard compatibility
                long_responses = convert_wide_to_long_format(dict_responses)
                long_format_headers = ["participant_id", "image_id", "face_view", "question_type", "response", "timestamp"]
                
                with open(simple_csv_path, "w", newline="") as f:
                    writer = csv.DictWriter(f, fieldnames=long_format_headers)
                    writer.writeheader()
                    writer.writerows(long_responses)
                print(f"✅ Saved simple CSV in LONG FORMAT for dashboard: {simple_csv_path}")
                print(f"   📊 Converted {len(dict_responses)} wide format rows to {len(long_responses)} long format rows")
            except Exception as e:
                print(f"⚠️ Simple CSV save failed: {e}")
                
        except Exception as e:
            print(f"⚠️ Live response saving failed (non-critical): {e}")

    # Check if finished
    if session["index"] >= len(session["sequence"]) * 2:  # 2 stages per face (toggle and full)
        return redirect(url_for("survey"))

    # Determine current image to show
    face_index = session["index"] // 2
    image_index = session["index"] % 2
    current = session["sequence"][face_index]
    image_dict = current["order"][image_index]
    image_file = image_dict["file"]
    version = image_dict["version"]
    
    if version == "toggle":
        side = image_dict.get("start", "left")
    else:
        side = version

    # Determine which blocks to show in template
    show_mf_questions = version == "compare"
    show_trust_questions = version in ("toggle", "full")

    progress = face_index + 1
    return render_template(
        "task.html",
        pid=session["pid"],
        image_url=url_for("static", filename=f"images/{image_file}"),
        face_id=current["face_id"],
        version=version,
        progress=progress,
        total=len(FACE_FILES),
        show_mf=show_mf_questions,
        show_trust=show_trust_questions,
        side=side,
    )

@app.route("/done")
def done():
    pid = request.args.get("pid")
    prolific_pid = request.args.get("PROLIFIC_PID", "")
    
    # Prepare completion URL for Prolific if needed
    completion_url = ""
    if prolific_pid:
        # You would replace this with your actual Prolific completion URL
        completion_url = "https://app.prolific.co/submissions/complete?cc=COMPLETION_CODE"
    
    return render_template("done.html", pid=pid, prolific_pid=prolific_pid, completion_url=completion_url)

# ----------------------------------------------------------------------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    print(f"🎯 Starting Facial Trust Study on port {port}")
    print(f"📍 URL: http://localhost:{port}")
    print("🔧 Using localhost binding for Windows compatibility")
    try:
        # Use 0.0.0.0 for Render deployment, localhost for local development
        host = "0.0.0.0" if os.environ.get("RENDER") else "127.0.0.1"
        app.run(host=host, port=port, debug=False)
    except OSError as e:
        if "Address already in use" in str(e):
            print(f"❌ Port {port} is already in use. Please stop other services on this port.")
        else:
            print(f"❌ Error starting server: {e}")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
