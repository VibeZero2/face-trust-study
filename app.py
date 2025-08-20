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


def save_participant_data(participant_id: str, responses: list, headers=None):
    """Save responses to a CSV file in data/responses/
    
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
            
        # Write the CSV file
        with open(filepath, "w", newline="") as f:
            # Use provided headers or get keys from first response
            field_names = headers if headers else responses[0].keys()
            writer = csv.DictWriter(f, fieldnames=field_names)
            writer.writeheader()
            writer.writerows(responses)
        
        print(f"✅ Saved participant data to {filepath}")
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
            if existing_session and not existing_session.get("session_complete", False):
                # Resume existing session
                session["pid"] = pid
                session["responses"] = existing_session.get("responses", [])
                session["face_order"] = existing_session.get("face_order", [])
                
                # Rebuild sequence from face_order with proper structure
                face_order = existing_session.get("face_order", [])
                sequence = []
                for face_id in face_order:
                    # Create a simplified sequence structure for resumed sessions
                    # This maintains compatibility with the task processing logic
                    sequence.append({
                        "face_id": face_id,
                        "order": [
                            {"version": "toggle", "file": f"{face_id}.jpg", "start": "left"}, 
                            {"version": "full", "file": f"{face_id}.jpg"}
                        ]
                    })
                session["sequence"] = sequence
                
                # CRITICAL: Calculate correct index based on completed faces
                # Analyze responses to determine which faces are fully completed
                responses = existing_session.get("responses", [])
                completed_faces_in_order = []
                partial_face_responses = []
                
                # Check each face in the original order to maintain sequence
                for face_id in face_order:
                    # Get all responses for this specific face
                    face_responses = [r for r in responses if len(r) >= 4 and r[2] == face_id]
                    toggle_responses = [r for r in face_responses if r[3] in ['left', 'right']]
                    full_responses = [r for r in face_responses if r[3] == 'full']
                    
                    # Face is complete ONLY if it has both left+right (toggle) AND full responses
                    is_complete = len(toggle_responses) >= 2 and len(full_responses) >= 1
                    
                    if is_complete:
                        completed_faces_in_order.append(face_id)
                        print(f"   ✅ Face {face_id}: Complete (toggle: {len(toggle_responses)}, full: {len(full_responses)})")
                    else:
                        # This face is incomplete - we'll restart from here
                        if face_responses:
                            partial_face_responses.extend(face_responses)
                            print(f"   🔄 Face {face_id}: Incomplete (toggle: {len(toggle_responses)}, full: {len(full_responses)}) - will restart")
                        break  # Stop at first incomplete face
                
                # Clean up: Remove partial responses for the incomplete face
                # Keep only responses from fully completed faces
                cleaned_responses = []
                for response in responses:
                    if len(response) >= 4:
                        face_id = response[2]
                        if face_id in completed_faces_in_order:
                            cleaned_responses.append(response)
                
                session["responses"] = cleaned_responses
                
                # Set index to start at the first incomplete face
                completed_count = len(completed_faces_in_order)
                
                # Check if we have any responses for the current face
                current_face_id = face_order[completed_count] if completed_count < len(face_order) else None
                if current_face_id:
                    current_face_responses = [r for r in responses if len(r) >= 4 and r[2] == current_face_id]
                    if current_face_responses:
                        # We have responses for this face, so we're in the middle of it
                        # Calculate which stage we're on for this face
                        toggle_responses = [r for r in current_face_responses if r[3] in ['left', 'right']]
                        full_responses = [r for r in current_face_responses if r[3] == 'full']
                        
                        print(f"   🔍 Current face {current_face_id} has {len(toggle_responses)} toggle, {len(full_responses)} full responses")
                        
                        if len(toggle_responses) < 2:
                            # Still on toggle stage - stay exactly where we are
                            session["index"] = completed_count * 2  # Start of toggle stage for this face
                            print(f"   🔄 Staying on toggle stage for face {current_face_id} (index: {session['index']})")
                        elif len(full_responses) < 1:
                            # Toggle complete, on full stage - stay exactly where we are
                            session["index"] = completed_count * 2 + 1  # Start of full stage for this face
                            print(f"   🔄 Staying on full stage for face {current_face_id} (index: {session['index']})")
                        else:
                            # This face is actually complete, move to next
                            session["index"] = (completed_count + 1) * 2
                            print(f"   ➡️ Face {current_face_id} is complete, moving to next face (index: {session['index']})")
                    else:
                        # No responses for current face, start at beginning
                        session["index"] = completed_count * 2
                        print(f"   ➡️ Starting fresh on face {current_face_id} (index: {session['index']})")
                else:
                    # All faces complete
                    session["index"] = len(face_order) * 2
                    print(f"   ✅ All faces complete (index: {session['index']})")
                
                if existing_session.get("prolific_pid"):
                    session["prolific_pid"] = existing_session["prolific_pid"]
                
                print(f"✅ Resumed session for participant {pid}")
                print(f"   Completed faces: {completed_count}/{len(face_order)}")
                print(f"   Resuming at index: {session['index']}")
                if partial_face_responses:
                    print(f"   🧹 Cleaned {len(partial_face_responses)} partial responses from incomplete face")
                print(f"   📊 Total valid responses: {len(cleaned_responses)}")
                return redirect(url_for("task", pid=pid))
        except Exception as e:
            print(f"⚠️ Session resume failed (non-critical): {e}")
    
    # Create new session (existing behavior unchanged)
    create_participant_run(pid, prolific_pid)
    return redirect(url_for("instructions"))

@app.route("/task", methods=["GET", "POST"])
def task():
    # If session missing but pid present in query (e.g., redirect loop), rebuild session
    if "pid" not in session:
        qpid = request.args.get("pid")
        if qpid:
            create_participant_run(qpid)
        else:
            return redirect(url_for("landing"))

    # Handle POST (save previous answer)
    if request.method == "POST":
        data = session["sequence"][session["index"] // 2]
        face_id = data["face_id"]
        version = request.form["version"]
        print(f"DEBUG: Saving response - index: {session['index']}, face_id: {face_id}, version: {version}")
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
        
        print(f"DEBUG: Advanced from index {current_index} to {session['index']}")
        
        # IRB-Safe: Save session state after each response (non-intrusive addition)
        if SESSION_MANAGEMENT_ENABLED:
            try:
                save_session_state(session["pid"], dict(session))
                print(f"DEBUG: Session saved - total responses: {len(session['responses'])}, index: {session['index']}")
            except Exception as e:
                print(f"⚠️ Session save failed (non-critical): {e}")
        
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
            
            # Also save a backup copy with just the participant ID to ensure it's found
            backup_filepath = save_participant_data(f"participant_{participant_id}", dict_responses, headers)
            if backup_filepath:
                print(f"✅ Saved backup response data to {backup_filepath}")
            
            # Create a simple CSV file for dashboard compatibility
            simple_csv_path = responses_dir / f"{participant_id}.csv"
            try:
                with open(simple_csv_path, "w", newline="") as f:
                    field_names = headers
                    writer = csv.DictWriter(f, fieldnames=field_names)
                    writer.writeheader()
                    writer.writerows(dict_responses)
                print(f"✅ Saved simple CSV for dashboard: {simple_csv_path}")
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
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
